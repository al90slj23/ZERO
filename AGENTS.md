# ZERO Agent Entry

ZERO is a reusable project initialization template. Read `.ai/L1#Overview/guide.md`, use `.ai/L2#Index/toc.md` to locate current standards, and follow `.ai/L3#Standards/references/zero-first-use.md` for first adoption.

- For a new or existing target project, run `.ai/L0#Execution/workflows/local/zero-bootstrap.sh --target <project> --prepare-only`, then complete the generated project adaptation specification before the full initialization.
- Keep the target's verified facts, existing rules and deployment boundaries. Never copy ZERO examples as project facts or replace business deployment scripts.
- Maintain knowledge and configuration sources only in `.ai`. QMD/CodeGraph tools, models and indexes are generated there; client and tool entries are pointers.
- With an exact path/symbol, read the relevant range directly. Unknown document topics start with a small scoped QMD `lex` result set; code relationships start with a narrow CodeGraph query. Broaden to vector/expanded search only when needed.
- Reuse current unchanged excerpts already visible in this conversation. Treat returned current source as already read; fetch only missing or stale ranges, and cap printed results instead of dumping full tool objects. Required initial project context and complete-file audits still apply.
- On unavailable retrieval, make at most one targeted retry before scoped `rg`/range-read fallback. Preserve owning-source verification and project boundaries.
- Batch an adopting project's source Markdown edits and run its retrieval adapter `refresh` once at task completion. Read-only tasks and unchanged sources do not proactively refresh; explicit repair requires a diagnosed stale/broken index.
- While developing this template, update its L0 specification, current L3 rules, L2 navigation and L1 entry together. Test bootstrap with isolated fixtures; do not initialize a different project accidentally.
