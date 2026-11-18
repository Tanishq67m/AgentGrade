# Static vs measured - shop-filesystem

| | |
|---|---|
| Server | secure-filesystem-server 2.0.0 |
| Static score | Glama TDQS, spec commit `b9881b0` (sha256 `3df9d731cb06`) |
| Judge | `openai/gpt-oss-20b`, 5 scoring(s) per definition |
| Generated | 2026-11-18 05:56 UTC |

TDQS reads only the tool definition (1.0-5.0; tier A >= 3.5, B >= 3.0 = passing, C >= 2.0, D). Measured = pass rate of real agent runs with that definition.

| Variant | Tools | TDQS mean (min-max) | Tier | Purp | Use | Behav | Param | Conc | Compl | Measured pass rate |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | search_files | 3.80 (3.7-3.9) | A | 5 | 3 | 4 | 2 | 5 | 3 | 4/36 (11%, CI 4%-25%) |
| glob-rules-only | search_files | 4.26 (4.1-4.3) | A | 5 | 3 | 5 | 3 | 5 | 5 | 18/24 (75%, CI 55%-88%) |
| explore-first-only | search_files | 4.40 (4.1-4.7) | A | 5 | 5 | 4 | 3 | 5 | 5 | 1/12 (8%, CI 1%-35%) |
| clear-search-description | search_files | 4.56 (4.2-4.8) | A | 5 | 5 | 5 | 4 | 5 | 4 | 17/24 (71%, CI 51%-85%) |
| upstream-2.2.0-description | search_files | 4.38 (4.3-4.5) | A | 5 | 3 | 4 | 4 | 5 | 5 | 2/12 (17%, CI 5%-45%) |
| glob-rules-generic-examples | search_files | 4.46 (4.3-4.7) | A | 5 | 3 | 5 | 4 | 5 | 5 | 3/12 (25%, CI 9%-53%) |

## Change vs `baseline`

| Variant | Δ TDQS | Δ measured pass rate |
|---|---|---|
| glob-rules-only | +0.46 | +64 points |
| explore-first-only | +0.60 | -3 points |
| clear-search-description | +0.76 | +60 points |
| upstream-2.2.0-description | +0.58 | +6 points |
| glob-rules-generic-examples | +0.66 | +14 points |

**Spearman rank correlation (TDQS vs measured), n = 6:** +0.20. With this few points it is a rough indication, not a test.

## What the judge said (first scoring of each distinct definition)

### search_files - baseline (TDQS 3.9, tier A)

> Recursively search for files and directories matching a pattern. The patterns should be glob-style patterns that match paths relative to the working directory. Use pattern like '*.ext' to match files in current directory, and '**/*.ext' to match files in all subdirectories. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.

*Summary:* The description is clear, concise, and provides useful behavioral context, but it lacks explicit usage guidelines, full parameter coverage, and a precise description of the output format. Overall, it is a solid but not exceptional definition.

