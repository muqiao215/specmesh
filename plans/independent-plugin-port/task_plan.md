# Independent SpecMesh machine port — historical roadmap

> 2026-09-15 范围决定：SpecMesh 独立发展，不再要求 CM 接轨。下文 CM 适配要求、SM-A10 配对验收和历史外仓状态仅作追溯，不是当前交付义务。SM-P2 退出范围而非完成；独立权威/真实交接由活动计划 S2/S3 承接。更广信任模型及完整 provider/device 矩阵仅为可选扩展，不绑定 Orca。

> 2026-09-15 收口：独立交付在 [bounded-delivery](../bounded-delivery/task_plan.md) 已4/4接受，v1.3.0正式发行并安装。本文件只保存旧阶段历史；CM接轨已退出范围，不自动恢复其待办。
>
> 2026-09-13 审计确认 SM-P0 Acceptance 列窄技术出口通过（下方 planned 为旧状态），SM-P1 限声明 POSIX profile 通过；不重做或扩大这两项结论。原 progress 的“commits/remote CI remain”已由该审计纠正。更广的 CM lifecycle、外部验收和 provider/device 条件仍开放，映射及证据见 [当前 findings](../bounded-delivery/findings.md)。

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
| SM-P0 | Draft contract review and standalone distribution | No CM dependency; CLI in clean optional runtime; schema fixtures and bounded input/output | accepted for the historical narrow profile; see bounded-delivery mapping |
| SM-P1 | Consistent inspection snapshot including dirty content | Concurrent HEAD/uncommitted edit/symlink replacement tests; stale references detected | complete for declared POSIX snapshot profile; standalone/paired checks and release CI passed |
| SM-P2 | CM hook semantics: task start, handoff, verify, closeout | Historical host-specific gate requirements only | retired from SpecMesh scope by user on 2026-09-15, not accepted/completed; paired-test history retained |
| SM-P3 | Reviewed authority and acceptance evidence provenance | Self-reported passed manifest never certifies external result; reviewer and evidence identity explicit | planned |
| SM-P4 | Repeatable real Agent takeover across controlled repos | Agent finds current intent/decisions/plan and produces accepted task result without replaying all history | planned |

## Validation matrix

SM-A01 independent operation with CM absent; SM-A02 stale HEAD/content; SM-A03 missing selected task docs; SM-A04 traversal/symlink/oversize; SM-A05 exact contract/version mismatch; SM-A06 timeout/invalid response; SM-A07 no source writes; SM-A08 no asserted/derived authority promotion; SM-A09 closeout external evidence unavailable stays unknown; SM-A10 paired CM/standalone outputs agree for shared fixtures.

## Rollback

Keep SPEC.md backward compatible unless a separately reviewed normative release changes it. Disable an optional adapter/hook when incompatible; do not silently approve gated work or remove repository continuity. No deployed source file replacement until release identity is verified. Preserve user-specific local standard changes rather than overwriting blindly.

## Dependencies / next

Next: follow [bounded-delivery](../bounded-delivery/task_plan.md): independent S2 acceptance → real fresh-Agent S3 → standalone R1. No CM host adoption or cross-repository release is required. Unknown closeout still cannot become verified merely through structural checks.

Historical references only (not dependencies): [CM lifecycle](https://github.com/muqiao215/ControlMesh/blob/main/plans/runtime-convergence/task_plan.md), [Viewer evidence](https://github.com/muqiao215/Codex-Claude-History-Viewer/blob/main/plans/agent-handoff-service/task_plan.md). The earlier 57 standalone / 9 paired checks remain historical results, not current acceptance.
