# SpecMesh project context

## Why
帮助人和 Agent 从少量渐进链接的项目文件恢复意图、约束与当前工作，并完成可验证的独立交接。

## User Intent
优先交付独立 SpecMesh：无需 ControlMesh 或 History，也能读取当前状态、交接包含 dirty 基线的未完成任务，让全新 Agent B 产出被独立验收接受的实际结果，并独立发行。

2026-09-15 用户确认：SpecMesh 今后独立发展，不再要求与 CM 接轨。项目意图、计划、交接、验证与收尾由本仓独立定义和发行；外部工具可以消费 Markdown 或独立接口，但不形成绑定、配套升级或联合发行义务。Orca 也不是新的必需宿主。原生同会话 resume/marker recall 不等于全新 Agent 交付。

## Non-goals
不自建 Agent runtime、调度器、provider 管理、历史数据库或第四个总平台；不强制图基础设施，不自动把会话声明晋升为项目事实。本轮不做 Ops、多设备协作或跨仓生产切换。

## Success
全新 Agent 从入口和明确交接材料即可找到意图、架构、决定与唯一下一步；保留既有未提交修改，拒绝过期/取消任务，以实际 diff、固定验证和 owner 接受证明交付。状态读取、dirty 交接、新 Agent 实际交付、独立发行分别验收；实验性检索仍需重复真实任务证据。

## Constraints
SPEC.md 仍是已发布规范；本次方向在活动计划中规划，不代表规范正文已经升级。模板只是脚手架，Map 为 derived，已审查 Markdown 为 asserted；只有 current area 注入 scoped memory，缓存可丢弃。未知、旧 done 和结构检查 pass 不得成为外部任务验收。

不改 SPEC.md/全局标准链接。用户最新要求完成独立版4/4，按 S2 → S3 → R1 验收顺序推进，R1包含本仓已验收源码提交、独立发行和隔离安装；不覆盖已有入口或扩展到其他仓库。每张实现卡独占范围、一次实现与独立审查、至多两轮修正；S1 的第 3 次续修为用户显式追加授权，原次数保留。用户已追加授权由主助手完成所有SpecMesh进度并亲自实现；原尝试/失败不重置，按 S2 独立验收 → S3 → R1 串行推进。不用 Goal。

默认在主工作区推进，确需并行或测试隔离才使用独立目录/worktree；保留已有直接 push 授权，不一律要求 PR。已配置授权的 CBC/AGY 等可按任务承担实现/审查；S3 的单次模型调用范围已确认，尚未执行。产品验收是否需真实 provider 与开发执行者身份分开判断；发布/安装按对应卡授权处理。

## Current State
2026-09-14 规划前本机 main 为 `d393c548a2a58989d65e6cdbd60a36e9a81a444f`，工作区 clean。规范 v1.1.0；2026-09-13 审计核对最新发行 v1.2.1 为 `5fab9f0`，main 的 artifact-requirements 增量已有独立 CI，但尚未进入新发行。该远端状态是审计时观察，本轮没有重测。

SM-P0 独立 CLI/有界合同、SM-P1 声明 POSIX 快照的窄出口已有通过证据，应直接复用。原生 same-session 只读 canary 不关闭全新 Agent 验收。Map v0 与 Area Overlay 保留实验身份。本次四个增量验收单元当前 3/4；文档规划完成不算产品通过。

SM-P0.S1 经用户追加第 3 次定点续修后，已获原审查者独立接受：A–F 通过，78 项相关回归通过，两个真实 Map 查询恢复。累计尝试 3，前两轮失败与第 3 次补丁保留；实现未提交、未发布。见 [S1 独立验收](plans/bounded-delivery/evidence/SM-P0.S1/acceptance.md)。

2026-09-15 S2累计第5次实现后，原独立审查者接受A～F；Python3.11/3.12全套107/107通过。当前S1/S2/S3共3/4。S3全新AGY B单次完成真实命令，经独立接受；R1源码准备与独立发行验收进行中。
[S2接受](plans/bounded-delivery/evidence/SM-P1.S2/acceptance.md)；[S3执行](plans/bounded-delivery/evidence/SM-P4.S3/execution.md)。此前失败和平台拦截记录保留。

## Current Priority

完成R1：精确源码提交及CI、v1.3.0工件、干净安装、实际入口和升级/回退对账。S1～S3已接受；CM接轨不在范围。

## Knowledge Map
- Normative rules → [SPEC.md](SPEC.md)
- Architecture → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Decisions → [docs/DECISIONS.md](docs/DECISIONS.md)
- Active bounded delivery → [plan](plans/bounded-delivery/task_plan.md), [findings](plans/bounded-delivery/findings.md), [progress](plans/bounded-delivery/progress.md)
- Prior machine-port phases and evidence → [independent-plugin-port](plans/independent-plugin-port/task_plan.md)
- Release alignment → [plans/release-alignment/](plans/release-alignment/)
- Completed Map experiment → [plans/map-v0-spike/](plans/map-v0-spike/)
- Completed Area experiment → [plans/area-overlay-v0/](plans/area-overlay-v0/)
- Experimental configuration → [.specmesh/context.md](.specmesh/context.md)

- Plan status index → [plans/README.md](plans/README.md)

## Approved next direction

2026-09-14 起以本仓 [bounded-delivery](plans/bounded-delivery/task_plan.md) 为活动交付计划。2026-09-15 确认长期独立方向：旧 SM/X IDs 仅用于追溯，CM 接轨不再是后续必做项。四个独立验收单元分母不变；旧 SM-P0/P1 的历史窄通过另列，不重复计数，不另建跨仓权威进度库。
