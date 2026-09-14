# SpecMesh 独立可用版：有界交付计划

> 2026-09-15 用户范围决定：独立发展是长期方向，不是 CM 接轨前的临时排序。CM lifecycle、等义适配与三仓对齐退出必做范围；可选适配不自动列入后续任务。S2 → S3 → R1 独立验收及原计数不变。

> 当前：S1/S2/S3 accepted，整体3/4。S2累计第5次实现后独立107/107通过，见[acceptance](evidence/SM-P1.S2/acceptance.md)。
> S3已独立接受；R1正在准备v1.3.0，正式发行尚未进行。
> [当前接手证据](evidence/SM-P1.S2/attempt-4.md)；[此前拒绝记录](evidence/SM-P1.S2/review-3.md)。
> [S1 独立验收](evidence/SM-P0.S1/acceptance.md)；[S2 派发任务卡](evidence/SM-P1.S2/dispatch-agy.md)。

## 状态与唯一下一步

S1累计尝试3、S2累计实现尝试5且已独立接受；S3全新AGY B调用1次、修正0、独立接受。整体3/4，见各卡acceptance.md。下一步完成R1精确源码、CI、发行工件、安装/回退及独立验收。

用户“完成到4/4”并要求继续，覆盖旧规划阶段的“不启动/不提交发布”暂停措辞；按原四卡范围串行实施，不改SPEC或全局标准链接，不扩大到CM/History。旧失败、平台拦截和次数均保留，不靠重命名重置。

## 目标、背景与边界

交付一个无需 CM/History 的项目连续性版本：读出当前项目状态，生成绑定完整 HEAD 与明确 dirty 范围的交接材料，让全新 Agent B 只接手被授权的下一步，产出经独立验收接受的结果，随后独立发行。通用开发流程在这里是“意图 → 计划 → 执行交接 → 验证 → 收尾”的输入输出与责任合同，不是另建执行运行时。

复用现有 `SpecMeshService`、严格 contracts、descriptor snapshot 和有界 Git reader。保留规范 v1.1.0、机器协议 `specmesh.port.v1-draft`、`specmesh.snapshot.v1` 的既有含义；本计划不是已发布规范。当前实现入口和证据见 [findings](findings.md)，产品边界见 [架构](../../docs/ARCHITECTURE.md) 与 [机器接口](../../docs/CODEKIT-INTEGRATION.md)。

当前不做：CM 宿主/TaskHub/调度、provider 管理、多设备接管、全量历史索引、Map v1、大型看板、第四个总平台。CM 可选适配继续保留，但不得反向成为独立读取、交接、验收或发行的前置依赖。不开启真实模型演示，不改 `SPEC.md` 或全局标准符号链接，不提交、推送、发布或安装。

## 旧任务映射与冻结计数

原 [independent-plugin-port](../independent-plugin-port/task_plan.md) 的 SM-P0、SM-P1 窄技术出口已由 2026-09-13 审计确认；它们仍是已验收复用基线。SM-P0 通过不表示完整插件产品已交付；SM-P1 限已声明 POSIX snapshot profile。旧五阶段审计为 2/5，本计划不改变该历史分母，也不重复计算父项与子项。

本次冻结 **4 个互不替代的增量验收单元**，当前 **3/4 已验收**。它是本仓独立可用版的关闭率，不是实现工作量比例；不用跨仓旧总百分比。只有对应卡全部出口及独立审查通过才计 1，partial/unknown/fail 不折算。若拆卡、扩平台或改完成定义，先记录分母变更理由，旧证据不删除、不靠拆分已有成果增加分子。

| 单元 | 沿用关系 | 本次独有出口 | 状态 |
|---|---|---|---|
| SM-P0.S1 | SM-P0 增量；承接 X-01 的独立状态/流程输入 | 人与机器能独立读出带来源的当前状态、完成标准、阻塞和下一步 | accepted，1/1；见独立验收证据 |
| SM-P1.S2 | SM-P1 增量；承接 SM-P3 的基线与证据责任 | dirty 交接、失败/未知记录、证据与源基线绑定，并能拒绝过期交接 | accepted；见S2 acceptance.md |
| SM-P4.S3 | SM-P4 的独立新会话子项；验证 SM-P3 | 真正全新 B 完成一个预先固定的实际任务并获独立接受；过期/取消不执行 | accepted；见S3 acceptance.md |
| SM-P0.R1 | SM-P0 的独立发行子项；承接 X-02 的 SpecMesh 部分 | 精确源码、检查、发行工件、干净安装和本机实际入口可对账 | 本地候选/解包验证已准备；发行验收依赖 S3 |

