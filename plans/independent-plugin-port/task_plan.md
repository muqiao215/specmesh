# Independent SpecMesh machine port and CM lifecycle integration

## Status / owner

Status: consistent snapshot published as v1.2.1, paired with the TypeScript CM candidate, and accepted for real local OpenCode read/continuation. External closeout and the remaining provider/device matrix stay open. Owner: SpecMesh maintainers. CM calls this interface; SpecMesh stays independently usable. Normative Markdown rules remain separate from optional executable tooling.

## Observed implementation

`specmesh_port/service.py` checks root/HEAD/path containment and selected continuity documents through revalidated descriptor snapshots. CLI is bounded JSON request/response with declared capabilities; propose_update is a Python method returning a diff. `verify_closeout` stays unknown without external verification. CM's TS candidate now has an optional task-start gate and handoff/verify operations; production cutover is not implied. Tracked Markdown is an asserted candidate, not reviewed authority.

## Requirements

- Preserve standalone Markdown use and independent CLI/library operation. No import of CM, Viewer, native history database or device coordinator.
- Version request/result schemas, declare tool capabilities and contract compatibility; CM adapter pinning must be visible and tested.
- Distinguish structural conformity, asserted project facts, observed code state and external execution evidence. None automatically confers authorization.
- Bind inspection to relevant content hashes, full HEAD and explicit task scope; changes during inspection produce stale/unknown, not confident pass.
- Proposal generation never applies code or publishes. Required unknown/error gate cannot become pass merely because a subprocess exited zero.

## Phases

| ID | Work | Acceptance | State |
|---|---|---|---|
| SM-P0 | Draft contract review and standalone distribution | No CM dependency; CLI in clean optional runtime; schema fixtures and bounded input/output | planned |
| SM-P1 | Consistent inspection snapshot including dirty content | Concurrent HEAD/uncommitted edit/symlink replacement tests; stale references detected | complete for declared POSIX snapshot profile; standalone/paired checks and release CI passed |
| SM-P2 | CM hook semantics: task start, handoff, verify, closeout | Hook request carries scope/version/evidence; timeout/unknown fail required gate; no implicit TaskHub writes | task-start/handoff/unknown-closeout candidate passes paired tests; external acceptance ownership remains open |
| SM-P3 | Reviewed authority and acceptance evidence provenance | Self-reported passed manifest never certifies external result; reviewer and evidence identity explicit | planned |
| SM-P4 | Repeatable real Agent takeover across controlled repos | Agent finds current intent/decisions/plan and produces accepted task result without replaying all history | planned |

## Validation matrix

SM-A01 independent operation with CM absent; SM-A02 stale HEAD/content; SM-A03 missing selected task docs; SM-A04 traversal/symlink/oversize; SM-A05 exact contract/version mismatch; SM-A06 timeout/invalid response; SM-A07 no source writes; SM-A08 no asserted/derived authority promotion; SM-A09 closeout external evidence unavailable stays unknown; SM-A10 paired CM/standalone outputs agree for shared fixtures.

## Rollback

Keep SPEC.md backward compatible unless a separately reviewed normative release changes it. Disable an optional adapter/hook when incompatible; do not silently approve gated work or remove repository continuity. No deployed source file replacement until release identity is verified. Preserve user-specific local standard changes rather than overwriting blindly.

## Dependencies / next

CM lifecycle ownership: https://github.com/muqiao215/ControlMesh/blob/main/plans/runtime-convergence/task_plan.md
Viewer context evidence: https://github.com/muqiao215/Codex-Claude-History-Viewer/blob/main/plans/agent-handoff-service/task_plan.md
Next: validate the declared snapshot capability against the TypeScript CM adapter and wire
task-start/handoff checks. Required unknown closeout remains blocked until external
acceptance is owned and verified; structural checks cannot supply that evidence.
