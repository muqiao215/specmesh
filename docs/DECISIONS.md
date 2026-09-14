# Decisions

## 2026-09-15 — SpecMesh 独立发展，不再以 CM 接轨为交付目标

决定：用户明确“以后的 specmesh 就单独了，不用和 cm 接轨”。SpecMesh 自主维护项目记忆、任务交接、独立接口与发行；CM lifecycle、CM 等义适配及三仓组合对齐退出本项目必做范围，标记为退出范围而非通过验收。

依据：用户本次指令为权威；[Orca与CM区别](chatgpt-conversation://6aa801c2-a34c-83e9-b4f5-3308147f1afe) 仅提供职责分离的讨论背景，其中集成方案不自动成为实施授权。

保留：既有接口兼容性、历史适配代码和验证证据；独立 S2 验收、S3 全新 Agent 真实交接与 R1 发行要求。没有独立验收结论仍不能标 done。

不采用：以 Orca 替换 CM 成为强制宿主；要求外仓配套升级、联合发布或迁移运行时；因方向变化删除历史记录。完整 provider/device 矩阵为可选后续扩展，不替代当前真实 Agent 验收。

重访条件：用户明确提出具体外部集成需求时另行界定范围；不能从旧计划自动恢复 CM 接轨。本决定覆盖下文旧决定中的 CM 后续必做含义。

## Keep continuity separate from execution and historical recall
SpecMesh stores reviewed intent/status; ControlMesh owns runtime lifecycle; History Viewer owns
historical discovery. Combining these responsibilities would make old transcript claims appear
current and couple the portable standard to an agent product. Revisit only with an evidenced
cross-project contract gap, not because all three tools contain context.

## Keep Map v0 and Area Overlay experimental
The graph improves bounded retrieval while separating derived code facts from asserted memory.
Tests and one repository experiment do not establish a universal required structure. Reject
mandatory graph services and automatic anchor rebinding; revisit after repeated real-task evidence.
Detailed adopt/adapt/reject conclusions remain in README.md and the completed Area plan.

## 2026-09-11 — Integrate against existing repository authority

Reuse the existing storage/parsers and keep SpecMesh independently callable. Do not install a second TaskHub from a proposal or equate historical handoff with live completion. The human overview and headless retrieval have separate entry points. See [scope and remaining limits](CODEKIT-INTEGRATION.md). Status: implemented for v1.2.0; broader roadmap gates remain planned.

## 2026-09-14 — 先独立可用版，按单卡退出

决定：SpecMesh 优先独立状态读取、dirty 基线交接、全新 Agent B 的实际任务验收和独立发行。最小通用流程合同定义意图/计划/交接/验证/收尾的输入、输出、失败与证据责任；CM 的执行权、History 的历史证据边界保留。文件格式与独立使用不得反向依赖宿主。详细出口及旧 ID 映射见 [bounded-delivery](../plans/bounded-delivery/task_plan.md)。

原因：现有独立 CLI 与 POSIX 快照已具窄通过证据，主要缺口是完整状态、可消费 dirty 交接和实际结果被接受。先要求三仓串联会把独立可用性推迟；same-session read/reopen 或 marker recall 又不能证明全新 Agent 完成交付。原生续接可以保留为宿主能力，但不替代本次独立验收。

不采用：先建 CM 插件宿主或第四个总平台；从零重写已验证 port/snapshot；用常驻 Goal/模型轮询追逐所有仓库。每张卡一次实现、一次独立审查、至多两轮修正，验证并更新本仓状态后退出，不自动取下一张。

本次规划不改已发布 SPEC.md 或全局标准链接；新行为通过明确的独立输出合同和有界任务验收后再决定发行。旧 SM-P0/P1 窄通过保留，SM-P2/SM-P3 更广范围、SM-P4 provider/device 与跨仓发行条件不自动关闭。当前四个增量验收单元只在本仓计数，不重复计算父项。

重访条件：独立 S1–S3 与 R1 取得真实验收后，若 CM/History 消费同一合同出现实际兼容缺口，再单列最小适配卡；若确实需要改变规范正文或扩大平台/信任范围，记录新出口和版本影响后另行审查。规划本身不使这些后续动作自动开始。
