"""Static scoring of tool definitions with Glama's Tool Definition Quality Score (TDQS).

Why this exists (ADR 0015 / 0016): static graders score a tool's description by reading it. AgentGrade
measures what agents actually do with it. To compare the two honestly, we re-implement TDQS from its
published specification and score the exact descriptions we have already measured.

Pipeline (TDQS spec, pinned commit):
  1. context signals   - deterministic facts about the input schema
  2. hard gates        - no description => 1.0 without an LLM call; tautology => purpose capped at 2
  3. LLM rubric        - one call, six dimensions scored 1-5, JSON only, validated, retried
  4. post-processing   - caps, flags, smells; weighted score with integer rounding; tier

The prompts are NOT copied into this repo: the TDQS repository has no license file. They are downloaded
from a pinned commit, extracted from the spec's Appendix A, and cached.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
import statistics
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError, model_validator

from agentgrade.evaluate import FATAL_ERRORS, run_setup
from agentgrade.mcp_client import McpServerConfig, McpToolInfo, connect
from agentgrade.models.base import ModelAdapter
from agentgrade.report import wilson_interval
from agentgrade.suite import ROOT_PLACEHOLDER, ServerConfig, Suite, Variant
from agentgrade.trace import new_run_id
from agentgrade.types import Message

TDQS_REPO = "glama-ai/tool-definition-quality-score"
TDQS_COMMIT = "b9881b0cfec88969e42672c92544487ca191a992"  # 2026-09-03

# Dimension -> weight in percent (TDQS "Computing the score").
WEIGHTS: dict[str, int] = {
    "purpose_clarity": 25,
    "usage_guidelines": 20,
    "behavioral_transparency": 20,
    "parameter_semantics": 15,
    "conciseness_structure": 10,
    "contextual_completeness": 10,
}
SHORT = {  # column headers in reports
    "purpose_clarity": "Purp",
    "usage_guidelines": "Use",
    "behavioral_transparency": "Behav",
    "parameter_semantics": "Param",
    "conciseness_structure": "Conc",
    "contextual_completeness": "Compl",
}

# Every placeholder the user-message template is expected to contain. If a different TDQS commit
# changes the template, rendering fails loudly instead of sending a half-filled prompt.
TEMPLATE_PLACEHOLDERS = {
    "{name}",
    '{title | "null"}',
    "{description}",
    '{inputSchema JSON | "{}"}',
    '{outputSchema JSON | "None provided"}',
    '{annotations JSON | "None provided"}',
    "{paramCount}",
    "{requiredParamCount}",
    "{schemaDescriptionCoverage}",
    "{paramsWithEnums}",
    "{hasNestedObjects}",
    '{sibling tool names, one per line | "None"}',
}
# "{name}", or with a fallback that may itself contain "{}": {inputSchema JSON | "{}"}
_PLACEHOLDER = re.compile(r"\{[A-Za-z](?:[^{}\n]|\{\})*\}")


class TdqsSpecError(RuntimeError):
    """The TDQS specification could not be fetched or no longer has the expected shape."""


# ---------------------------------------------------------------------------------------------
# The prompt, from the published spec


@dataclass(frozen=True)
class TdqsPrompt:
    system: str
    user_template: str
    commit: str
    sha256: str  # of the spec file the prompt was taken from

    def __post_init__(self) -> None:
        found = set(_PLACEHOLDER.findall(self.user_template))
        if found != TEMPLATE_PLACEHOLDERS:
            raise TdqsSpecError(
                "TDQS user-message template changed: unexpected "
                f"{sorted(found - TEMPLATE_PLACEHOLDERS)}, missing "
                f"{sorted(TEMPLATE_PLACEHOLDERS - found)}"
            )


def parse_spec(readme: str, commit: str) -> TdqsPrompt:
    """Extract Appendix A's system prompt and user-message template (the two ```text blocks)."""
    lines = readme.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("## Appendix A"))
    except StopIteration:
        raise TdqsSpecError("TDQS spec has no 'Appendix A' section") from None
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## Appendix")),
        len(lines),
    )
    blocks: list[str] = []
    i = start
    while i < end and len(blocks) < 2:
        if lines[i].strip() == "```text":
            j = i + 1
            while j < end and lines[j].strip() != "```":
                j += 1
            blocks.append("\n".join(lines[i + 1 : j]))
            i = j
        i += 1
    if len(blocks) != 2:
        raise TdqsSpecError(f"Expected 2 text blocks in Appendix A, found {len(blocks)}")
    return TdqsPrompt(
        system=blocks[0],
        user_template=blocks[1],
        commit=commit,
        sha256=hashlib.sha256(readme.encode()).hexdigest(),
    )


