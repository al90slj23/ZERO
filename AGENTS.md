# ZERO Agent Entry

ZERO is a reusable project initialization template. Read `.ai/L1#Overview/guide.md`, use `.ai/L2#Index/toc.md` to locate current standards, and follow `.ai/L3#Standards/references/zero-first-use.md` for first adoption.

- For a new or existing target project, run `.ai/L0#Execution/workflows/local/zero-bootstrap.sh --target <project> --prepare-only`, then complete the generated project adaptation specification before the full initialization.
- Keep the target's verified facts, existing rules and deployment boundaries. Never copy ZERO examples as project facts or replace business deployment scripts.
- Maintain knowledge and configuration sources only in `.ai`. QMD/CodeGraph tools, models and indexes are generated there; client and tool entries are pointers.
- After changing an adopting project's source Markdown, run its retrieval adapter `refresh` before task completion. Use QMD for document lookup and CodeGraph for source relations when useful; verify provenance.
- While developing this template, update its L0 specification, current L3 rules, L2 navigation and L1 entry together. Test bootstrap with isolated fixtures; do not initialize a different project accidentally.
