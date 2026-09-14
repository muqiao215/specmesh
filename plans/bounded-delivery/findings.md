# Findings

## 4/4 请求后的阻塞复核 — 2026-09-15

实时 agent inventory 返回 `/root/s1_independent_review` 为 errored，原因仍为 `This content was flagged for possible cybersecurity risk`，不是运行中或验收通过。未启动替代审查调用。当前HEAD为d393c548a2a58989d65e6cdbd60a36e9a81a444f，handoff/service/CLI/handoff tests的SHA与attempt-4最终记录一致。`python3 -B -m unittest discover -s tests`：104/104，10.808秒，exit0。只记录本地回归证据，S2-F及其下游仍未满足；累计S1尝试3、S2实现尝试4，本轮新增实现/AGY调用0，费用unknown。

## 独立产品方向确认 — 2026-09-15

用户参考“Orca与CM区别”讨论，明确 SpecMesh 今后单独发展、不用与 CM 接轨。讨论里的 CM/Orca 桥接建议不是本项目实施指令；不新增 Orca 依赖，不改 CM/History 仓库。长期决定见 [DECISIONS](../../docs/DECISIONS.md)。

CM lifecycle、CM 等义适配和三仓组合从必做范围退出，而非测试通过。旧失败、次数和历史结果保留；S2 独立验收、S3 真实交接、R1 发行仍是当前出口。下文历史“仍开放”的 CM 待办由本次范围决定覆盖。

## S2 最后一次修正的当前观察 — 2026-09-15

- 原 AGY 会话第 2 次修正于 02:44 超过 30 分钟并关闭服务；原 db/lock 无进程持有，其他 AGY 进程不属于这次打印调用。未为超时重启会话。
- 当前 service.py 给 build_handoff 传 snapshot，但函数签名未接受它，且调用已在 snapshot 的 with 生命周期之外。93 项回归中原 78 项通过，handoff 14 error + CLI 1 failure。
- schema 已要求 baseline.coverage，但原 builder 仍不输出该字段。handoff.py 与 tests/test_handoff.py 均与 review-2 的 SHA 相同；不能把 CLI/schema 的局部改动当作核心修复完成。
- snapshot 的路径数上限被从 64 改为 256；CLI stdin 增加 1 MiB 上限，但文件分支仍在 stat 后普通 read_bytes。这些都是未验收的末轮局部改动。
- 原始输出与当前 S2 范围累计候选分别见 [tests](evidence/SM-P1.S2/correction-2-tests.log)、[patch](evidence/SM-P1.S2/correction-2-candidate.patch)。patch 相对 HEAD；其中 service/CLI 包含已存在的 S1 增量，不冒称仅第 2 轮 diff。
- S1 累计尝试仍 3、已接受；S2 一次实现 + 两次修正调用（末轮超时未完成）。原审查者最终拒绝，独立复现语义自签、dirty范围泄露和101项遗漏，见 [review-3](evidence/SM-P1.S2/review-3.md)。当前及累计完整 token/费用 unknown；历史流检查点另外保留，不重复加总。

## S1 独立验收收口 — 2026-09-14

用户“开始 s1”续接原卡的 S1-F，原审查者 `/root/s1_independent_review` 独立接受同一
第 3 次修复候选，A–F 通过，78/78 回归通过。实现 hash 未变；本次仅更新文档状态。
真实仓 JSON/text 仍可因保留历史状态词而 ambiguous，这是有限抽取的保守输出，不能用
接口已验收推导项目声明一致。累计尝试 3，费用/token unknown；完整证据见
[acceptance](evidence/SM-P0.S1/acceptance.md)。以下记录保留各自发生时的状态。

> 第 3 次续修发现：状态链首个错误在聚合条件（已解析/规范化的 done + in_progress 未比较）；
> Map 独立错误在 focus 预算选点（configured_by 目标存在且未门控，但被符号密度挤出）。
> 两条路径不互相生成输入。一次补丁已通过相关验证，来源诊断、枚举、真实任务声明未改。
> 完整复现和前后证据：[attempt-3](evidence/SM-P0.S1/attempt-3.md)。

## SM-P1.S2 候选实现发现 — 2026-09-14