async def load_tdqs_prompt(cache_dir: Path, commit: str = TDQS_COMMIT) -> TdqsPrompt:
    """The prompt at a pinned commit: from the local cache, or downloaded once."""
    cache = cache_dir / f"tdqs-{commit[:12]}.md"
    if not cache.is_file():
        url = f"https://raw.githubusercontent.com/{TDQS_REPO}/{commit}/README.md"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TdqsSpecError(f"Could not download the TDQS spec from {url}: {exc}") from exc
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(response.text, encoding="utf-8")
    return parse_spec(cache.read_text(encoding="utf-8"), commit)


# ---------------------------------------------------------------------------------------------
# Stage 1: context signals; rendering the user message


def _round_half_up(numerator: int, denominator: int) -> int:
    """Integer round-half-up (JavaScript Math.round for non-negative values). Python's round()
    rounds half to even, which would give different numbers from the reference implementation."""
    return (2 * numerator + denominator) // (2 * denominator)


def context_signals(input_schema: dict[str, Any] | None) -> dict[str, Any]:
    properties = (input_schema or {}).get("properties") or {}
    required = (input_schema or {}).get("required") or []
    count = len(properties)
    described = sum(
        1
        for p in properties.values()
        if isinstance(p, dict) and str(p.get("description", "")).strip()
    )

    def is_object(prop: Any) -> bool:
        kind = prop.get("type") if isinstance(prop, dict) else None
        return kind == "object" or (isinstance(kind, list) and "object" in kind)

    return {
        "paramCount": count,
        "requiredParamCount": len(required),
        "schemaDescriptionCoverage": _round_half_up(described * 100, count) if count else 100,
        "paramsWithEnums": sum(
            1 for p in properties.values() if isinstance(p, dict) and "enum" in p
        ),
        "hasNestedObjects": any(is_object(p) for p in properties.values()),
    }


def _json_or(value: Any, fallback: str) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) if value else fallback


def render_user_message(prompt: TdqsPrompt, tool: McpToolInfo, siblings: list[str]) -> str:
    signals = context_signals(tool.input_schema)
    values = {
        "{name}": tool.name,
        '{title | "null"}': tool.title or "null",
        "{description}": tool.description,
        '{inputSchema JSON | "{}"}': _json_or(tool.input_schema, "{}"),
        '{outputSchema JSON | "None provided"}': _json_or(tool.output_schema, "None provided"),
        '{annotations JSON | "None provided"}': _json_or(tool.annotations, "None provided"),
        "{paramCount}": str(signals["paramCount"]),
        "{requiredParamCount}": str(signals["requiredParamCount"]),
        "{schemaDescriptionCoverage}": str(signals["schemaDescriptionCoverage"]),
        "{paramsWithEnums}": str(signals["paramsWithEnums"]),
        "{hasNestedObjects}": str(signals["hasNestedObjects"]).lower(),
        '{sibling tool names, one per line | "None"}': "\n".join(siblings) or "None",
    }
    # One pass over the template: substituted text (JSON braces, descriptions) is never re-scanned.
    return _PLACEHOLDER.sub(lambda m: values.get(m.group(0), m.group(0)), prompt.user_template)


# ---------------------------------------------------------------------------------------------
# Stage 3 output contract; stage 4 scoring


class DimensionScore(BaseModel):
    score: int = Field(ge=1, le=5)
    justification: str