2026-09-15 范围变更：旧 SM-P2 的 CM lifecycle、X-01 的 CM 等义适配、X-02 的三仓组合对齐退出 SpecMesh 必做范围，不记作已完成。SM-P3 的独立权威边界及 SM-P4 的真实交接要求承接至 S2/S3；更广信任模型和完整 provider/device 矩阵为可选扩展，不自动执行。四单元分母不变；退出CM范围不增加验收分子。外部集成仅在用户另行提出真实需求后规划，不以 Orca 替换 CM 成为强制依赖。

## 最小流程合同（待实现、待验收）

| 步骤 | 输入与输出 | 责任、失败与证据 |
|---|---|---|
| 意图/状态 | 当前入口与显式选定任务 → 项目身份、目标、约束、任务、完成标准、阻塞、下一步 | 已审查文档仍由项目 owner 维护；抽取结果只带来源，不自动变成 reviewed truth；缺失/歧义为 unknown |
| 计划 | 当前任务与可观察完成标准 → 有边界的唯一下一步、写范围和停止条件 | 人/受授权执行者选择任务；项目文本、历史记录和“ready”不能自行授予执行权限 |
| 交接 | 当前文档、显式 dirty 范围和证据 → 完整 HEAD、范围指纹、保留事项、成功/失败/未知、证据基线 | SpecMesh 只生成可检查材料；消费前重新验证；缺失、过期、冲突或取消时不声称可继续 |
| 验证 | 指定任务产物、实际 diff、固定检查 → 对每个标准的 pass/fail/unknown | 验证由有明确身份与范围的独立审查者完成；自报 passed、退出 0、marker recall 都不构成结果验收 |
| 收尾 | 验证记录与 owner 接受决定 → 准确完成/未完成、未验证范围与唯一建议下一步 | 独立证据绑定执行后基线；未知保持开放；不自动取下一张、不恢复取消任务 |

## 每张卡共同执行约束

- 默认在主工作区推进；只有并行写入或受控验证确需隔离时才选择独立临时 repo/worktree。既有直接 push 授权保持有效，不因独立审查而改成一律 PR 或重复审批；本轮仍只规划，不提交推送。后续动作按适用的既有授权及当张卡范围执行，不自动扩展到发布/安装。
- 开始前读取本仓 `AGENTS.md` → `PROJECT.md` → 本卡与相关入口；记录 branch、完整 HEAD、受影响文件 hash、staged/unstaged/untracked 范围及已存在修改。不把新 worktree 当作包含原目录的 dirty 内容。其他执行者可能写同一范围时停止并报告，不覆盖、不清理。
- 一张卡最多一次实现、一次独立审查、至多两轮修正；每轮保留原因、diff 与实际验证。两轮后仍失败、范围越界、协议破坏、认证/额度不可用或未知授权依赖时停止，交付失败/unknown 与复现。压缩上下文、换会话或换执行者不重置额度。
- 实现/审查可复用用户已配置并授权的 CBC、AGY 等执行者，由当次派发选择；不强制新增模型注册/凭据，不静默换模型，不新增递归子代理。本轮不启动任何模型 CLI。S1/S2/R1 的“产品验证不调用真实 provider”不禁止这些已授权执行者参与实现/审查；S3 的真实产品演示在单独派发时固定模型/provider、次数与可执行预算。读不到费用/token 时记录 unknown；提示词不是硬限额。
- 验收记录按单元保存到 `plans/bounded-delivery/evidence/<ID>/`，只存必要的脱敏证据。至少含：输入版本、source SHA、验证前后范围指纹、dirty diff、环境/命令/退出码、逐项结果、审查者身份/范围、失败尝试、费用或 unknown。大日志/运行库不进仓；不得读取真实凭据或全量私人历史。
- 验收只选择与本卡相关的回归；已有窄通过证据先复用，因本卡改变行为才重验受影响项。真实 provider、synthetic、静态检查、历史证据分开。改了证据依赖文件则该证据过期；原始记录保留。
- 每次结束更新本计划状态及 [progress](progress.md)，输出交付行为、基线/产物、验收、未验证项、消耗、唯一下一步并退出。不自动发布、不建立后台任务、不切换其他仓库主线。

## 下一张可直接分发的详细任务卡

### SM-P0.S1：独立状态读取（accepted）