- **Purp 5** - The description clearly states the tool’s function—recursively searching for files and directories using glob-style patterns relative to the working directory—and specifies the return type (full paths). It also notes the constraint of only searching within allowed directories, which distinguishes it from other file‑listing tools.
- **Use 3** - The description hints at appropriate use cases (“Great for finding files when you don't know their exact location”) but does not explicitly state when to avoid the tool or recommend alternatives such as list_directory or list_allowed_directories.
- **Behav 4** - Beyond the annotations, the description explains glob pattern syntax, relative path handling, and the restriction to allowed directories, providing useful behavioral context that the annotations alone do not cover.
- **Param 3** - With 0% schema description coverage, the baseline is 3. The description adds meaning for the pattern parameter (glob style, relative paths) but omits details for the path and excludePatterns parameters, so it does not fully compensate for the coverage gap.
- **Conc 5** - The description is concise, front‑loaded, and each sentence contributes distinct information—purpose, pattern syntax, examples, return value, and scope—without unnecessary filler.
- **Compl 3** - While the description covers the main purpose and pattern semantics, it does not mention the excludePatterns parameter or the exact output format (the output schema indicates a single string, yet the description says it returns full paths). Thus it is partially complete.

### search_files - glob-rules-only (TDQS 4.1, tier A)

> Find files and directories by glob pattern under `path`. IMPORTANT: patterns are matched against paths RELATIVE to `path`, and a pattern WITHOUT '**/' only matches entries directly inside `path`, not in subdirectories. To search all subdirectories, start the pattern with '**/', e.g. '**/*.json' or '**/*invoice*'. Matching is on names, not file contents. Returns full paths of all matches. Only searches within allowed directories.

*Summary:* The description is highly effective: it clearly defines the tool’s purpose, provides useful pattern‑matching guidance, discloses key behavioral constraints, and aligns with the output schema. Minor gaps remain in explicit usage guidelines and full parameter coverage, but overall it meets the highest quality standards.

- **Purp 5** - The description begins with a clear verb‑phrase: "Find files and directories by glob pattern under `path`", explicitly stating the resource and operation. It also specifies the scope (under `path`) and the nature of the match (names, not contents), which distinguishes it from sibling tools like `list_directory`.
- **Use 3** - The description explains how to use glob patterns (e.g., starting with '**/' to search subdirectories) and notes that patterns are matched relative to `path`. However, it does not explicitly advise when to choose this tool over alternatives such as `list_directory` or `read_file`.
- **Behav 4** - Beyond the annotations, the description reveals important behavioral details: pattern matching is relative to `path`, a pattern without '**/' only matches direct entries, and the search is confined to allowed directories. These nuances are not captured by the annotations alone.
- **Param 3** - With 0% schema description coverage, the baseline is 3. The description adds meaning for `path` and `pattern` (relative matching, subdirectory rules) but omits discussion of `excludePatterns`, so it partially compensates for the lack of schema detail.
- **Conc 5** - The description is concise, consisting of five focused sentences that each convey distinct, necessary information without redundancy.
- **Compl 5** - The output schema is a single string field `content`, and the description explicitly states that it returns full paths of all matches, covering the return value fully.

### search_files - explore-first-only (TDQS 4.5, tier A)

> Recursively search for files and directories matching a pattern. The patterns should be glob-style patterns that match paths relative to the working directory. Use pattern like '*.ext' to match files in current directory, and '**/*.ext' to match files in all subdirectories. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories. If you don't know the folder layout yet, call directory_tree or list_directory first.

*Summary:* The description is highly effective: it clearly defines the tool’s purpose, offers concrete usage guidance, adds valuable behavioral details, and is concise and complete. The only shortfall is incomplete parameter coverage for 'path' and 'excludePatterns'.

- **Purp 5** - The description clearly states the tool performs a recursive search for files and directories using glob-style patterns, explicitly distinguishing it from other file operations.
- **Use 5** - It advises that the tool only searches within allowed directories and recommends using directory_tree or list_directory when the folder layout is unknown, providing explicit alternatives.
- **Behav 4** - Beyond the readOnlyHint annotation, the description reveals recursion depth, relative path matching, and the restriction to allowed directories, adding meaningful behavioral context.
- **Param 3** - The description explains glob-style patterns and gives examples, but it omits details about the required 'path' parameter and the optional 'excludePatterns', leaving some parameter semantics uncovered.
- **Conc 5** - The description is concise, well‑structured, and each sentence contributes useful information without redundancy.
- **Compl 5** - It fully describes the output format (full paths in a string) and clarifies the operational scope (allowed directories), matching the output schema.

### search_files - clear-search-description (TDQS 4.6, tier A)

> Find files and directories by glob pattern under `path`. IMPORTANT: patterns are matched against paths RELATIVE to `path`, and a pattern WITHOUT '**/' only matches entries directly inside `path`, not in subdirectories. To search all subdirectories, start the pattern with '**/', e.g. '**/*.json' or '**/*invoice*'. Matching is on names, not file contents. If you don't know the folder layout yet, call directory_tree or list_directory first. Returns full paths of all matches. Only searches within allowed directories.

*Summary:* The description is highly clear, well‑structured, and provides extensive behavioral detail, but it falls short in fully documenting the output format, leading to a lower completeness score.

- **Purp 5** - The description clearly states "Find files and directories by glob pattern under `path`", using a specific verb and resource, and explains the relative nature of patterns, distinguishing it from other file tools.
- **Use 5** - It explicitly advises when to call directory_tree or list_directory first and notes that the search is limited to allowed directories, giving concrete guidance on when to use this tool versus alternatives.
- **Behav 5** - Beyond the readOnlyHint annotation, the description discloses pattern matching rules, relative path semantics, exclusion handling, and the restriction to allowed directories, providing full behavioral context.
- **Param 4** - With 0% schema description coverage, the description compensates by explaining how `path` and `pattern` are interpreted, though it omits details about `excludePatterns`. This partial compensation earns a 4.
- **Conc 5** - The description is front‑loaded, concise, and each sentence adds value, fitting the tool’s scope without unnecessary verbosity.
- **Compl 2** - The output schema expects a single string field `content`, yet the description says it returns full paths of all matches, implying a list. This mismatch indicates incomplete coverage of the return format.

### search_files - upstream-2.2.0-description (TDQS 4.5, tier A)

> Find files and directories by NAME, not by content: this tool never reads or searches inside files. It walks the tree under 'path' and matches a glob pattern against each entry's path relative to 'path' (case-sensitive). Use '*.ext' to match entries directly under 'path', and '**/*.ext' or '**/name' to match at any depth. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.

*Summary:* The description is highly effective: it clearly defines the tool’s purpose, provides useful behavioral context, compensates for missing schema details, and remains concise. Minor improvement could be explicit guidance on when not to use the tool or alternatives.

- **Purp 5** - The description begins with "Find files and directories by NAME" and clearly states the resource and action, distinguishing it from sibling tools that read file contents.
- **Use 3** - It notes the tool is useful when the exact location is unknown, but does not explicitly state when not to use it or reference alternatives such as list_directory.
- **Behav 5** - The text explains that the tool never reads file contents, walks the tree under a given path, applies case‑sensitive glob patterns, and only searches within allowed directories—information beyond the readOnlyHint annotation.
- **Param 4** - With 0% schema description coverage, the description supplies key details: the meaning of the glob syntax, the optional excludePatterns, and the case‑sensitivity of matching.
- **Conc 5** - The description is six focused sentences, each adding distinct value without redundancy, and front‑loads the core purpose.
- **Compl 5** - It specifies that the tool returns full paths to all matching items, covering the output schema’s content field, and notes the restriction to allowed directories.

### search_files - glob-rules-generic-examples (TDQS 4.3, tier A)

> Find files and directories by glob pattern under `path`. IMPORTANT: patterns are matched against paths RELATIVE to `path`, and a pattern WITHOUT '**/' only matches entries directly inside `path`, not in subdirectories. To search all subdirectories, start the pattern with '**/', e.g. '**/*.ext' or '**/name'. Matching is on names, not file contents. Returns full paths of all matches. Only searches within allowed directories.

*Summary:* The description is highly effective: it clearly states the tool’s purpose, provides detailed behavioral context, and is concise and complete. It could improve by explicitly referencing alternative tools for guidance, but overall it meets the highest evaluation tier.

- **Purp 5** - The description begins with "Find files and directories by glob pattern under `path`", a clear verb+resource statement. It also specifies that only allowed directories are searched, distinguishing it from sibling tools that read or write files.
- **Use 3** - The description explains how glob patterns work (relative vs. '**/' prefixes) and that matching is on names, which implies when to use this tool versus a simple list or read operation. However, it does not explicitly reference alternative tools or provide exclusion rules.
- **Behav 5** - Beyond the annotations (readOnlyHint true, openWorldHint false), the description details pattern matching rules, relative path semantics, subdirectory search behavior, and the fact that only allowed directories are scanned, providing full behavioral context.
- **Param 3** - With 0% schema description coverage, the baseline is 3. The description covers the semantics of `path` and `pattern`, but omits details about `excludePatterns`, so it partially compensates but does not fully cover all parameters.
- **Conc 5** - The description is concise, consisting of five focused sentences that each add distinct information without redundancy.
- **Compl 5** - The output schema is a simple string of full paths, and the description explicitly states that it returns full paths of all matches, covering the return format. All other relevant behavior (pattern rules, allowed directories) is also documented.

## Caveats

- Small n: a handful of definitions and one agent model. This can show that TDQS did not track measured behavior here, not that it never does.
- Glama's production judge model is not published; absolute scores may differ from glama.ai. Compare variants with each other.
