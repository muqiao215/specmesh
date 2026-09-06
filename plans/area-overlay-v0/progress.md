# Progress

## Current

Area Overlay v0 全部完成：35/35 测试通过；用户代码 Review 通过（5 项评审发现全部修复并复验）；实现、仓库接入与规划文档已提交并推送（`56fe4fd`/`0ea0d5a`/`1222e5a`）；adopt/adapt/reject 结论已写入 README。缓存重建后 `check` fresh，两区 current。

## Done

### 前一轮（计划期）

- 读取用户引用的"SpecMesh 每周推进"会话，提取 Area Overlay 方向与证据协议候选。
- 建立 `plans/area-overlay-v0/` 三件计划文件并分类每周研究候选。
- 基线：10 项 Map v0 测试通过，缓存 fresh，global 1197/1200。

### 本轮（实现期）

- `scripts/map_v0.py`：新增 normalize_area_id、parse_areas（严格行解析）、_validate_areas（格式/唯一性/1..3 anchors/superseded_by 无链）、load_areas、_resolve_anchor、resolve_areas；RELATION_RE 支持 `scope:`；build_graph 绑定 `source_state.area_resolution` 并校验 dangling scope；render_view 增加 gating + areas 段；CLI 增加 `areas` 子命令。
- 修复聚合优先级：ambiguous > candidate_rebind > unresolved（唯一候选是行动建议，必须浮出；仅 current 注入）。
- areas 段原子渲染 + 预算预留（budget/3 上限），node 行按剩余预算渲染。
- 测试文件不再发射符号节点（谓词复用 tests 关系规则），修复 RealTaskFocusTests 5/5 回归。
- `tests/test_area_overlay.py`：20 项新测试（规范化/重复 ID/四状态/重命名/歧义/superseded/解析器严格性/确定性/预算/CLI）。
- 真实仓库集成：`.specmesh/repo-areas.v0.yaml`（area:map-derivation、area:memory-authority）；`core.md` 五条关系加 `scope: area:map-derivation`（待用户复核）；`context.md` 增加 `area_overlay` 配置与 Area Overlay 文档。
- 验证：30/30 通过；global 1199/1200 含 areas 段；focus ≤800 含查询相关 area 块；缓存重建逐字节一致。
- 拷贝实验（/tmp/opencode/specmesh-scratch）：map_v0.py→repo_map.py 后 `candidate_rebind` + 唯一候选 `code://scripts/repo_map.py#build_graph`，`spec://map-v0` 停止注入；人工改 YAML 后 `current` 恢复注入。

## Remaining

（无 — v0 收口完成；后续候选见 findings.md 的每周候选分类）

## Issues

- 确认后的视图中，stale memory 关系目标（如 implemented_by → 旧路径）以 `[code; asserted]` 节点呈现（2026-09-07 评审修复：不再伪装派生节点，排名亦不涉及）；memory 内容本身仍属人工维护（memory_write_policy: reviewed）。属设计边界，非缺陷。

## Next

无。实验闭环：README adopt/adapt/reject 结论 + 最终 build → check → areas → global/focus 验证完成后收口。

## 2026-09-06 评审修复轮

- 修复全部 5 项评审发现（2 P1 + 3 P2），35/35 测试通过（+6 新测试：非规范 scope 拒绝+建议、malformed 行 fail-loud、stale 目标 asserted+gate+不排名、重复字段、重复 anchors 头、split_into 拒绝；1 个旧语义测试改写为拒绝路径；旧 fixture 移除 derived-provenance 行）。
- 真实仓库：build/check/areas（两区 current）、global 1199/1200、focus 788，重建逐字节一致（sha 7ee49764…）。
- scratch 验证：git mv map_v0.py→repo_map.py → candidate_rebind（旧路径 0 幻影节点行）；YML 人工确认 → current + spec://map-v0 / mem://core 回归。
- core.md defines 改挂 area:memory-authority；context.md 增补权威规则文档；task_plan 移除拆分声明并加非目标。

## 2026-09-07 复审收口轮

- 用户复审：5 项代码问题全部关闭，无新实现缺陷，代码 Review 通过。
- 修正交接文档失效结论：Current 30/30 → 35/35；Issues 与 findings.md 中 stale 目标"派生节点"描述改为 `[code; asserted]`；Gating rule 段同步评审后语义（scoped-only 非真实文件判据、fail-loud scope 校验）。
- README Map v0 实验段新增 Area Overlay v0 adopt/adapt/reject 结论 + `areas` 命令。
- task_plan 最后一项勾选；最终验证 build → check → areas → global/focus。
