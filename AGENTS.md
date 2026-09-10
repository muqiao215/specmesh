# Project instructions

This repository maintains SpecMesh v1.1. Read PROJECT.md first. Read SPEC.md for normative
rules, docs/ARCHITECTURE.md for implementation boundaries, docs/DECISIONS.md for rationale,
and only the relevant plans/<task>/ files. CLAUDE.md delegates to this entry.

SPEC.md is the versioned standard; templates mirror its minimum structure. Map v0 and Area
Overlay are experiments, not mandatory adoption requirements. Preserve asserted/derived
authority and current-only scoped-memory injection. Generated .specmesh/cache stays untracked.

Maintain task_plan.md, findings.md and progress.md for substantial work. Update project intent,
architecture or decisions only for durable changes. Verify changes with unittest and, when map
inputs change, rebuild/check the map. Publish reviewed source; copy SPEC.md to local user-level
installations only after release verification. Never let generated graphs rewrite reviewed memory.