**可观察行为。** 在不安装、不启动 CM/History、不访问 native 历史库的环境里，显式指定受控 repo 与 task，得到内容一致的人可读状态和 JSON 状态：项目是谁、当前做什么、完成标准是什么、阻塞/证据/下一步在哪里。缺项或冲突显示 unknown/ambiguous；引用绑定当前内容，不能把结构 check 的 pass 展示成项目任务已完成。

**规划基线。** `main`，`d393c548a2a58989d65e6cdbd60a36e9a81a444f`；规划开始前工作区 clean。本轮新增文档属于应保留的后续 dirty 范围；派发时重新记录实际 HEAD 和 diff，不 reset 到这个 SHA。

**现有入口。**

- [service.py](../../specmesh_port/service.py)：`_select`、`check`；目前只给文档引用/hash 与结构 findings，尚无完整语义状态读模型。
- [snapshot.py](../../specmesh_port/snapshot.py)、[git_reader.py](../../specmesh_port/git_reader.py)：复用已通过的有界观察，解析与 hash 必须使用同一次读取的字节，输出前同样重验。
- [__main__.py](../../specmesh_port/__main__.py)、[contracts_runtime.py](../../specmesh_port/contracts_runtime.py)、[contracts](../../specmesh_port/contracts/)：CLI、严格 schema 及有限输入输出。
- [test_machine_port.py](../../tests/test_machine_port.py)：复用 standalone、readonly、dirty/stale、特殊文件、超时和 unknown-closeout 回归。

**允许写范围。** `specmesh_port/` 中与状态读取直接相关的模块和一个独立状态输出 schema；`tests/test_machine_port.py` 及必要的状态 fixture/测试文件；`docs/CODEKIT-INTEGRATION.md`、本计划三文件和本卡 evidence。实现者拥有新增状态 schema；旧 CM 已镜像的 request/result/capabilities schema 不得在本卡破坏性修改。若无法兼容则停止报告，不越仓修 adapter。不得改 `SPEC.md`、Map/Area、CM/History、全局配置或发布安装文件。

**实现步骤与兼容出口。**

1. 增量检查当前是否已有等效输出；若已有只补证据。保留默认 CLI JSON、既有操作与退出码。状态视图使用显式 opt-in 输出入口；可选择独立格式参数，具体拼写由本卡实现时记录，本文不声称新命令已存在。
2. 在本仓独立定义版本化状态读模型；作为单独输出合同，不把新增字段塞进旧 strict result 后要求 CM 同时升级。它复用旧 request 的 repo/HEAD/task 范围，不扩大读权限。
3. 最小内容固定为：项目身份、选定任务与目标/约束、完成标准、完整 observed HEAD、选中文档指纹与明确 coverage、阻塞、声明状态、证据引用、唯一下一步或 unknown。每项附相对源路径、原始位置与 SHA-256；缺失、重名、未支持格式不能自行猜测。
4. 优先按已有 Markdown 标题和显式字段做有限抽取，记录支持的标题/格式；保留原句与来源。`task_path` 不明确时要求显式选择或给出 unknown/ambiguous，不能扫描所有历史计划后随意选一个。临时状态视图不是新权威数据库。
5. JSON 与人类文本由同一模型渲染。区分 asserted candidate、观察到的文件/基线事实、尚未验证的 evidence 引用；过去“done/pass”仅作原文声明。fresh 只表示声明 coverage 内观察有效，不能把未观察的全工作区称 clean。

**冻结验收清单（全部满足才关闭 S1）。**

| 检查 | 必须观察到的结果 |
|---|---|
| S1-A 独立调用 | 临时目录/精简环境无 CM/History 进程或依赖；同一显式 repo/task 完成人类和 JSON 状态输出；JSON 可按本仓 schema 验证 |
| S1-B 最小完整状态 | 固定受控 fixture 的身份、任务、目标/约束、完成标准、HEAD/coverage、阻塞、证据和下一步均可定位到当前源；两种呈现含义一致 |
| S1-C 不足与冲突 | 缺字段、两个候选 active task、互相冲突的状态、缺证据、明确失败记录可见；unknown/ambiguous/fail 不成为项目“已完成” |
| S1-D 基线与只读 | 同 HEAD 改内容、读取中修改、旧 expected HEAD、缺失源得到 fresh hash 或 stale/blocked 的正确区别；仓库前后字节/状态无写入。产品只读路径可调用既有受控 Git plumbing，禁止执行项目文本提供的命令、真实 provider、非授权执行或网络 |
| S1-E 兼容 | 旧默认 CLI 请求/结果/能力 schema 与退出码不变；相关 snapshot、安全限制、unknown-closeout 回归通过；默认使用者无需 CM 配套改动 |
| S1-F 审查与收口 | 独立审查者按 A–E 和实际 diff/证据作接受或拒绝；保留失败尝试、支持格式/平台与未观察范围，更新状态后退出 |

