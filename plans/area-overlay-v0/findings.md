# Findings

## Referenced weekly conversation

以下内容来自用户引用的 ChatGPT 会话，属于待仓库验证的研究候选，不自动视为项目事实或执行指令。

- Map 与 Memory 已形成的核心边界：代码结构为 `derived`，经审查的 Markdown 为 `asserted`。
- 最新研究提出稳定职责层：文件和符号是当前坐标，`area:<id>` 才承担长期职责身份。
- 建议吸收 Nx 的逻辑节点/文件证据分离、Backstage 的规范化引用、Prow 的局部作用域、Graphiti 的失效/替代语义。
- 建议拒绝中央 Catalog、UUID 服务、图数据库、自动聊天抽取、daemon 和自动 Memory 迁移。
- 最新建议实验为 Repository Map v0 Area Overlay，重点验证 `current / unresolved / ambiguous / candidate_rebind`，不是搜索质量。

## Candidate backlog from earlier weekly work

需要与当前仓库核对后分类为 `implemented / partial / missing / rejected`：

- Map 缺失语义：`not_indexed / indexed_not_selected / searched_not_found`
- 执行表面与提交表面分离，以及未跟踪文件角色
- `patch_candidate` 的基准提交、涉及路径摘要与 stale 判定
- 环境权威、锁文件漂移和 `environment_stale`
- 基线失败、候选差值和测试稳定性完整序列
- verifier/test 变更的反事实敏感性验证
- 稳定 Area ID 与当前代码坐标的解析层

## Current hypothesis

Map v0 已经落地，Area Overlay 是最小且自然的下一步；其余证据协议已有真实 fixture 研究，但是否应进入 SpecMesh 稳定规范，仍需以仓库现状和重复任务证据判断。

## Repository gap check — 2026-09-06

当前仓库 HEAD 为 `9f8616d`，规范版本为 v1.1；工作区在本计划创建前干净。v1.1 新增的是开放 PR 的单轨与定期收口纪律，不包含每周研究中的 Area 或证据协议。

| 候选 | 状态 | 仓库证据 | 判断 |
|---|---|---|---|
| Map v0：代码/记忆双权威、内容哈希、全局/focus 预算 | `implemented_experimental` | `.specmesh/context.md`、`.specmesh/memory/core.md`、`scripts/map_v0.py`、10 项测试 | 已落地且发布，但仍是非规范性 spike |
| 稳定 `area:<id>` 与 anchor 解析 | `missing` | 全仓只有本计划提及 area；生成器只认识 `code/mem/spec` | 当前最自然的下一步 |
| `current / unresolved / ambiguous / candidate_rebind` | `missing` | Map JSON 无 area resolution 记录 | 应随 Area Overlay 一起验证 |
| `not_indexed / indexed_not_selected / searched_not_found` | `missing` | Map 只输出选中节点，未声明 producer 能力或检索覆盖 | 重要，但不应与 Area v0 同批扩大范围 |
| execution/submission surface 与 untracked 角色 | `verified_once_external_fixture` | History Viewer 的 R-001 fixture 已验证 tracked-diff-only 交接失败和四类 untracked 角色；SpecMesh 仓库尚无 schema | 仍是 `lesson_candidate`，待第二个独立任务 |
| patch candidate 基准/路径摘要/stale 判定 | `verified_once_external_fixture` | R-001 fixture 已验证 unchanged、`reverify_on_new_base`、`stale_candidate` 和 conflict | 不塞进 Area 实验，待第二个独立任务 |
| environment authority / `environment_stale` | `partial_external_fixture` | R-001 记录了 OpenCode 默认模型漂移；该 fixture 没有项目锁文件，无法验证 lock drift | 证据不完整，不能晋升 |
| baseline delta、稳定性序列 | `verified_once_external_fixture` | R-001/N-001/U-001 差值与三次一致运行已保存 | 待第二个独立任务 |
| verifier/test 反事实敏感性 | `verified_once_external_fixture` | 旧实现 + 新 verifier 失败、新实现 + 新 verifier 通过；弱 verifier 被判 `proof_gap` | 待第二个独立任务 |
| 开放变更收口纪律 | `implemented_normative` | SPEC v1.1，commit `9f8616d` | 已落地，不进入本计划 |

## Scope decision

本计划只推进 Area Overlay，因为它直接延续已经发布的 Map v0，并且能在一个小型、确定性的 fixture 中证伪。其余缺口保留为后续候选；把它们同时实现会重新把 SpecMesh 推向大而全的流程框架。

## Format adaptation

每周会话建议以 `repo-map.v0.ndjson` 输出 Area resolution，但真实 Map v0 已使用 `.specmesh/cache/repo-map.json` 的 canonical JSON。Area 实验应扩展现有图 schema，不创建第二套并行 Map 格式。人工权威文件定为 `.specmesh/repo-areas.v0.yaml`。

## Precedence decision — 2026-09-06 实现

