# Findings

The roadmap is grounded in repository code, existing contracts and prior recorded acceptance, not the prototype archive alone. Implementation status and remaining gates are in task_plan.md. No new runtime migration or fleet rollout is claimed complete by this plan.

## Consistent snapshot findings (2026-09-12)

- Original discovery read PROJECT.md separately from hashing; same-HEAD dirty edits could pass with inconsistent references. Selected index changes also require comparing full metadata, not only a modified boolean.
- An isolated fixture reproduced `git status` executing a configured clean filter. Replaced it with `ls-files --stage -z` and `ls-tree -z HEAD` plus raw blob identity comparison. The regression asserts the filter's marker is never created.
- Descriptor-relative traversal and final revalidation catch path substitution, same-byte atomic replacement, missing-file appearance/deletion, FIFO and size violations. A substitution fixture spies on actual reads and verifies outside bytes are never consumed.
- Git 2.43.0 on this host does not accept the newer `--no-lazy-fetch` command option. The reader uses `GIT_NO_LAZY_FETCH=1` plus protocol denial for compatibility; a missing partial-clone tree cannot start a fixture remote helper. Primary reference: [Git environment and literal pathspec documentation](https://git-scm.com/docs/git).
- `modified` uses raw bytes/mode versus index and HEAD, deliberately without content filters. Normalized content may conservatively appear modified; this flag supplies context, never authority.
- Fifty-four standalone tests pass locally, including a real CLI, five-second Git deadline, owned-child cleanup and an unknown closeout result. TypeScript host pairing is tracked separately; green structural tests do not prove Agent consumption or external result acceptance.

## Artifact requirements — 2026-09-12

An Agent's successful protocol result does not prove required artifacts exist. The
optional port therefore transports explicit requirements independently of runtime
permissions and execution evidence. Source manifests share the descriptor/HEAD
snapshot; no declared output file is opened by this feature. Closeout still cannot
be certified by a self-authored manifest. CM must own adoption and verification.