**验证方式与证据。** 使用合成的受控 Git fixture，至少含规范标题完整项目、缺失/冲突项目、同 HEAD dirty 修改、明确失败仍留有旧 done 声明四组；不执行项目 Markdown 中命令。把精确命令、stdin、必要 stdout/stderr、退出码、环境和结果保存为本卡 evidence。现有测试入口是 `python3 -B -m unittest discover -s tests -p 'test_machine_port.py'`；新测试文件若使用不同名称须记录实际运行入口。不为 S1 重跑不相关全套，不把“57 tests”当新状态语义证明。

**权限、预算与停止。** 2026-09-14 已由用户正式派发；沿用当前受控环境，产品验证无需真实 provider。一次实现、一次独立审查、至多两轮修正；费用未知写 unknown。发现需要通用 Markdown 语义推理服务、跨仓 schema 修改、全工作区扫描、权限扩大、既有用户修改归属不明或两轮后仍失败，保留结果并停止。不得为了满足验收删除失败 fixture、弱化预期或把 unresolved 当 pass。

**停止后的唯一建议。** S1 已独立接受；由用户明确派发 S2 后再执行。本卡的第 3 次定点续修由用户另行授权并已完成，旧两轮上限与失败记录保留，不重置累计次数，不自动开启第四次修正。

## 后续批次（排队，派发前只细化当张卡）

### SM-P1.S2：绑定 dirty 基线的独立交接（candidate ready for review）

**可观察行为。** 从 S1 状态生成可独立消费交接材料，包含目标/约束/决定、完成/失败/未知、剩余工作、唯一下一步、完整 HEAD、显式覆盖的 staged/unstaged/untracked 内容、范围指纹以及每份证据对应的基线。未覆盖范围明确 unknown；不以 HEAD 相同推定 fresh，不默认打包整个仓库或凭据。dirty 内容保留或能定位原件，不假设新 worktree 自动包含。消费前检测过期、同 HEAD 内容变化、覆盖遗漏、缺源、缺证据或 cancelled，拒绝可执行状态。

**规划基线。** `main`，`d393c548a2a58989d65e6cdbd60a36e9a81a444f`；进入时 dirty 清单与文件 SHA 见本卡证据。保留所有已有改动，不 reset/stash/清理。

**现有入口与复用。**
- `SpecMeshService.prepare_handoff`、`SpecMeshService.verify_handoff`：交接生成与消费前验证。
- `snapshot.py`、`git_reader.py`：安全 POSIX 文件快照与受限 Git plumbing (`ls-files`, `ls-tree`, `rev-parse`)。
- `specmesh_port/handoff.py`、`contracts/specmesh-handoff.schema.json`：`specmesh.handoff.v1` 独立读写模型与契约。
- `specmesh_port/__main__.py`：CLI opt-in `--handoff json|text` 与 `--verify-handoff <file>|-`。
- `tests/test_handoff.py`：受控测试覆盖 clean、staged+unstaged、untracked、同 HEAD 篡改、旧 HEAD、缺源/缺证据、失败冲突与取消。

**允许写范围。** `specmesh_port/handoff.py`、`specmesh_port/contracts/specmesh-handoff.schema.json`、`specmesh_port/service.py`、`specmesh_port/__main__.py`、`tests/test_handoff.py`、`docs/CODEKIT-INTEGRATION.md`、本计划三件套与 `plans/bounded-delivery/evidence/SM-P1.S2/`。不得改 `SPEC.md`、Map/Area 实现、History/ControlMesh、全局配置、凭据或发布安装文件。

