"""Run traces: one JSON object per line (JSONL), written *while* the run happens.

Why JSONL: each event is flushed as soon as it occurs, so a run that crashes halfway
still leaves a readable partial trace; files can be grepped or streamed line by line.

Every event: {"seq": n, "ts": "<UTC ISO time>", "type": "<event type>", ...data}
Event types: run_started, model_call, tool_result, run_finished, run_failed, check.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any

from pydantic import BaseModel

REDACTED = "[REDACTED]"

# A key is secret if one of its *words* is a secret word, or two adjacent words form one.
# Whole words, not substrings: "access_token" is secret, "input_tokens" is not
# (bug found in M3 - substring matching redacted our token counts).
SECRET_WORDS = frozenset(
    {"token", "secret", "password", "passwd", "pwd", "authorization", "auth", "cookie",
     "credential", "credentials", "apikey", "bearer"}
)  # fmt: skip
SECRET_WORD_PAIRS = frozenset({("api", "key"), ("private", "key"), ("access", "key")})
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def key_words(key: str) -> list[str]:
    """'X-Api-Key' -> ['x','api','key'];  'accessToken' -> ['access','token']"""
    spaced = _CAMEL_BOUNDARY.sub("_", key)
    return [w for w in re.split(r"[^a-zA-Z0-9]+", spaced.lower()) if w]


def is_secret_key(key: str) -> bool:
    words = key_words(key)
    return any(w in SECRET_WORDS for w in words) or any(
        pair in SECRET_WORD_PAIRS for pair in zip(words, words[1:], strict=False)
    )


def redact(value: Any) -> Any:
    """Return a copy of `value` with secret-looking dict keys masked, at any depth."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        return {
            k: REDACTED if isinstance(k, str) and is_secret_key(k) else redact(v)
            for k, v in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(v) for v in value]
    return value


def new_run_id() -> str:
    """Sortable, unique: 20261021T153012Z-a1b2c3"""
    return f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"


class TraceWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("a", encoding="utf-8")
        self._seq = 0

    @classmethod
    def create(cls, runs_dir: Path, run_id: str | None = None) -> TraceWriter:
        run_id = run_id or new_run_id()
        return cls(runs_dir / run_id / "trace.jsonl")

    @property
    def run_id(self) -> str:
        return self.path.parent.name

    def event(self, type: str, **data: Any) -> None:
        self._seq += 1
        record = {"seq": self._seq, "ts": datetime.now(UTC).isoformat(), "type": type}
        record.update(redact(data))
        self._file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        self._file.flush()  # on disk now - survives a crash later in the run

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> TraceWriter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


def read_trace(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
