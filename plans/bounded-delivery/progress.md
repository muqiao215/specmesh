# Progress

> 最新：S1/S2/S3/R1全部独立接受（4/4），v1.3.0已发行并安装；旧结果按历史保留。

## Current

done

独立可用版4/4。源码/tag0bfdfd1d4c79bdefc5926b87877253e69a6f93a7，v1.3.0正式发行；双Python CI各112/112、远端下载和安装29/29、smoke各6项通过。specmesh --version=1.3.0。见[R1证据](evidence/SM-P0.R1/release.md)、[独立接受](evidence/SM-P0.R1/acceptance.md)。文档收口不改发行源码身份。

## Done

- SM-P1.S2 首次实现：定义独立 `specmesh.handoff.v1` schema (`contracts/specmesh-handoff.schema.json`)，不污染旧 strict result。
- 新增 `specmesh_port/handoff.py`：实现目标/约束/决定提取、完成/失败/未知分类、剩余工作、唯一下一步、完整 HEAD 绑定、staged/unstaged/untracked 显式覆盖及基于多源的确定性 `scope_fingerprint`。
- 实现消费前前置检测 (`verify_handoff` 与 `--verify-handoff`)：检测 stale HEAD、同 HEAD 内容变更、dirty 文件缺失/哈希不匹配、缺证据、状态冲突与任务取消，并在异常时严格拒绝可执行状态 (`executable: false`, exit 3)。
- 更新 `specmesh_port/__main__.py`：新增 `--handoff [json|text]` 与 `--verify-handoff`；保留旧默认 CLI 行为（无 flag 时仍返回旧 result 契约）。
- 新增 `tests/test_handoff.py` 11 项针对性回归：覆盖 clean、staged+unstaged、untracked、同 HEAD 篡改、stale HEAD、缺源/缺证据、失败冲突、已取消任务、多候选下一步及 CLI 交互。
- 运行总套件 `test_map_v0`、`test_machine_port`、`test_area_overlay`、`test_handoff`，89/89 全部通过 (exit 0)。
- 更新 `docs/CODEKIT-INTEGRATION.md`，同步 handoff 规范、CLI 入口与消费前门禁语义。

- S1 收口：原独立审查者接受 A–F，78/78 通过；文档更新后主执行者重跑 Map/Area 38/38 通过，build/check fresh，实现与测试 hash 均与接受候选一致。累计尝试 3，无新增实现补丁；以下保留先前过程。

- 读取仓库入口/架构/决定、原 port 计划、下载附件和 2026-09-13 最终要求审计；核对实际入口与当前 HEAD。
- 规划起点：`main`，`d393c548a2a58989d65e6cdbd60a36e9a81a444f`，写入前工作区 clean；保留本轮文档 dirty 修改，未改已有产品代码。
- 明确独立状态、dirty 交接、全新 B 实际交付、独立发行四个增量单元，映射旧 SM/X IDs，并把 CM 宿主/全 provider/device/三仓组合留为开放的后续边界。
- 给 S1 写成可直接分发的任务卡，其余三卡只保留行为、入口/写范围、验收、证据、预算/停止和不自动下一张的必要约束。
- 更新 PROJECT、计划索引、决定与旧主计划/进度顶部承接指针；旧进度正文、历史 canary、失败与审计链接保留。
- SM-P0.S1：新增独立 `specmesh.project-state.v1` schema 与有限 Markdown 状态抽取器；每条语义声明绑定相对路径、行号、源 SHA 和 asserted_candidate 权威。
- 新增显式 `--project-state json|text`，两种呈现来自同一模型；旧默认 CLI、request/result schema 与退出码路径未改。
- 新增 8 项状态回归，总 machine-port 30/30 通过：完整状态、复杂卡片标签/验收表、JSON/text 一致、显式任务选择、缺证据/状态冲突、dirty 当前 hash、stale/读取中变化、Markdown 不执行。
- 真实仓库精简环境试跑：当前 bounded-delivery 可提取 S1-A～S1-F、13 条约束和唯一 Next；两种输出 exit 0，5 个已有 dirty 文档均显式列入 coverage，未称整个工作区 clean。
- 首次独立审查拒绝候选：Done 冒充 Evidence、fenced code 伪造标题、text 控制符透传、text 缺身份来源/声明权威、缺 blocker 仍 observed、合法大输入逃逸成 request_rejected。
- 第 1 轮修正：分离 Done 与 Evidence；围栏内容不参与标题/字段/任务链接；所有 text 动态值转义 C0/C1；身份与声明显示来源/权威；空 blocker 标题与缺标题分开；4097 字符/超过 200 条声明稳定降为 unknown。新增 5 项回归，总 machine-port 35/35 通过。
- 第二次独立复验发现：历史 Done 参与当前状态判断、CommonMark 伪 closing fence/缩进代码绕过、51 task candidates 逃逸 schema。第 2 轮修正将 Done 放入只展示的 history，收紧围栏/缩进语法并给 candidates 加 50 项边界；新增 3 项回归，总 machine-port 38/38，真实仓恢复 observed。
- 最终独立复验确认第二轮指定四项已关闭，但新增反例 `Status: done` + `Current: in progress` 仍无 conflict，S1-A/D/E 通过，S1-B/C 未全部通过。按两轮上限停止并保留候选，不弱化标准、不启动 S2。
- 收口回归：machine-port 38/38、Area Overlay 25/25 通过；Map v0 8/10，通过失败的两个真实任务视图都因新增状态节点挤掉 `code://.specmesh/context.md`。缓存仍可 build/check 为 fresh、两个 Area current，但检索回归未关闭。