- 用户授权 AGY 派发实施 S2。S2 核心是可消费交接生成、显式 dirty 基线保留与消费前前置拒绝门禁。
- 契约设计：新建 `specmesh-handoff.schema.json` (`specmesh.handoff.v1`)，保持独立，不更改 CM 镜像契约或原有 `specmesh-result`。CLI 采用显式 opt-in `--handoff json|text` 与 `--verify-handoff <file>|-`。
- Dirty 显式覆盖：使用只读 Git plumbing (`ls-files --stage`, `ls-tree -r HEAD`, `ls-files --modified`, `ls-files --others --exclude-standard`) 精确区分 staged、unstaged、staged_and_unstaged 与 untracked，计算文件 sha256、locator 并内联保留文本内容。
- 确定性范围指纹：`scope_fingerprint` 基于 HEAD、文档 coverage、dirty 列表及证据绑定联合哈希，任一处变动均导致指纹不一致。
- 消费前前置检测 (`verify_handoff`)：不能假设下游或新 worktree 自动包含未提交修改。消费前核验工作区文件哈希、HEAD、证据状态、取消声明与唯一步骤，若 dirty 缺失或内容改变则拒绝执行 (`executable: false`, exit 3)。
- 兼容性：旧默认 CLI、退出码与 `--project-state` 保持完全兼容；回归测试扩展至 89/89（新增 11 项针对性回归全部通过）。

## 输入与权威顺序

2026-09-14 的用户方向：三个既有仓库分别规划；SpecMesh 第一、History 第二、ControlMesh 第三，Ops 暂不管。不使用 Goal，不实施代码，不自动进入下一批。该方向优先于旧跨仓执行顺序。本文记录事实与旧假设，不授予执行权限。

- [下载附件：THREE_PROJECTS_BOUNDED_DELIVERY.md](/home/muqiao/下载/THREE_PROJECTS_BOUNDED_DELIVERY.md)：2026-09-13 的有限交付建议；SHA-256 `fe885b85d69836ecc728204edb810e0ea20b2f2c47bd05e458a8780e276e339c`。
- [最终要求审计，2026-09-13](/home/muqiao/Documents/Codex/2026-09-06/new-chat/outputs/runtime-convergence/final-requirements-audit-20260913.md)：SHA-256 `f946813661876235569923f8abc4397511cbe422b509a0f80e5e5ad87350a85e`。使用其中 SpecMesh、X-01/X-02、版本与证据边界；不把旧跨仓总比例带入本计划。
- [原机器接口主计划](../independent-plugin-port/task_plan.md)、[原进度及原生 canary](../independent-plugin-port/progress.md)、[原发现](../independent-plugin-port/findings.md) 保留完整历史证据。

外部本机文档链接仅用于追溯，其他机器可能没有同一路径；当前计划的目标、出口、范围及证据摘要已在本仓三文件中写全，独立接手不依赖下载目录、历史库或 CM 可用。

## 本次直接核对

| 项目 | 本次观察 |
|---|---|
| 仓库 | `/home/muqiao/桌面/obsidian/my-programming-world/编程/SpecMesh` |
| branch / HEAD | `main` / `d393c548a2a58989d65e6cdbd60a36e9a81a444f` |
| 工作区 | 规划写入前 `git status --short` 无输出；本轮只按已分配独占范围修改本仓文档 |
| 规范 | `SPEC.md` SHA-256 `5ba5820f1d6ab67b6977520dd0cb2be6e02bbe7b45ce077de1eb35743f8d80ca`；不改规范正文或全局链接 |
| 实际入口 | [`__main__.py`](../../specmesh_port/__main__.py) 暴露 capabilities 与 bounded JSON；四个 request 操作是 inspect/check/prepare_handoff/verify_closeout |
| 状态差距 | [`service.py`](../../specmesh_port/service.py) `_select` 与 `check` 已读取入口、架构/决策、显式 task 三文件并返回引用/hash；没有完整的人/机器项目状态读模型。inspect/prepare_handoff 目前沿用相同结构检查结果 |
| 复用边界 | [`snapshot.py`](../../specmesh_port/snapshot.py)、[`git_reader.py`](../../specmesh_port/git_reader.py) 提供 descriptor 内容/身份重验和有界、禁 transport/filter 的 Git plumbing；本轮不重写 |

## SM-P0.S1 派发基线 — 2026-09-14

- 用户已明确要求按更新计划完成任务，因此 SM-P0.S1 从 ready 进入 in progress；该授权不扩展到 S2、S3、R1、提交、推送、发布或安装。
- 实现前仍为 `main` / `d393c548a2a58989d65e6cdbd60a36e9a81a444f`。已有 dirty 仅含规划产生的 `PROJECT.md`、`docs/DECISIONS.md`、计划索引、旧计划承接指针和新 `plans/bounded-delivery/`，没有产品代码修改。
- S1 允许写范围固定为 `specmesh_port/` 的状态读取模块与独立 schema、`tests/test_machine_port.py` 及必要 fixture、`docs/CODEKIT-INTEGRATION.md`、本计划与 `evidence/SM-P0.S1/`。保留并绕开现有规划修改，不 reset/stash/覆盖。

