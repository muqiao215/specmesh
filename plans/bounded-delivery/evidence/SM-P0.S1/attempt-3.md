# SM-P0.S1 — 第 3 次定点续修，2026-09-14

本轮定点验证通过；整张 S1 卡仍 blocked / 未获独立接受，关闭率保持 0/4。
这不是新任务，没有重置次数、改名或开启子任务。原一次实现及前两轮修正/审查记录
保留于 [原记录](README.md)。本轮仅一次实现补丁；授权已用完，停止，不启动 S2。

## 基线与范围

- 核对的完整 HEAD：`d393c548a2a58989d65e6cdbd60a36e9a81a444f`，main，保留原 dirty 候选。
- 实现仅 `scripts/map_v0.py::render_view`、`specmesh_port/project_state.py::build_project_state`。
- 测试仅既有 `test_map_v0.py`、`test_machine_port.py`，新增 5 个方法；原测试不删不降级。
- 另更新本卡证据/三件套索引及接口已知缺陷说明；未改真实 Status/Current 声明来满足测试。
- 未改 schema、公共枚举、SPEC、Map 版本/预算/权威、service、CLI 入口、History 或 ControlMesh。
- 未提交 Git、推送、发布或安装；未启动 Goal、子代理、provider 验证或切换模型。
- 前两轮审查记录及累计 dirty diff 可读；未发现逐轮独立保存的 patch，不能虚构逐轮 diff。
- 第 3 次相对进入时 dirty 基线的完整代码/测试差异：[attempt-3.patch](attempt-3.patch)。
  临时原文件副本保留在 `/tmp/specmesh-attempt3-xHupYV/`，不作为持久交接依赖。

## 首个错误环节与最小修复

状态链：解析保留 `task_plan Status: done` 和 `progress Current: in progress`；
规范化已经产生 `{done, in_progress}`。首个错误在聚合：旧条件只检查完成与失败/未知。
现比较当前声明是否含多个规范化类别，并保留既有完成与失败/未知 blocker 的冲突规则。
历史 Done 不参与；同义类别（completed/done、working/in-progress）仍可 observed。
`observed` 继续仅表示输入已读取/复核，不代表完成或外部验收。冲突用既有 ambiguous，
保留两条原声明及 path、line、SHA-256、asserted_candidate，诊断显示归一化类别。

Map 链：代码解析、图节点/显式关系和 Area 门控均正确，不消费上述 project-state 模型。
修复前 context 为真实 derived 文件，存在 asserted configured_by 边，且 gated=False；
两个 query 的 context 排名分别 55/44，spec://map-v0 排名 10/8。输出选中 spec，却在
800-token 贪心裁剪时遗失配置入口。首个错误在 focus 选点，不是解析或缓存新鲜度。
现将选中节点的活动 asserted configured_by 目标作为同一个预算块纳入 focus；不硬编码
路径/query、不调 PageRank、不提高预算、不递归展开关系。Global 选点语义不变。

## 前后验证

先添加明确命名的两个真实查询回归和状态冲突回归，再运行未修实现：3 项均失败，exit 1。
完整原始输出：[before](attempt-3-before.log)。之后仅应用一次实现补丁。

| 场景 | 修复前 | 修复后 |
|---|---|---|
| fix Python public symbol extraction | context 节点缺失，800 Token | 实际 CLI 三入口均在，797/800 |
| verify content hash freshness and cache rebuild | context 节点缺失，800 Token | 实际 CLI 三入口均在，799/800 |
| 同任务 done + in progress | observed，无 conflict | ambiguous，有 declared_status_conflict；JSON/text CLI exit 3 |

测试方法数：Map 13/13、machine-port 40/40、Area Overlay 25/25，共 78/78（exit 0）。
原有 73 个方法保留并通过；新增 5 个方法含 scope/authority/budget 和状态同义词反例。
既有五个真实查询全部通过。旧记录“8/10”口径不精确：10 个方法中的同一个方法有
两个失败 subtest，并非两个独立失败方法；旧原始记录不删除。

命令：`PYTHONPATH=tests python3 -B -m unittest test_map_v0 test_machine_port test_area_overlay -v`。
原始输出：[tests](attempt-3-tests.log)。[CLI 输出](attempt-3-cli.log) 包含真实 build/check/areas、
两个 query 和 global，以及隔离 fixture 的冲突 JSON/text，二者来源字段与模型一致。
仅测试 fixture 改写为冲突，不改真实任务文档。Global 1195/1200；两个 Area current；
重复 build 逐字节一致；既有删缓存重建、内容哈希失效和 scope 重绑定测试通过。
本轮未做全仓审计、远端 CI、发行或新 Agent 独立验收。

## 实现与契约指纹

```text
map_v0.py      45ad735ea615f1cd9276f6a17683f792775f058a1504c9e6282bdfead6920a6b
project_state  9a479af17a566faed0faca102d57140d277a3b4d9f1cddcea9ee8956fa4b8131
map tests      10d030080c6ca7dd2e30b1f8202ba6279bba4e682af9f791ac39cf60b097aabc
machine tests  0dbe8e0f887073e94150bc22baa65d4ad4275d8d9d95053f82e3bbee21435ca5
state schema   751817af4846aa875b26bf1e5c3b774c833199d345fa86c229680799922f4aa0
SPEC.md        5ba5820f1d6ab67b6977520dd0cb2be6e02bbe7b45ce077de1eb35743f8d80ca
```

后两项与原证据相同。CLI 日志的缓存指纹绑定其运行时输入；文档交接写入后需重新 build/check，
不将旧日志指纹冒充最新仓库状态。

## 剩余问题与累计消耗

- 已报告的两个检索回归和 done/in-progress 反例均通过本次验证；不是完整自然语言状态解析器，
  未扩展否定句/语义理解，不能据此声称所有表述均可正确判定。
- S1 独立验收尚未发生，仍 blocked / not accepted，0/4；无权自动推进 S2。
- 按用户口径，累计尝试 **3**；前两轮记录保留。本轮实现补丁 **1**，追加修正 **0**。
- 新 Goal **0**、新子代理 **0**、产品 provider 调用 **0**、模型切换 **0**。
- 前两轮累计 token/费用 **unknown**；本轮新增 token/费用 **unknown**；累计 token/费用 **unknown**。
  无账户级逐任务账单数据，不能用产品 provider 调用为零推断 Agent 调用免费。
