# SpecMesh project context

## Why
Help people and agents recover project intent and current work across sessions and tools from
small, progressively linked files.

## User Intent
Use SpecMesh together with ControlMesh and History Viewer. SpecMesh owns reviewed project
knowledge; CM owns task execution; Viewer finds historical evidence. A native resumed session
retains provider context but does not supersede current code or reviewed project documents.

## Non-goals
No agent runtime, orchestration, transcript database, mandatory graph infrastructure or automatic
promotion of conversation claims to project truth.

## Success
A new agent can locate intent, architecture, decisions and the active plan without replaying history.
Experimental retrieval is adopted only after repeatable real-task evidence.

## Constraints
SPEC.md is normative. Templates are scaffolding, not filled project memory. Map facts are derived;
reviewed Markdown claims are asserted. Only current areas inject scoped memory. Caches are disposable.

## Current State
SPEC.md is v1.1.0 and matches the installed user standard at the start of release alignment.
Map v0 and Area Overlay implementation/review are complete (35 regression tests); both remain
experimental and do not expand the mandatory standard. The first GitHub Release v1.1.0 records that baseline. Distribution v1.2.0 is now published with the optional draft machine port; 39 tests pass, the Map is fresh, and SPEC.md matches the installed user standard.

## Current Priority
Repository self-adoption and v1.1.0 publication are complete. Further Map evolution waits for
repeated real-task gaps. The optional independent machine port is included as a draft tool in distribution v1.2.0; it does not change the mandatory standard or add orchestration. See [machine port](docs/CODEKIT-INTEGRATION.md).

## Knowledge Map
- Normative rules → [SPEC.md](SPEC.md)
- Architecture → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Decisions → [docs/DECISIONS.md](docs/DECISIONS.md)
- Release alignment → [plans/release-alignment/](plans/release-alignment/)
- Completed Map experiment → [plans/map-v0-spike/](plans/map-v0-spike/)
- Completed Area experiment → [plans/area-overlay-v0/](plans/area-overlay-v0/)
- Experimental configuration → [.specmesh/context.md](.specmesh/context.md)

- Plan status index → [plans/README.md](plans/README.md)

## Approved next direction

The primary coordinating Agent owns cross-project delivery. Repository-owned execution details and current status: [independent-plugin-port](plans/independent-plugin-port/task_plan.md). These future milestones remain planned; current released behavior retains its existing authority.
