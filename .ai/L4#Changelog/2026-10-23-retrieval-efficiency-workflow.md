# v2.1.2 retrieval efficiency workflow

Date: 2026-10-23. Status: implementation and validation in progress.

Current entry rules now favor known-path range reads, small scoped QMD lexical results and narrow CodeGraph relationship queries. Unchanged evidence already visible in the conversation is reused; callers expand only for missing context, freshness or completeness requirements. Tool-result printing is bounded, and unavailable retrieval has a finite fallback path.

Source edits are batched before one completion refresh. Read-only tasks do not proactively refresh; diagnosed index problems use explicit repair. Existing mandatory project context, first-adoption audits and ownership/security boundaries remain in force.

Tool/model pins and the physical six-layer layout remain unchanged. The [active specification](../L0%23Execution/specs/completed/retrieval-efficiency/00.spec-01.requirements.md) tracks runtime and comparable-task validation. No reduction ratio or cost benefit is claimed before measurement.
