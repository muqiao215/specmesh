# SM-P1.S2 — AGY 派发

## 本次派发运行记录

- AGY conversation ID：`d273fe58-78ea-4a0a-98ce-f8d0721f742b`。
- 调用方进程观察句柄：unified exec session `47145`；后续须核对该句柄，不因等待超时重新启动。
- 已观察到 init、run_command 和读取本派发文件的 view_file 成功事件，不能据此声称 S2 完成。
- 未传 model/agent 覆盖参数；实际模型名未知，费用未知。未使用 skip-permissions。
- 注意：AGY init cwd 是本仓，但其 run_command 初始 pwd 实为 antigravity-cli/scratch；
  后续仓库操作须明确指定本仓绝对路径。AGY 已找到并读取本派发文件。
- S2 与 S3/R1 串行；本记录仅证明派发与开始读取，不构成独立验收。

## 实现派发

用户授权：让 AGY 执行；可并行则并行，否则逐项执行。S2 → S3 → R1 为依赖链，
本次串行派发 S2；不并行写同一源码，不提前执行后续卡的产品演示或发布安装。

你是本卡实现者 AGY。仓库为当前工作目录 SpecMesh，不是 History Viewer。
先读取 AGENTS.md、PROJECT.md、plans/bounded-delivery 三件套，以及 S1 acceptance.md；
然后只读取与 S2 直接相关的 service/snapshot/git_reader/contracts 和测试。

S1 已独立接受，候选仍有未提交修改；累计 S1 尝试 3，原证据必须保留。记录当前 HEAD、
dirty 清单及本卡相关文件进入时 hash，保留所有已有改动，不 reset/stash/清理。

本次落实 plans/bounded-delivery/task_plan.md 中 SM-P1.S2 原有完整范围：

- 生成独立可消费交接材料，包含目标/约束/决定、完成/失败/未知、剩余工作、唯一下一步、
  完整 HEAD、显式 staged/unstaged/untracked 覆盖、范围指纹、证据与来源基线绑定。
- dirty 内容需保留或能定位原件，不能假设新 worktree 自动包含。消费前检测过期、
  同 HEAD 内容变化、覆盖遗漏、缺源、缺证据或 cancelled，拒绝可执行状态。
- 使用独立版本化合同，保留旧默认 CLI / 严格 schemas；不把交接材料当权限签发或自动执行器。
- 受控 fixture 覆盖 clean、staged+unstaged、相关 untracked、同 HEAD 修改、旧 HEAD、
  缺源/缺证据、失败仍留旧 done、取消；真实源码回归和旧 S1 兼容不得降低预期。

先在原计划的 S2 卡冻结上述要求的逐项验收与写范围，再实施一次有界实现。
允许写本包中 S2 相关模块/独立 schema、相关 tests、接口说明、原计划三件套与本目录证据。
不用另建计划/任务重置次数；不得改 SPEC.md、Map/Area 实现、History/ControlMesh、全局配置、
凭据或发布安装文件。只操作受控仓库及必要临时 fixture，不读取私人会话库。

完成实现后运行相关验证并交回独立审查；你不能自己声称外部接受或把 1/4 改为 2/4。
一次实现，审查后至多两轮指定修正；此次调用先交付候选和验证，不自发循环审查或递归代理。
无权新增 Goal、改变模型/账号、启动产品 provider 演示、网络访问、提交、推送、发布、安装或 S3。
这不禁止你当前作为已获授权 AGY 执行者正常进行本次模型会话。

保持原配置模型。若工具权限/认证/额度阻塞，报告具体缺失证据后停止，不跳过权限、不自动重试启动新会话。
成本/token 能读取则记录，不能读取则 unknown，不伪称硬预算；前次记录不删。

交付：实现文件与相对进入时 diff、各项验收的测试/命令/退出码、真实失败输出、候选指纹、
尚未验证范围、唯一下一步（独立审查）和累计本卡尝试。同步原 progress/findings，最后停止。
