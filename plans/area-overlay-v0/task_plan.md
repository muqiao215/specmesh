# Task

## Goal

在现有 Map v0 之上验证一个最小的 Area Overlay：让长期 Memory 绑定稳定职责 ID，而 Map 负责把职责解析到当前文件和公开符号，从而在代码移动后保持记忆连续性且不误绑。

## Context

Map v0 已验证派生代码图、人工语义记忆、内容哈希和预算化 focus 可以共用检索入口。尚未解决的问题是：`code://<path>#<symbol>` 是当前坐标，不是跨重命名、拆分与合并的长期身份。

## Requirements

- 使用人工审查、进入 Git 的 `.specmesh/repo-areas.v0.yaml` 保存少量稳定职责
- Area ID 使用规范化的 `area:<kebab-id>`，写入时检查格式和全仓唯一性
- Area 只保存 `purpose`、当前 anchors 和 `read_next`，不复制源码或聊天记录
- 派生 Map 输出绑定 `source_state` 的 `area_resolution`
- 解析状态仅为 `current`、`unresolved`、`ambiguous`、`candidate_rebind`
- Memory 通过 `scope: area:<id>` 关联职责；本实验不得自动改写 Memory
- 相同输入逐字节一致，缓存仍可删除重建
- 任务视图最多呈现 purpose、三个入口和 `read_next`

## Non-goals

- 不自动为每个目录、文件或符号创建 Area
- 不用 Git rename 自动迁移职责或 Memory
- 不增加数据库、向量检索、daemon、MCP 服务、后台同步或每目录 Map
- 不在本实验中解决所有 patch、test、environment 证据协议
- 不直接把实验升级为 SpecMesh 稳定规范
- 不另建与现有 `.specmesh/cache/repo-map.json` 平行的 NDJSON Map 格式
- 不建模一对多拆分（`split_into`）：v0 schema 显式拒绝该字段；职责拆分时人工建立新 Area ID，旧 ID 用 `superseded_by` 指向其中一个继任者

## Plan

- [x] 记录当前 Map v0 基线，确定 Area YAML 与派生记录的最小契约
- [x] 实现 ID 规范化、重复检查和 anchor 解析
- [x] 为四种解析状态添加确定性测试
- [x] 验证无关重命名、职责移动、歧义与显式替代（一对多拆分为显式非目标，见 Non-goals）
- [x] 将 Area 结果接入受预算约束的 focus 视图
- [x] 用真实任务验证跨路径变化的定位与 Memory 连续性（真实仓库 + /tmp/opencode 拷贝实验）
- [x] 更新实验文档，保留 adopt / adapt / reject 结论（README「Area Overlay v0 结论」节）

## Success

同一职责只改变文件或公开符号位置时，保留 Area ID 并在人工确认 anchor 后继续命中原 Memory；职责拆分或语义变化时必须建立新 ID；无法唯一解析时停止注入相关 Memory，并给出可验证原因。

三条件均已验证：scripts/map_v0.py → repo_map.py 重命名后 area:map-derivation 进入 `candidate_rebind` 且给出唯一候选 `code://scripts/repo_map.py#build_graph`，`spec://map-v0` 停止注入；人工改 YAML 后恢复 `current`，Memory 重新注入；歧义（≥2 候选）与无候选场景由测试覆盖（ambiguous/unresolved 停止注入）。

## Status

实现与验证完成；用户评审（5 项：2 P1 + 3 P2）全部修复并复验：35/35 测试通过。P1-1 stale code 目标不再标注 derived（asserted），PageRank/渲染只用活跃 scope 子图，candidate_rebind 期间旧路径 0 幻影节点行（仅保留人工 rebind 提示行）；P1-2 memory 解析 fail-loud（malformed 行、非规范 scope 给规范化建议、悬空 scope 均带 文件:行号 报错，不再静默归一化/丢弃）；P2：defines 关系改挂 area:memory-authority；拆分显式列为非目标（split_into 字段被拒，有测试）；parse_areas 拒绝重复字段。真实仓库 global 1199/1200、focus ≤800、缓存重建逐字节一致；scratch 拷贝验证 candidate_rebind → 人工确认 → current + Memory 回归完整闭环。用户复审（2026-09-07）：代码 Review 通过，5 项发现全部关闭、无新缺陷。实验闭环完成：adopt/adapt/reject 结论已入 README，交接文档已同步最终语义（35/35、asserted 标注、fail-loud scope 校验）。

## Next Step

撰写实验文档结论（adopt / adapt / reject），并把 core.md 的人工 scope 标注提交用户复核。

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| 聚合优先级错误：任一 anchor 无候选即判 unresolved，掩盖同区另一 anchor 的唯一候选 | 1 | 重排为 ambiguous > candidate_rebind > unresolved；仅 current 注入，安全性不变 |
| 视图测试预算过紧：80 token 被 node 行占满，areas 段被原子丢弃 | 1 | 测试显式传 400；CLI fixture 预算 80→200 |
| node 贪婪耗尽预算，areas 段在 focus 视图永远放不下 | 2 | 先构建 areas 段并预留其 token（上限 budget/3），node 行按剩余预算渲染 |
| 新测试文件 ~45 个符号节点令 PageRank 度集中，挤掉 context.md（RealTaskFocusTests 5/5 回归） | 2 | 测试文件不再发射符号节点（文件节点 + imports/tests 边已足够导航）；谓词复用 tests 关系规则 |
| AreasCliTests/调试脚本写 `.specmesh/memory/core.md` 前未建父目录（FileNotFoundError） | 1 | mkdir parents；memory_root 必须指向文件而非目录 |
| test_missing_areas 视图中 spec://render 缺失 | 1 | 调试证实为排名+预算（排名第 5，第 5 行放不下），非 gating 缺陷 |
| 评审修复轮：旧测试 fixture 的 `provenance: derived` 关系行依赖旧的静默跳过行为，fail-loud 解析后 8 个旧测试报错 | 1 | 语义变更属预期：memory 中 provenance 恒为 asserted；fixture 移除该行，对应测试改为断言 malformed 报错 |