class JudgeOutput(BaseModel):
    scores: dict[str, DimensionScore]
    annotation_contradiction: bool
    summary: str

    @model_validator(mode="after")
    def _all_six(self) -> JudgeOutput:
        if set(self.scores) != set(WEIGHTS):
            raise ValueError(f"expected dimensions {sorted(WEIGHTS)}, got {sorted(self.scores)}")
        return self


def parse_judge_output(text: str) -> JudgeOutput:
    """JSON only is requested; tolerate a ```json fence or text around the object."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in judge output: {text[:200]!r}")
    return JudgeOutput.model_validate(json.loads(text[start : end + 1]))


def round1(numerator: int, denominator: int) -> float:
    """TDQS rounding: numerator/denominator rounded half-up to one decimal, in integer arithmetic."""
    return ((20 * numerator + denominator) // (2 * denominator)) / 10


def compute_tdqs(scores: dict[str, int]) -> float:
    return round1(sum(scores[d] * w for d, w in WEIGHTS.items()), 100)


def tier(score: float) -> str:
    if score >= 3.5:
        return "A"
    if score >= 3.0:
        return "B"
    if score >= 2.0:
        return "C"
    if score >= 1.0:
        return "D"
    return "F"


def is_tautological(tool: McpToolInfo) -> bool:
    text = tool.description.strip().lower()
    return text in {tool.name.lower(), (tool.title or "").strip().lower()} - {""}


class StaticScore(BaseModel):
    """One TDQS scoring of one tool definition (one repeat)."""

    variant: str
    tool: str
    repeat: int
    definition_hash: str
    description: str
    judge: str
    tdqs_commit: str
    scores: dict[str, int] = Field(default_factory=dict)
    justifications: dict[str, str] = Field(default_factory=dict)
    tdqs: float | None = None
    tier: str | None = None
    flags: list[str] = Field(default_factory=list)
    smells: list[str] = Field(default_factory=list)
    summary: str = ""
    attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None


def finalize(base: dict[str, Any], tool: McpToolInfo, output: JudgeOutput) -> StaticScore:
    """Stage 4: deterministic post-processing of a validated judge output."""
    scores = {d: output.scores[d].score for d in WEIGHTS}
    flags: list[str] = []
    if is_tautological(tool):
        scores["purpose_clarity"] = min(scores["purpose_clarity"], 2)
        flags.append("Tautological Description")
    if output.annotation_contradiction:
        flags.append("Annotation Contradiction")
    value = compute_tdqs(scores)
    return StaticScore(
        **base,
        scores=scores,
        justifications={d: output.scores[d].justification for d in WEIGHTS},
        tdqs=value,
        tier=tier(value),
        flags=flags,
        smells=[d for d in WEIGHTS if scores[d] < 3],
        summary=output.summary,
    )


def definition_hash(tool: McpToolInfo, siblings: list[str]) -> str:
    payload = json.dumps(
        [
            tool.name,
            tool.title,
            tool.description,
            tool.input_schema,
            tool.output_schema,
            tool.annotations,
            siblings,
        ],
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


async def score_tool(
    judge: ModelAdapter,
    prompt: TdqsPrompt,
    tool: McpToolInfo,
    siblings: list[str],
    *,
    variant: str,
    repeat: int,
    max_attempts: int = 3,
) -> StaticScore:
    base = {
        "variant": variant,
        "tool": tool.name,
        "repeat": repeat,
        "definition_hash": definition_hash(tool, siblings),
        "description": tool.description,
        "judge": judge.name,
        "tdqs_commit": prompt.commit,
    }
    if not tool.description.strip():  # stage 2 hard gate: nothing to evaluate
        ones = dict.fromkeys(WEIGHTS, 1)
        return StaticScore(
            **base, scores=ones, tdqs=1.0, tier="D", flags=["No Description"], smells=list(WEIGHTS)
        )

    messages = [
        Message(role="system", content=prompt.system),
        Message(role="user", content=render_user_message(prompt, tool, siblings)),
    ]
    tokens_in = tokens_out = 0
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            response = await judge.complete(messages, [])
        except FATAL_ERRORS:
            raise
        except Exception as exc:  # noqa: BLE001 - one failed call must not stop the experiment
            last_error = f"{type(exc).__name__}: {exc}"
            continue
        tokens_in += response.usage.input_tokens
        tokens_out += response.usage.output_tokens
        try:
            output = parse_judge_output(response.content)
        except (ValueError, ValidationError) as exc:  # schema mismatch => retry (TDQS rule)
            last_error = f"invalid judge output: {exc}"[:500]
            continue
        scored = finalize(base, tool, output)
        return scored.model_copy(
            update={"attempts": attempt, "input_tokens": tokens_in, "output_tokens": tokens_out}
        )
    return StaticScore(
        **base,
        attempts=max_attempts,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        error=last_error,
    )


# ---------------------------------------------------------------------------------------------
# Running it over a suite's variants


async def snapshot_tools(
    suite: Suite, log: Path, launch: ServerConfig | None = None
) -> tuple[list[McpToolInfo], dict[str, Any]]:
    """Start a server once (fixture + setup, like a real run) and record tools/list.

    `launch` is the command to run (a variant's server build); default: the suite's server.
    """
    launch = launch or suite.server
    with tempfile.TemporaryDirectory(prefix="agentgrade-static-") as tmp:
        root = Path(tmp).resolve() / "sandbox"
        if suite.server.fixture is not None:
            shutil.copytree(suite.server.fixture, root)
        else:
            root.mkdir()
        await run_setup(suite.server.setup, root, log)
        server = McpServerConfig(
            name=suite.name,
            command=launch.command,
            args=[a.replace(ROOT_PLACEHOLDER, str(root)) for a in launch.args],
            timeout_s=suite.server.timeout_s,
            stderr_log=log,
        )
        async with connect(server) as conn:
            return list(conn.tools), conn.describe()


def variant_definitions(
    server_tools: list[McpToolInfo], suite: Suite, variant: Variant, only_tools: list[str] | None
) -> list[tuple[McpToolInfo, list[str]]]:
    """(tool definition as this variant's agent saw it, sibling names) for each tool to score.

    Overrides replace only the description; schema and annotations stay the server's. Siblings are
    every tool the server offers (what TDQS sees for a real server). Tools a variant removed are skipped.
    """
    by_name = {t.name: t for t in server_tools}
    names = only_tools or suite.tools_for(variant)
    unknown = sorted(set(names) - set(by_name))
    if unknown:
        raise ValueError(f"Tools not offered by the server: {unknown}. Offered: {sorted(by_name)}")
    visible = set(suite.tools_for(variant))
    overrides = variant.description_overrides or {}
    out = []
    for name in names:
        if name not in visible:
            continue
        tool = by_name[name]
        if name in overrides:
            tool = dataclasses.replace(tool, description=overrides[name].strip())
        siblings = [t.name for t in server_tools if t.name != name]
        out.append((tool, siblings))
    return out


ProgressFn = Callable[[StaticScore, bool], None]  # (score, reused from an identical definition)


async def score_suite(
    suite: Suite,
    judge: ModelAdapter,
    prompt: TdqsPrompt,
    out_dir: Path,
    *,
    variants: list[Variant],
    only_tools: list[str] | None,
    repeats: int,
    on_score: ProgressFn | None = None,
) -> tuple[list[StaticScore], dict[str, Any]]:
    # One tools/list snapshot per distinct server build (variants may run a proposed patch).
    snapshots: dict[tuple[str, tuple[str, ...]], tuple[list[McpToolInfo], dict[str, Any]]] = {}
    server_info: dict[str, Any] = {}
    cache: dict[str, list[StaticScore]] = {}  # identical definitions are scored once
    scores: list[StaticScore] = []
    with (out_dir / "static_scores.jsonl").open("w", encoding="utf-8") as sink:
        for variant in variants:
            launch = suite.server_for(variant)
            build = (launch.command, tuple(launch.args))
            if build not in snapshots:
                suffix = "" if not snapshots else f".{variant.name}"
                snapshots[build] = await snapshot_tools(
                    suite, out_dir / f"server{suffix}.log", launch
                )
                (out_dir / f"tool_definitions{suffix}.json").write_text(
                    json.dumps(
                        [dataclasses.asdict(t) for t in snapshots[build][0]],
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
            server_tools, info = snapshots[build]
            server_info = server_info or info
            for tool, siblings in variant_definitions(server_tools, suite, variant, only_tools):
                key = definition_hash(tool, siblings)
                reused = key in cache
                if not reused:
                    cache[key] = []
                    for repeat in range(1, repeats + 1):
                        cache[key].append(
                            await score_tool(
                                judge, prompt, tool, siblings, variant=variant.name, repeat=repeat
                            )
                        )
                for s in cache[key]:
                    s = s.model_copy(update={"variant": variant.name})
                    scores.append(s)
                    sink.write(s.model_dump_json() + "\n")
                    sink.flush()
                    if on_score:
                        on_score(s, reused)
    return scores, server_info


# ---------------------------------------------------------------------------------------------
# Measured side: pass rates from existing suite runs


class Measured(BaseModel):
    passed: int
    total: int
    models: list[str]
    run_dirs: list[str]

    @property
    def rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


def load_measured(run_dirs: list[Path], suite_name: str) -> dict[str, Measured]:
    """Pool pass counts per variant across run folders of the SAME suite and the SAME model."""
    pooled: dict[str, Measured] = {}
    models: set[str] = set()
    for run_dir in run_dirs:
        path = run_dir / "results.json"
        if not path.is_file():
            raise FileNotFoundError(f"No results.json in {run_dir}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["suite"] != suite_name:
            raise ValueError(f"{run_dir} is suite {data['suite']!r}, not {suite_name!r}")
        model = str(data.get("model", {}).get("name"))
        models.add(model)
        for run in data["runs"]:
            m = pooled.setdefault(
                run["variant"], Measured(passed=0, total=0, models=[], run_dirs=[])
            )
            m.passed += bool(run["passed"])
            m.total += 1
            if model not in m.models:
                m.models.append(model)
            if run_dir.name not in m.run_dirs:
                m.run_dirs.append(run_dir.name)
    if len(models) > 1:
        raise ValueError(
            f"Run folders use different models {sorted(models)}: pass rates can't be pooled."
        )
    return pooled


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """Spearman rank correlation (average ranks for ties). None if either side is constant."""

    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            for k in range(i, j + 1):
                out[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx * vy) ** 0.5


# ---------------------------------------------------------------------------------------------
# Report


class VariantRow(BaseModel):
    variant: str
    tools: list[str]
    tdqs_values: list[float]  # one per scored repeat (all scored tools)
    errors: int
    dims: dict[str, float]  # median per dimension
    measured: Measured | None = None

    @property
    def tdqs_mean(self) -> float | None:
        return statistics.fmean(self.tdqs_values) if self.tdqs_values else None


def summarize(
    scores: list[StaticScore], variant_order: list[str], measured: dict[str, Measured]
) -> list[VariantRow]:
    rows = []
    for name in variant_order:
        mine = [s for s in scores if s.variant == name]
        if not mine:
            continue
        ok = [s for s in mine if s.tdqs is not None]
        rows.append(
            VariantRow(
                variant=name,
                tools=sorted({s.tool for s in mine}),
                tdqs_values=[s.tdqs for s in ok],
                errors=len(mine) - len(ok),
                dims={d: statistics.median(s.scores[d] for s in ok) for d in WEIGHTS} if ok else {},
                measured=measured.get(name),
            )
        )
    return rows


def _fmt_rate(m: Measured | None) -> str:
    if m is None or not m.total:
        return "-"
    lo, hi = wilson_interval(m.passed, m.total)
    return f"{m.passed}/{m.total} ({m.rate:.0%}, CI {lo:.0%}-{hi:.0%})"


def render_static_report(
    rows: list[VariantRow],
    *,
    suite: Suite,
    server_info: dict[str, Any],
    judge: str,
    prompt: TdqsPrompt,
    repeats: int,
    reference: str | None,
    scores: list[StaticScore],
) -> str:
    out = [
        f"# Static vs measured - {suite.name}",
        "",
        "| | |",
        "|---|---|",
        f"| Server | {server_info.get('server_name')} {server_info.get('server_version')} |",
        f"| Static score | Glama TDQS, spec commit `{prompt.commit[:7]}` (sha256 `{prompt.sha256[:12]}`) |",
        f"| Judge | `{judge}`, {repeats} scoring(s) per definition |",
        f"| Generated | {datetime.now(UTC):%Y-%m-%d %H:%M} UTC |",
        "",
        "TDQS reads only the tool definition (1.0-5.0; tier A >= 3.5, B >= 3.0 = passing, C >= 2.0, D). "
        "Measured = pass rate of real agent runs with that definition.",
        "",
        "| Variant | Tools | TDQS mean (min-max) | Tier | "
        + " | ".join(SHORT[d] for d in WEIGHTS)
        + " | Measured pass rate |",
        "|---|---|---|---|" + "---|" * len(WEIGHTS) + "---|",
    ]
    for r in rows:
        if r.tdqs_values:
            spread = f"{r.tdqs_mean:.2f} ({min(r.tdqs_values):.1f}-{max(r.tdqs_values):.1f})"
            t = tier(round(r.tdqs_mean, 1))
        else:
            spread, t = "error", "-"
        if r.errors:
            spread += f", {r.errors} failed"
        dims = " | ".join(f"{r.dims[d]:g}" if r.dims else "-" for d in WEIGHTS)
        out.append(
            f"| {r.variant} | {', '.join(r.tools)} | {spread} | {t} | {dims} | {_fmt_rate(r.measured)} |"
        )

    ref = next((r for r in rows if r.variant == reference), None)
    if ref and ref.tdqs_mean is not None and ref.measured:
        out += [
            "",
            f"## Change vs `{reference}`",
            "",
            "| Variant | Δ TDQS | Δ measured pass rate |",
            "|---|---|---|",
        ]
        for r in rows:
            if r is ref or r.tdqs_mean is None or r.measured is None:
                continue
            out.append(
                f"| {r.variant} | {r.tdqs_mean - ref.tdqs_mean:+.2f} | "
                f"{(r.measured.rate - ref.measured.rate) * 100:+.0f} points |"
            )

    paired = [r for r in rows if r.tdqs_mean is not None and r.measured and r.measured.total]
    if len(paired) >= 4:
        rho = spearman([r.tdqs_mean for r in paired], [r.measured.rate for r in paired])
        out += [
            "",
            f"**Spearman rank correlation (TDQS vs measured), n = {len(paired)}:** "
            + (f"{rho:+.2f}" if rho is not None else "undefined (one side is constant)")
            + ". With this few points it is a rough indication, not a test.",
        ]

    out += ["", "## What the judge said (first scoring of each distinct definition)", ""]
    seen: set[str] = set()
    for s in scores:
        if s.definition_hash in seen or s.tdqs is None:
            continue
        seen.add(s.definition_hash)
        same = sorted({x.variant for x in scores if x.definition_hash == s.definition_hash})
        out += [
            f"### {s.tool} - {', '.join(same)} (TDQS {s.tdqs}, tier {s.tier})",
            "",
            f"> {s.description}",
            "",
            f"*Summary:* {s.summary}",
            "",
        ]
        out += [f"- **{SHORT[d]} {s.scores[d]}** - {s.justifications[d]}" for d in WEIGHTS]
        out.append("")
    errors = [s for s in scores if s.error]
    if errors:
        out += ["## Failed scorings", ""]
        out += [f"- {s.variant} / {s.tool} r{s.repeat}: {s.error}" for s in errors]
        out.append("")
    out += [
        "## Caveats",
        "",
        "- Small n: a handful of definitions and one agent model. This can show that TDQS did not track "
        "measured behavior here, not that it never does.",
        "- Glama's production judge model is not published; absolute scores may differ from glama.ai. "
        "Compare variants with each other.",
        "",
    ]
    return "\n".join(out)


def new_static_run_dir(runs_dir: Path) -> Path:
    out = runs_dir / f"{new_run_id()}-static"
    out.mkdir(parents=True)
    return out