## SM-P0.S1 实现发现 — 2026-09-14

- 旧 `check` 只返回结构 findings/references。新状态输出必须是独立 schema，不能向 CM 已镜像的 strict `specmesh-result` 塞字段；因此采用显式 `--project-state json|text`，输入仍复用受控 request，默认路径不变。
- 简单 H2 模板不足以读取本仓真实活动计划：S1 验收表位于 H3 下的加粗标签。有限抽取器因此支持 H2/H3 与已记录的加粗字段标签，并保留验收表数据行、跳过表头/分隔线；真实仓试跑准确得到 S1-A～S1-F。
- `observed` 只表示声明范围内输入在完整 HEAD、Git metadata 和 descriptor snapshot 上稳定；它不是 complete/pass，也不表示全工作区 clean。dirty 当前字节可被可靠观察并以 `modified: true` 暴露；expected HEAD 不符或读取中变化才 blocked。
- 未显式给 `task_path` 时不自动选择 PROJECT 链接。零/一个候选均 unknown 并要求显式选择，多个候选为 ambiguous；旧 done 与 failure/unknown 共存也为 ambiguous，不推断完成。

## SM-P0.S1 独立审查与第 1 轮修正

独立审查者首次拒绝实现，实证六个语义/呈现反例：`Done` 错作 evidence、代码围栏内标题可伪造状态、text 透传终端控制符、text 缺身份来源与 statement authority、缺 blocker 字段仍 observed、合法 4097 字符或超 200 条输入在最终 schema 验证处逃逸为 request_rejected。Git 新鲜度和旧 CLI 兼容本轮未发现问题。

第 1 轮修正保持模型边界而非放宽 schema：`Done` 只作为声明展示；Evidence/Verification 才满足证据字段；围栏内容完全不参加标题、字段和任务链接发现；text 对所有动态 C0/C1 字符做可见转义并显示身份 source 与声明 authority；空 Issues/Blockers 标题表示已明确无阻塞，标题缺失则 unknown；超限声明返回有效 schema + unknown 和明确 issue。六类反例均进入 `tests/test_machine_port.py`，修正后 35/35 通过，交回同一独立审查者复验。

第二次独立复验拒绝三个剩余边界：历史 Done 污染 Current、带 info string 的伪 closing fence 与缩进代码绕过、51 task candidates 超 schema。第 2 轮将 Done 分离到只展示的 `history`，严格要求 closing fence 尾部仅空白、忽略四空格/Tab 缩进代码，并在 schema 前把 candidates 有界到 50；38/38 通过，真实仓 JSON/text 恢复 `observed`。

最终独立复验确认上述指定边界关闭，但发现两个当前来源本身的互斥状态仍可能漏判：`task_plan ## Status: done` 与 `progress ## Current: in progress` 同时出现时，当前特判只识别 done 与 failed/unknown，结果错误为 `observed`。这违反 S1-C。两轮修正额度已耗尽，因此 SM-P0.S1 保持未接受、0/4 不变，S2 不得启动；复现与完整审查记录见 [evidence](evidence/SM-P0.S1/README.md)。

本轮未重新访问远端发布/CI、运行模型 CLI 或产品全套。下节的 Release、CI 与 canary 是 2026-09-13 审计/原计划所核对的历史事实，不伪称 9 月 14 日重测。

## 附件旧假设与当前处理