`resolve_areas` 聚合优先级定为 `ambiguous > candidate_rebind > unresolved`：任一 anchor 有 ≥2 候选即 ambiguous（注入错误 anchor 的代价最高）；否则任一 anchor 存在唯一候选即 candidate_rebind（行动建议必须浮出，per-anchor reason 仍报告 no-candidate 的 anchor）；全部无候选才 unresolved。注入安全性不受影响——只有 `current` 注入。

## Gating rule — 2026-09-06 实现（2026-09-07 评审后修订）

节点仅当其全部关系带 scope、scope ∩ injectable(current 且非 superseded) = ∅、且不属于真实文件集合（sources 路径）时被 gate；任一 unscoped 关系的端点永不 gate（向后兼容：无 scope 的 memory 行为不变）。判据从早期的 `mem://`/`spec://` 前缀改为"scoped-only 且非真实文件"：mem/spec 自动覆盖，stale `code://` 旧路径同样被 gate，真实文件（如 SPEC.md）只丢 scoped 边、节点保留；带 `#` 的符号节点不属于真实文件集合，随 scope gate。scoped edge 仅在 scope ∈ injectable 时渲染。构建期 scope 校验 fail-loud：非规范形式（不再静默 normalize，报错附 normalize_area_id 建议）、悬空 scope 均为带 `文件: 行号` 的 RuntimeError；`- relation:` 行解析失败（含 `provenance: derived`）同样报错。

## Ranking & budget findings — 2026-09-06 实现

- 符号节点会把 PageRank 度集中到所属文件：新增 ~45 符号的测试文件使 `tests/test_area_overlay.py` 排名第一，挤掉 `code://.specmesh/context.md`（RealTaskFocusTests 5/5 回归）。修复：测试文件（复用 tests 关系谓词）不再发射符号节点；文件节点 + imports/tests 边已足够导航。
- node 行贪婪耗尽预算会令 areas 段永远放不下；修复：先构建 areas 段（原子块，cap = budget/3），node 行按 budget − section_tokens 渲染。
- 单行 node 约 11–18 token（长符号 id 更贵）；fixture 视图测试预算需 ≥400 才能同时容纳 node 与 area 块。
- `spec://render` 在 80 token 视图缺席的根因是排名+预算（排第 5，余量不足），gating 集合为空——不是 gate 缺陷。

## Scratch-copy validation — 2026-09-06

`map_v0.py → repo_map.py` 重命名：area:map-derivation → `candidate_rebind`，唯一候选 `code://scripts/repo_map.py#build_graph`；`spec://map-v0` 从 focus 消失。人工仅改 YAML anchors → `current`，`spec://map-v0` 恢复注入。Memory 文件全程未被工具改写。已知边界（2026-09-07 评审后已修正标注）：stale memory 关系目标（旧路径）在确认后以 `[code; asserted]` 节点呈现——诚实标注"仅 memory 断言、代码未派生"，等待人工更新 core.md 目标路径；gating 管注入时机，memory 内容本身仍属人工维护（memory_write_policy: reviewed）。

## Desktop entry

- 已创建 `/home/muqiao/桌面/SpecMesh` 符号链接。
- 链接解析到 canonical repository：`/home/muqiao/桌面/obsidian/my-programming-world/编程/SpecMesh`。
- 通过该链接执行 `git rev-parse --show-toplevel` 返回同一仓库路径。

## Review-fix round — 2026-09-06 评审修复

- Memory 解析语义收紧为 fail-loud：`- relation:` 行不完整（含 `provenance: derived`，memory 中 provenance 恒为 asserted）、scope 非规范（不再静默 normalize，报错附 normalize_area_id 建议）、scope 悬空，均 RuntimeError 且带 `文件: 行号`。旧 fixture 依赖的"静默跳过"被判定为设计缺陷（评审 P1-2）。
- Stale code:// 目标（重命名后的旧路径）authority 一律 `asserted`：memory 端点节点永不在文件循环中产生，文件循环覆盖全部真实文件；"未被代码派生"的事实不得标 derived（评审 P1-1）。
- 活跃 scope 子图：_rank 邻接只含 scope 为 None 或 injectable 的边；_gated_memory_nodes 从 mem/spec 前缀判断改为"scoped-only 且 非真实文件"判断（real_files = sources 路径集合）——mem/spec 自动覆盖，真实文件（如 SPEC.md）只丢 scoped 边不丢节点，符号节点（带 #）不属于 real_files 故仍被 gate。
- 实测证据：scratch 重命名后 global/focus 中旧路径节点行 0 次，唯一出现是 `[candidate_rebind]` 人工提示行本身；人工确认 YAML 后 stale memory 端点以 `[code; asserted]` 呈现（诚实标注，等待人工更新 core.md）——与确认前"伪装成 derived 幻影"有本质区别。
- parse_areas 每 item 维护 seen_fields，重复标量字段/重复列表头报 `duplicate area field 'X'`。
- `defines`（mem://core → spec://map-v0）是语义身份关系，改挂 area:memory-authority：实现重命名不得隐藏核心语义记忆（评审 P2）。
- 一对多拆分不建模：split_into 作为未知字段被拒（有回归测试）；拆分 = 人工建新 ID + 旧 ID superseded_by 指向继任者之一。
