# Progress

## Current

Consistent document/Git inspection is implemented locally. Discovery uses captured PROJECT
bytes, all present/missing selected files and task directories are revalidated, and descriptor
reads reject special files and substituted path components. POSIX descriptor support is
required only by this optional machine profile; Markdown remains platform-independent.

The initial full regression run passed 54 tests in 6.312 seconds. Additional standalone
capability/unknown-closeout CLI assertions and CM integration are being verified next.

## Done

Ownership, actual code seams, acceptance, dependencies and rollback documented.

Reproduced a repository clean filter being executed by the previous git-status check.
The port now compares raw Git blob identities/index/HEAD through bounded read-only
plumbing instead, with content filters/hooks/transports disabled. Tests cover filter
non-execution, missing partial-clone objects, dirty edits, index changes, atomic file
replacement, symlink substitution, FIFO input, Git output limits and timeout cleanup.

## Remaining

Execute the phase gates in task_plan.md; record concrete tests and released versions.

## Issues

External/provider/device acceptance requires scoped runtime execution and evidence.

## Next

Wire the declared snapshot profile to CM's trusted TypeScript adapter and lifecycle,
then run paired standalone/CM checks before source publication.
# Paired snapshot qualification — 2026-09-12

Final standalone run: 54 tests, 6.462 s, passed; rebuilt Map reports fresh. The real Python
port and TypeScript CM adapter return identical dirty-worktree references. Seven CM tests
pass (32 assertions), covering missing documents before model preflight, unchanged grants,
profile/content revocation, real local task queue completion, unknown self-reported closeout,
optional startup without native credentials, and real subprocess stop/reaping. Task queue
execution in these tests is synthetic; real Agent consumption and external acceptance are
separate gates. Distribution version 1.2.1 is prepared; remote CI/release not yet verified.
