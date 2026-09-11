# Codekit integration

Status: implemented and validated for v1.2.0; publication evidence is tracked by the release coordinator. Future roadmap phases remain planned.

## Scope
# Optional independent machine port (draft)

SpecMesh's normative file convention remains `SPEC.md`. This optional Python 3.11+ profile exposes the same project-continuity boundary to tools without adding a CM dependency, transcript database, Agent runtime or required daemon. Markdown-only users need no new runtime.

```sh
python -B -m specmesh_port --allowed-root /absolute/project < request.json
```

Example request (substitute the full current Git SHA):

```json
{"contract_version":"specmesh.port.v1-draft","operation":"check","repo_root":"/absolute/project","expected_head":"0000000000000000000000000000000000000000","task_path":null,"mode":"read_only"}
```

The zero SHA intentionally fails freshness checks; obtain the actual HEAD first. The standalone command validates a bounded request and returns JSON. Supported operations are inspect, check, prepare_handoff, propose_update and verify_closeout. `propose_update` generates a proposal only; it never applies it. CM currently exposes the read-only subset through its own optional adapter.

The service checks repository-root and allowed-root binding, full before/after HEAD, bounded progressive documents and path/symlink containment. A selected task requires task_plan.md, findings.md and progress.md. A tracked document remains asserted_candidate; tracking alone does not make it reviewed authority. Check pass means these structural checks passed, not semantic correctness of every project claim. Concurrent uncommitted edits are not completely bound by HEAD checks. Closeout remains unknown without external verification; a self-reported passed acceptance manifest is insufficient.

The draft schemas live inside specmesh_port/contracts and are mirrored by the CM adapter. This is deliberate interface versioning, not shared installation state. No package publication, default-standard replacement or general plugin host is included. Future integration must preserve standalone use and verify actual task-launch/closeout callers before claiming automatic gates.

## Acceptance
- Review full repository callers before adapting recipes.
- Preserve existing storage/parser authority and original worktrees.
- Run affected regressions and explicit fixture integration.
- Record unverified production/platform boundaries.

## Next
Review docs/CODEKIT-INTEGRATION.md and the current diff; reconcile newer base commits before merge. Broader runtime work remains separate.
