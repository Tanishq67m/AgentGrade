# Static vs measured - shop-filesystem

| | |
|---|---|
| Server | secure-filesystem-server 2.0.0 |
| Static score | Glama TDQS, spec commit `b9881b0` (sha256 `3df9d731cb06`) |
| Judge | `openai/gpt-oss-120b`, 5 scoring(s) per definition |
| Generated | 2026-11-17 14:41 UTC |

TDQS reads only the tool definition (1.0-5.0; tier A >= 3.5, B >= 3.0 = passing, C >= 2.0, D). Measured = pass rate of real agent runs with that definition.

| Variant | Tools | TDQS mean (min-max) | Tier | Purp | Use | Behav | Param | Conc | Compl | Measured pass rate |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | search_files | 3.62 (3.4-4.0) | A | 4 | 3 | 4 | 3 | 5 | 2 | 4/36 (11%, CI 4%-25%) |
| glob-rules-only | search_files | 3.92 (3.7-4.3) | A | 5 | 3 | 4 | 3 | 5 | 2 | 18/24 (75%, CI 55%-88%) |
| explore-first-only | search_files | 4.12 (3.8-4.4) | A | 5 | 4 | 4 | 3 | 5 | 2 | 1/12 (8%, CI 1%-35%) |
| clear-search-description | search_files | 4.12 (3.9-4.4) | A | 5 | 4 | 4 | 4 | 5 | 2 | 17/24 (71%, CI 51%-85%) |
| upstream-2.2.0-description | search_files | 4.04 (3.9-4.2) | A | 5 | 4 | 4 | 3 | 5 | 2 | 2/12 (17%, CI 5%-45%) |
| glob-rules-generic-examples | search_files | 3.92 (3.7-4.5) | A | 5 | 3 | 4 | 3 | 5 | 2 | 3/12 (25%, CI 9%-53%) |

## Change vs `baseline`

| Variant | Δ TDQS | Δ measured pass rate |
|---|---|---|
| glob-rules-only | +0.30 | +64 points |
| explore-first-only | +0.50 | -3 points |
| clear-search-description | +0.50 | +60 points |
| upstream-2.2.0-description | +0.42 | +6 points |
| glob-rules-generic-examples | +0.30 | +14 points |

**Spearman rank correlation (TDQS vs measured), n = 6:** -0.09. With this few points it is a rough indication, not a test.

## What the judge said (first scoring of each distinct definition)

### search_files - baseline (TDQS 3.6, tier A)

> Recursively search for files and directories matching a pattern. The patterns should be glob-style patterns that match paths relative to the working directory. Use pattern like '*.ext' to match files in current directory, and '**/*.ext' to match files in all subdirectories. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.

*Summary:* The description clearly defines the tool's purpose and adds useful behavioral details, but it falls short on parameter explanation and output documentation, and it provides only implicit usage guidance.

- **Purp 5** - The description uses a clear verb "search" and specifies the resource "files and directories" with recursion and glob‑style patterns, making its function distinct from sibling tools like read_file or list_directory.
- **Use 3** - It notes the tool is useful "when you don't know their exact location," providing an implied usage scenario, but it does not state when not to use it or name alternative tools.
- **Behav 4** - Beyond the readOnlyHint annotation, the description adds behavior such as recursive glob matching, pattern syntax examples, and the restriction to allowed directories, with no conflict to the annotations.
- **Param 2** - The description explains the pattern format but does not clarify the required "path" parameter or the optional "excludePatterns" array, leaving most parameters undocumented despite 0% schema coverage.
- **Conc 4** - The text is compact and each sentence contributes useful information; a slight trimming could improve brevity, but overall it is well‑structured and front‑loaded.
- **Compl 2** - The output schema returns a single "content" string, yet the description only says it returns "full paths" without detailing format, leaving the response shape unclear.

### search_files - glob-rules-only (TDQS 3.7, tier A)

