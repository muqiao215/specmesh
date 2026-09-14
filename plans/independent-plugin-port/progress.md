> 历史 snapshot：以下保留 2026-09-12 的实现/发布/canary 记录，包含后来已由审计纠正的待办文字。2026-09-14 起的当前状态、唯一下一张卡与旧出口映射见 [bounded-delivery/progress.md](../bounded-delivery/progress.md)；本文件不触发另一条执行线。

> 2026-09-15：CM 接轨从 SpecMesh 必做范围退出，非完成；下文 CM 后续待办不再触发执行。当前独立验收与发行只以 bounded-delivery 为准。

# Current

2026-09-12: optional artifact requirement candidate transport implemented in the
independent service. Explicit source selection, bounded unique file requirements,
source hash/reference and snapshot revalidation preserve asserted-candidate authority.
No artifact creation, execution, or CM dependency was added.

# Done

Machine-port focused suite: 22 tests passed before documentation updates. Paired CM
suite: 9 tests / 37 assertions passed, including source mutation revocation and
unrequested/unreferenced candidate refusal. CM typecheck passed.

# Remaining

Full standalone suite passed: 57 tests, 6.493 seconds. Contract mirror verification,
commits and remote CI remain.
Explicit runtime adoption, reviewed authority, external closeout and the remaining
real-provider/device takeover matrix are not complete. Distribution remains 1.2.1;
this source change is not a release or installed-standard update.

# Next

Run the standalone regression suite and verify paired contract bytes before publishing
this independently usable candidate interface.

## Previous released baseline and native acceptance


## Current

Consistent document/Git inspection is published in [v1.2.1](https://github.com/muqiao215/specmesh/releases/tag/v1.2.1)
at `5fab9f0f824352ef6d32b72cc8a31050e6499b5f`. Python 3.11/3.12
[CI 34642616803](https://github.com/muqiao215/specmesh/actions/runs/34642616803) passed.
The local release tag and remote tag agree; installed normative SPEC.md matches byte-for-byte.
Discovery uses captured PROJECT
bytes, all present/missing selected files and task directories are revalidated, and descriptor
reads reject special files and substituted path components. POSIX descriptor support is
required only by this optional machine profile; Markdown remains platform-independent.

The final full regression run passed 54 tests in 6.462 seconds, including standalone
capability/unknown-closeout CLI assertions. Seven CM integration tests pass on Bun 1.3.11.
CM's corresponding source is published at `3073c7fe0758b79abae7724017b9df40e00d4f73`;
its independent CI result is recorded by CM's runtime-convergence plan.

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

Define externally verifiable closeout provenance without promoting self-authored claims;
extend the qualified local read profile to the remaining native/provider/device matrix.

## Paired snapshot qualification — 2026-09-12

Final standalone run: 54 tests, 6.462 s, passed; rebuilt Map reports fresh. The real Python
port and TypeScript CM adapter return identical dirty-worktree references. Seven CM tests
pass (32 assertions), covering missing documents before model preflight, unchanged grants,
profile/content revocation, real local task queue completion, unknown self-reported closeout,
optional startup without native credentials, and real subprocess stop/reaping. Task queue
execution in these tests is synthetic. A separate real OpenCode 1.18.29/M3 canary passed two
turns across CM reopen, with the same original session and five current document reads on
each turn. Independent native-database verification confirms changed PROJECT/findings
content and marker recall without reinjection. One task/two completed episodes, one model
preflight generation and two loopback fixture replies remain after duplicate input; nine
native commands and three model-run commands ran. Actual provider billing counts were not
measured. All nine containers are confirmed absent. No production writer or chat account
was changed. General native writes, other providers/devices and external result acceptance
remain separate gates; this read-only canary does not complete the full migration.