## Remaining

无本轮必做剩余项。

| 单元 | 状态 | 证据 |
|---|---|---|
| S1 | accepted | evidence/SM-P0.S1/acceptance.md |
| S2 | accepted | evidence/SM-P1.S2/acceptance.md |
| S3 | accepted | evidence/SM-P4.S3/acceptance.md |
| R1 | accepted | evidence/SM-P0.R1/acceptance.md |

CM接轨已退出范围，非完成；Map v1及更广provider/device矩阵仅可选未来需求，不影响本轮4/4。

## Issues

无当前阻断项。限制：声明POSIX/Python3.11/3.12 profile，完整性校验不是来源签名；回退演练基线为本任务rc1候选，不宣称正式v1.2.1升级覆盖。历史错误及检查局限保留在各卡证据，累计完整费用unknown。

## Next

无；完成文档收口，不自动启动下一任务或CM接轨。

## 本轮自查

独立只读审查后修正：S1 允许既有受控 Git plumbing；默认主工作区并保留既有直接 push 授权；真实 provider 的产品验证限制与已配置 CBC/AGY 实现/审查角色分开；旧 progress 顶部补历史指针。没有启动任务。

已核对 8 个文档（新建三件套，更新 5 个入口/决定文件）：60 个本地链接均可解析，`git diff --check` 通过；单卡状态与 0/4 口径一致。`SPEC.md` SHA-256 仍为 `5ba5820f1d6ab67b6977520dd0cb2be6e02bbe7b45ce077de1eb35743f8d80ca`，产品代码及规范未改。未提交、推送、发布或安装；这不是 S1 产品验收。

主助手按本仓 AGENTS 补跑文档输入相关验证：`python3 -B -m unittest discover -s tests -p 'test_map_v0.py'` 的 10 项通过；`test_area_overlay.py` 的 25 项通过，均 exit 0。没有运行 machine-port 全套或真实 provider。map_v0.py build/check 已通过并返回 fresh；本条记录写入后再生成最终指纹并检查，派生缓存保持 ignored。该检查只证明当前文档索引新鲜，不增加产品验收分子。

一次文档检查器误要求每个 findings 文件都重复出现 Ops，触发检查器断言；这不是项目缺陷。改为检查任务主计划的范围边界，避免为满足机械校验重复写文档。

本轮第一次更新进度的组合补丁因上下文匹配失败而未应用；未产生部分写入。拆成精确小块后成功，产品实现未受影响。

失败收口的第一次组合补丁也因 task_plan 末段上下文少一个空格而整批未应用；拆分后成功，没有部分写入或产品影响。