> Find files and directories by glob pattern under `path`. IMPORTANT: patterns are matched against paths RELATIVE to `path`, and a pattern WITHOUT '**/' only matches entries directly inside `path`, not in subdirectories. To search all subdirectories, start the pattern with '**/', e.g. '**/*.json' or '**/*invoice*'. Matching is on names, not file contents. Returns full paths of all matches. Only searches within allowed directories.

*Summary:* The definition clearly states the tool's purpose and adds useful behavior details, but it lacks explicit usage guidance, omits the optional excludePatterns parameter, and does not align with the output schema, limiting its overall completeness.

- **Purp 5** - The description uses a clear verb "Find" and specifies the resource "files and directories" with detailed pattern rules, distinguishing it from sibling read/list tools.
- **Use 3** - It explains how to use glob patterns but does not explicitly state when to prefer this tool over alternatives or any exclusions, leaving usage largely implied.
- **Behav 4** - Beyond the readOnlyHint annotation, the description clarifies pattern matching semantics, relative path handling, and that only names are matched, providing valuable behavioral detail.
- **Param 3** - With 0% schema coverage, the description explains the required "path" and "pattern" parameters well, but it omits any mention of the optional "excludePatterns" parameter.
- **Conc 4** - The text is compact and each sentence adds distinct information about matching rules and scope; it is brief yet comprehensive.
- **Compl 2** - The description says the tool returns full paths, but the output schema only defines a single "content" string, and the optional "excludePatterns" parameter is undocumented, leaving key output and parameter details incomplete.

### search_files - explore-first-only (TDQS 4.1, tier A)

> Recursively search for files and directories matching a pattern. The patterns should be glob-style patterns that match paths relative to the working directory. Use pattern like '*.ext' to match files in current directory, and '**/*.ext' to match files in all subdirectories. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories. If you don't know the folder layout yet, call directory_tree or list_directory first.

*Summary:* The description is strong on purpose and safety, offering clear guidance and useful behavior details. It falls short on fully documenting all parameters and the exact output format, but overall provides a concise and helpful overview.

- **Purp 5** - The description uses the specific verb "search" on the resource "files and directories" and adds the recursion and glob‑style pattern details. This makes it clearly distinct from sibling tools like list_directory or directory_tree.
- **Use 4** - It tells the agent the tool only searches within allowed directories and advises calling directory_tree or list_directory first when the folder layout is unknown, giving clear context for when to use it. It does not explicitly list cases where it should not be used.
- **Behav 4** - The description aligns with the readOnlyHint annotation (non‑destructive) and adds useful behavior such as recursive glob matching, allowed‑directory restriction, and pattern examples. No contradiction with annotations is present.
- **Param 3** - The description explains the "pattern" parameter and gives usage examples, but it does not describe the "path" base directory nor the optional "excludePatterns" array, leaving some parameters undocumented.
- **Conc 5** - The text is brief and each sentence contributes new information (purpose, pattern syntax, return value, safety, and alternative tools). There is no unnecessary filler.
- **Compl 3** - While the purpose and usage are well covered, the output schema (an object with a single "content" string) is not explained, leaving the format of the returned paths ambiguous.

### search_files - clear-search-description (TDQS 3.9, tier A)

> Find files and directories by glob pattern under `path`. IMPORTANT: patterns are matched against paths RELATIVE to `path`, and a pattern WITHOUT '**/' only matches entries directly inside `path`, not in subdirectories. To search all subdirectories, start the pattern with '**/', e.g. '**/*.json' or '**/*invoice*'. Matching is on names, not file contents. If you don't know the folder layout yet, call directory_tree or list_directory first. Returns full paths of all matches. Only searches within allowed directories.

*Summary:* The definition clearly states the tool's purpose and provides useful usage and behavior details, but it falls short on fully documenting optional parameters and the output format, limiting its completeness.