| 附件或旧文档 | 差异与处理 |
|---|---|
| 附件基线只记录 SpecMesh v1.1.0、35 tests | 审计已核对发行 v1.2.1（`5fab9f0f824352ef6d32b72cc8a31050e6499b5f`）；新增 artifact-requirements 在 main `d393c54`，并有当前 SHA 独立 CI。不得据旧基线从零重做 port/快照 |
| S1–S3 是附件逻辑标签 | 落地复用 SM-P0.S1、SM-P1.S2、SM-P4.S3；独立发行用 SM-P0.R1，既有父项和子项不重复计分 |
| 原 SM-P0 状态 planned | 审计确认其 Acceptance 列技术出口已满足；保留 narrow pass，不借此称正式插件/完整流程完成。原表作为旧阶段记录保留，顶部指向新权威状态 |
| 原 progress 的 commits/remote CI remain | 审计核对 main `d393c54` 已远端同步，独立 [CI 34679645905](https://github.com/muqiao215/specmesh/actions/runs/34679645905) 两种 Python 均成功；该待办已过时，新计划不重跑/重复提交来“完成”它 |
| 旧 codekit 计划把 propose_update 列为 CLI operation | 当前 [`CODEKIT-INTEGRATION.md`](../../docs/CODEKIT-INTEGRATION.md) 明确它是独立 Python 方法；本计划只引用实际 CLI 支持，不沿用旧命令假设 |
| 原生两轮 read/reopen 是 Agent 接手成果 | 它是同一原始会话的局部真实读取/回忆证据；不是全新 Agent B、不证明实际任务 diff/独立接受，也不关闭 S3 |
| 审计原推荐先补三仓链路 | 本次方向改为先独立闭环；CM lifecycle 与三仓组合仍保留开放项，但不阻挡本仓 S1–S3 或独立发行 |
| 全局标准和 repo 字节一致 | 审计确认全局文件是指向本仓 SPEC 的符号链接；相同 hash 不能证明独立 executable/plugin 的安装与运行身份 |

## 已通过基线与尚未覆盖的条件

- **SM-P0 narrow pass**：不依赖 CM、独立 CLI、schema fixtures、有界输入输出；审计在 `/tmp`、精简环境、Python `-I -B` 下验证 capabilities 与 prepare_handoff，并核对当前 SHA 独立 CI。依据 [原验收定义](../independent-plugin-port/task_plan.md)、[独立 CLI 回归](../../tests/test_machine_port.py)、[CI](https://github.com/muqiao215/specmesh/actions/runs/34679645905)。S1 增加的是完整状态语义输出，不重新计算这项通过。
- **SM-P1 declared POSIX pass**：dirty content、HEAD/index、原子替换、symlink/FIFO/oversize 与缺失文档变化都在 snapshot 范围内重验；见 [回归](../../tests/test_machine_port.py)、[发布 v1.2.1](https://github.com/muqiao215/specmesh/releases/tag/v1.2.1) 与 [发布记录](../independent-plugin-port/progress.md)。这不是全工作区事务快照，也不证明另一 worktree 有未提交内容。S2 必须说明所覆盖文件及 dirty 交接语义。
- **SM-P2 partial**：CM 可选 adapter、task-start/handoff/unknown-closeout 与三处契约镜像已有证据；CM required lifecycle/外部 closeout 尚未全关闭。原计划留作可选后续，不修改 CM 源码，不纳入独立可用版 4 个单元。
- **SM-P3 partial**：`verify_closeout` 不接受自签 passed 为外部验收，缺少可信 reviewer/evidence identity 全闭环。S2/S3 只建立当前受控独立任务所需的明确证据责任，不宣称通用外部验证器/所有宿主完成。
- **SM-P4 partial**：历史 same-session canary 保留于 [progress](../independent-plugin-port/progress.md)；S3 专验全新 B、真实结果、保留 dirty 与拒绝过期/取消。跨 provider/device 旧矩阵仍不在本轮独立版完成声明内。

## 与最终要求的关系

`X-01` 要求独立通用开发流程、也可内嵌 CM。现有 [SPEC 工作流](../../SPEC.md) 定义文档连续性，不负责模型执行方法；[README](../../README.md) 亦声明不接管开发流程。新方向把可独立使用的最小流程输入/输出/失败/证据责任明确落在 [task_plan](task_plan.md)，随后用 S1–S3 验证；本轮不宣称规范正文已升级。将来 CM 通过相同 versioned contract 适配，执行权仍归宿主，必须有自己的等义验收，不能反向改变文件格式使独立使用失效。

`X-02` 是三仓发布与本机组合对齐。R1 只承接 SpecMesh 的源码→发行→独立安装/入口链，必须准确报告这一范围；不顺带关闭 History、CM 或 Ops。下载附件中较早版本、全局符号链接、单仓 CI 均不能替代这条链。

本仓新分母为 S1/S2/S3/R1 共 4，旧 SM-P0/P1 通过作为依赖事实单列。当前 0/4 不表示从零实现，而表示新增四个可用行为还未验收。本轮文档完成不进入产品分子。

## 限制与待派发时确认

S1 已有本仓代码入口与有限写范围，因此 ready 仅表示可分发；实现未开始。后续卡开始前重新核对 writer/dirty 状态。S3 的真实 provider/model、预算、实际小任务与 owner 必须由当次派发明确固定；本次不选择账号或启动真实会话。R1 发布/安装同样以当次明确授权与已验证工件为边界。

发现命令路径错误一次：首次文件列表包含本仓不存在的 `outputs/`；实际审计位于协调工作区，已按已知绝对路径读取。未因此创建额外平台/输出目录。