**实现步骤与兼容出口。**
1. 独立定义 `specmesh.handoff.v1` schema，不修改原有 strict `specmesh-result` 或 CM 镜像契约。
2. 提取项目目标、约束、决策、完成/失败/未知、剩余工作、唯一下一步，严格绑定相对源码位置与 SHA-256。
3. 显式扫描并区分 staged、unstaged、staged_and_unstaged 与 untracked 文件，记录当前 worktree SHA-256、locator 并在文本边界内保留 content。
4. 计算基于 HEAD、覆盖文档、dirty 清单与证据绑定的确定性 `scope_fingerprint`。
5. 提供 `verify_handoff` 消费前门禁与 `--verify-handoff` CLI，若 HEAD 不符、内容变化、dirty 遗漏、缺证据、状态冲突或任务取消，立即拒绝可执行状态 (`executable: false`, exit 3)。
6. 保留旧默认 CLI 行为，无 `--handoff` 时仍返回既有 `specmesh-result`。

**冻结验收清单（全部满足才关闭 S2）。**

| 检查 | 必须观察到的结果 |
|---|---|
| S2-A 独立调用与合同 | 独立版本化交接 schema (`specmesh.handoff.v1`) 与文本渲染；JSON 契约验证通过；CLI opt-in `--handoff json\|text`；旧默认 CLI 与严格 schema 保持兼容；不将交接材料当权限签发或自动执行器 |
| S2-B 最小完整交接 | 目标、约束、决定、完成/失败/未知、剩余工作、唯一下一步、完整 HEAD、范围指纹、证据基线均绑定来源与 SHA；未覆盖范围明确 unknown |
| S2-C Dirty 覆盖与保留 | 显式区分 clean、staged、unstaged、staged+unstaged、相关 untracked；保存 dirty 内容与定位原件 (locator)，不假定新 worktree 自动包含；计算 scope_fingerprint |
| S2-D 消费前前置检测 | `--verify-handoff` 检测过期 (stale HEAD / stale source sha)、同 HEAD 内容变化、覆盖遗漏 (dirty 缺失)、缺源、缺证据、状态冲突或 cancelled，拒绝可执行状态 (`executable: false`, exit 3) |
| S2-E 兼容与只读回归 | 旧默认 CLI 请求/结果/能力与退出码不变；S1 project-state 模型无破坏；只读 plumb Git，不覆盖项目源，不调用真实 provider / 网络；全套测试 89/89 通过 |
| S2-F 审查与收口 | 独立审查者按 S2-A～E 和实际 diff/证据作接受或拒绝；保留失败尝试、未观察范围，更新状态后退出；不自行声称外部接受或改变 1/4 计数 |

**验证方式与证据。** 使用合成的受控 Git fixture，测试入口为 `PYTHONPATH=tests python3 -B -m unittest test_map_v0 test_machine_port test_area_overlay test_handoff -v`（89/89 通过）。所有命令、退出码、真实失败复现、进入前后 diff 及文件指纹保存于 `plans/bounded-delivery/evidence/SM-P1.S2/`。

**权限、预算与停止。** 2026-09-14 用户已授权 AGY 执行；一次实现、一次独立审查、至多两轮修正；保持配置模型，不改账号/凭据，不新建子代理。调用结束交付候选和验证后停止，唯一建议下一步交回独立审查，不自动开始 S3。

### SM-P4.S3：全新 Agent B 完成被验收的实际下一步

- 行为：在本仓或另一个明确受控的真实项目内，预先固定一个有实际用途的小任务及独立完成标准；A 留下未完成任务与应保留 dirty 修改，B 从全新空白会话仅凭项目入口、S2 交接和本次授权完成指定下一步。不得用只改 marker 的演示替代实际产物。
- 入口/写范围：使用已验收 S1/S2 公共入口；默认主工作区，只有受控测试确需保护现有状态时采用独立临时 repo/worktree，事前固定任务文件和独占边界；验收记录只写本卡 evidence 与状态。无论选择何种目录，必须真实保留并核验 A 的 dirty 情境，不能假定新目录已含它；禁止复用真实用户会话库、原生 resume、fork 完整 A 历史或转交隐藏上下文。
- 验收：先运行确定性的交接/冲突测试；真实演示中 B 的新会话身份与输入清单可核对，能指出约束/剩余工作，保留 A 修改，用实际 diff 和预先固定的测试证明任务完成，独立 reviewer/owner 明确接受。第二个受控场景中 stale 或 cancelled 输入阻止执行；不得将失败测试因旧“done”记录而跳过。
- 证据：A/B 不同 session identity、B 实际获准输入、任务标准冻结记录、原有 dirty hash、执行前后 diff/检查、拒绝场景和 owner 接受。same-session read/reopen、原生 recall、fake/synthetic 推理只作历史辅助，不算本出口。
- 预算/停止：派发前明确允许的 provider/model、费用/token 上限或可支持的单次调用限额；无法确认则不启动真实调用。至多 A 准备一次、B 执行一次、独立审查一次，加全卡最多两轮修正；记录实际调用和费用或 unknown。遇认证/额度、超范围写入、证据缺失或达到上限即停止，不自动重开；通过后只建议 R1。