- **Purp 5** - The description uses the specific verb "Find" and clearly identifies the resource as "files and directories" with a glob pattern, distinguishing it from sibling tools like list_directory or directory_tree.
- **Use 4** - It advises to call directory_tree or list_directory first when the folder layout is unknown, giving a clear cue on when to use this tool, though it does not enumerate explicit exclusions or alternatives.
- **Behav 4** - The description details pattern‑matching rules, relative‑path semantics, and the fact that only names are matched, providing behavioral information beyond the readOnlyHint annotation without any contradictions.
- **Param 3** - With 0 % schema coverage, the description explains the required parameters (path and pattern) and their matching behavior, but it does not mention the optional excludePatterns parameter, leaving a gap.
- **Conc 4** - The text is compact and each sentence adds distinct value (purpose, pattern rules, usage tip, return value), though it could be slightly tighter.
- **Compl 2** - The description says the tool returns full paths, but the output schema only defines a generic "content" string, and the description does not explain this mismatch or the exact format of the returned data.

### search_files - upstream-2.2.0-description (TDQS 4.2, tier A)

> Find files and directories by NAME, not by content: this tool never reads or searches inside files. It walks the tree under 'path' and matches a glob pattern against each entry's path relative to 'path' (case-sensitive). Use '*.ext' to match entries directly under 'path', and '**/*.ext' or '**/name' to match at any depth. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.

*Summary:* The tool description is clear about purpose and core behavior, offering solid usage guidance and parameter meaning despite missing details for an optional argument. However, it fails to describe the output format, which limits contextual completeness.

- **Purp 5** - The description uses a specific verb "Find" and clearly identifies the resource (files and directories) and the method (by name using glob patterns), distinguishing it from content‑search tools and from sibling read/write tools.
- **Use 4** - It explains the appropriate scenario – locating files when the exact location is unknown – and explicitly excludes content searching. It does not name alternative tools, but the context is clear.
- **Behav 4** - The description adds concrete behavior (case‑sensitive glob matching, depth handling, allowed‑directory restriction) that is not covered by the readOnlyHint annotation, while staying consistent with the annotations.
- **Param 4** - With 0 % schema coverage, the description supplies meaning for the required parameters "path" and "pattern" (search root and glob syntax). It omits any detail about the optional "excludePatterns", leaving a gap.
- **Conc 5** - The description is brief, front‑loaded, and each sentence provides distinct, useful information without redundancy.
- **Compl 2** - The output schema only defines a single string field "content", but the description says the tool returns full paths to matching items and does not explain how those paths are represented, leaving the return format undocumented.

### search_files - glob-rules-generic-examples (TDQS 3.7, tier A)

> Find files and directories by glob pattern under `path`. IMPORTANT: patterns are matched against paths RELATIVE to `path`, and a pattern WITHOUT '**/' only matches entries directly inside `path`, not in subdirectories. To search all subdirectories, start the pattern with '**/', e.g. '**/*.ext' or '**/name'. Matching is on names, not file contents. Returns full paths of all matches. Only searches within allowed directories.

*Summary:* The tool description clearly states its purpose and adds valuable behavioral details, but it lacks explicit usage guidance, omits one optional parameter, and does not explain the output format, resulting in moderate overall completeness.

- **Purp 5** - The description uses a clear verb "Find" and specifies the resource "files and directories" with the scope of a glob pattern under a given path, distinguishing it from sibling read/list tools.
- **Use 3** - The description explains what the tool does but does not explicitly state when to prefer it over other tools or any exclusions; usage is only implied by the need for glob pattern searches.
- **Behav 4** - Beyond the readOnlyHint annotation, the description details pattern matching rules, relative path semantics, and that only names are matched, providing useful behavioral context without contradicting annotations.
- **Param 3** - With 0% schema description coverage, the text explains the purpose of "path" and "pattern" well, but it omits any mention of the optional "excludePatterns" parameter, leaving a gap.
- **Conc 4** - The description is compact and each sentence adds distinct information, though it could be slightly trimmed; overall it is well‑structured and avoids unnecessary filler.
- **Compl 2** - The output schema expects a "content" string, yet the description only says it returns full paths without specifying format. Additionally, the optional "excludePatterns" parameter is undocumented, making the description incomplete.

## Caveats

- Small n: a handful of definitions and one agent model. This can show that TDQS did not track measured behavior here, not that it never does.
- Glama's production judge model is not published; absolute scores may differ from glama.ai. Compare variants with each other.
