# Task

## Goal

在真实 SpecMesh 仓库完成一个最小 Map v0 spike，验证代码派生图与人工语义记忆可以共享地址和检索协议，同时保持不同权威、新鲜度和生命周期。

## Requirements

- 提交型入口为 `.specmesh/context.md` 与 `.specmesh/memory/core.md`
- 派生缓存为 `.specmesh/cache/repo-map.json`，不进入 Git
- 只使用 Python 标准库
- 提取文件、Python 公开符号、import/reference、测试关系；其它语言退化为文件级
- 使用内容哈希判定缓存新鲜度，输出确定性 JSON
- 同一图生成全局视图与任务 focus，预算分别不超过 1200/800 个 v0 token
- 用五个真实任务验证入口、实现与测试定位

## Non-goals

- 不增加向量数据库、MCP、后台进程、Git Hook 或每目录 CODEMAP
- 不把派生代码事实与人工记忆赋予相同权威
- 不将 spike 直接宣称为稳定产品

## Plan

- [x] 检查仓库基线与现有规范
- [x] 实现上下文、记忆根和确定性图生成器
- [x] 添加单元测试与五任务定位验收
- [x] 验证确定性、内容哈希失效、删除缓存重建和预算
- [x] 更新 README/规范边界与任务记忆
- [x] 使用三个新 Agent 完成五任务定位验收
- [x] 审阅 diff 并提交推送

## Success

Map v0 在同一 HEAD 上逐字节稳定，源码变化会使旧缓存失效，删除缓存后可完整重建，两种视图均受预算约束，五个真实任务能定位相关入口、实现和测试。

## Status

完成：实现、自动测试、真实仓库验证、新 Agent 定位验收及发布均已完成。

## Next Step

后续只在真实任务暴露检索缺口时迭代，不把 Map v0 自动升级为 SpecMesh 规范要求。

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| None | 0 | — |