### SM-P0.R1：独立发行与本机可用性对账

- 行为：把通过 S1–S3 的范围作为独立 SpecMesh 工件发行；用户在无 CM/History 的已声明环境可安装/解包并执行状态与交接入口，版本与源码可以核对。正式支持范围先固定 Python 3.11/3.12 与现有 POSIX profile，Markdown 的平台边界保持原义；不承诺未验收平台。
- 入口/写范围：本仓 README、接口说明、必要打包文件、`.github/workflows/`、发布清单和本计划；只在实际派发明确覆盖的独立安装目录做验证。选择最小一种可分发方式，不为插件宿主增加 CM 依赖；标准正文/全局 symlink 变更须另有明确范围，不能随安装覆盖。
- 验收：功能 → 完整 source SHA/dirty 清单 → 该 SHA 必需检查 → tag/Release/工件 hash → 干净安装与实际入口模块位置/版本 → S1/S2 smoke 全链可核对；升级/撤回演练保留原项目记忆与 dirty 数据。仅上传源码、CI 绿、符号链接同字节分别不足以证明安装与运行通过。
- 证据：构建/安装/命令/工件 digest、发布 provenance、已选支持范围与回退结果；只有实际获得覆盖发布/安装的派发授权后才做外部动作。停止：身份不一致、必需检查失败、安装覆盖用户内容或需改变规范时先保留工件并报告；至多两轮修正，不自动接 CM/History/Ops 后续批次。

## 变更与回退

2026-09-14 将活动方向从先补 CM 集成改为先独立可用版；不撤销历史功能或其通过证据。若任一卡发现已通过基线存在反例，记录受影响条件与重验范围；不重写旧证据成“从未通过”。实施回退以当次 diff/隔离工件为单位，保留未提交资料、失败记录和旧安装；禁止 reset --hard、全局 stash/pop 或清理 untracked。

本轮执行收口：SM-P0.S1 完成一次实现、三次独立审查（初审、两轮修正后的复验）和两轮修正；最终因 S1-C 仍有反例而停止，证据保留在 `evidence/SM-P0.S1/`。本轮不运行真实 provider，不改规范正文，不提交、推送、发布或安装；当前没有可自动执行的下一张卡。

## 所有 SpecMesh 计划对账 — 2026-09-15

| 原计划/出口 | 当前实际结果 | 剩余项 |
|---|---|---|
| map-v0-spike | 已完成/历史发布；本次13项Map回归通过 | Map v1是未批准的未来候选，不作为已承诺实现 |
| area-overlay-v0 | 已完成/历史发布，adopt/adapt/reject已落地；本次25项通过 | 无v0遗留项 |
| codekit-integration | 旧v1.2.0实现已交付，当前窄兼容回归通过 | 旧说明由当前接口文档替代，不另算新进度 |
| release-alignment | 旧v1.2.1发行对齐为历史完成 | 新runtime发行统一归R1 |
| independent-plugin-port SM-P0/P1 | 原独立接口/声明POSIX快照窄验收完成 | 不用父项重复增加4单元分子 |
| SM-P1.S2 | 主助手本地修复，23项handoff通过 | 独立审查调用未完成 |
| SM-P4.S3 | 既有单次真实B范围已授权 | S2接受后运行，不以smoke子进程替代 |
| SM-P0.R1 | 1.3.0rc1候选ZIP、文件hash、双Python解包自检完成 | 精确提交CI、正式发行、长期安装/升级撤回 |
| 旧SM-P2 / X-01 CM部分 / X-02三仓部分 | 2026-09-15 按用户决定退出范围，非完成 | 不再要求CM接轨、外仓同步或组合发行；历史证据保留 |
| 旧SM-P3/SM-P4独立部分 | 权威边界与真实交接仍由S2/S3验收 | 当前独立审查阻塞不因移除CM要求而解除 |
| 更广信任模型 / 完整provider-device矩阵 | 可选扩展，非当前必做 | 不宣称已经验证，不自动启动 |

因此“所有进度”已逐项对账，但尚未全部验收完成。平台拒绝的动作是独立审查调用，
不是产品代码测试；未换模型/渠道绕过拦截，未恢复AGY实现。完整累计token/费用unknown。
