# Architecture

SPEC.md defines the continuity standard. templates/ supplies minimal entry and task-file examples.
README.md is the public introduction; PROJECT.md records this repository's intent and priorities.

scripts/map_v0.py derives a deterministic, budgeted graph from code/Git and reviewed memory.
.specmesh/context.md configures experimental inputs; .specmesh/memory/ supplies asserted claims;
.specmesh/repo-areas.v0.yaml declares reviewed responsibility anchors. .specmesh/cache/ is rebuildable
output and is never authoritative or tracked. Area ambiguity or pending rebind suppresses scoped
memory; malformed authoritative declarations fail loudly.

History Viewer may show these files and old conversations. ControlMesh may execute agents working
on them. Neither changes the normative ownership of reviewed project knowledge. Markdown adoption
installs SPEC.md as the user's standard and uses templates only where a controlled project's actual
needs justify them. The optional machine profile runs independently as a bounded subprocess;
Markdown adoption does not require it.

## Read Next
- [Normative standard](../SPEC.md)
- [Experimental configuration and commands](../.specmesh/context.md)
- [Decisions](DECISIONS.md)
- [Release plan](../plans/release-alignment/task_plan.md)

## Codekit integration (v1.2.0)

See [CODEKIT-INTEGRATION](CODEKIT-INTEGRATION.md) for the new module boundary, public invocation and limits. This local implementation does not establish deployment acceptance.

`specmesh_port/service.py` owns progressive selection, structural findings and proposal generation.
`snapshot.py` owns descriptor-anchored observations and content/identity revalidation, including
missing files. `git_reader.py` owns bounded, filter-free Git plumbing with transport denial.
`__main__.py` exposes a capability descriptor and read-only request/result JSON. Contracts stay
inside this independent package; host adapters mirror and validate them. No module imports CM or
History Viewer. Assertions, derived references and externally verified results remain distinct.
