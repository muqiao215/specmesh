# SM-P1.S2 第 1 轮指定修正 / 最多 2 轮

用户已要求主动依序推进，收到审查问题后由 AGY 修正再交独立复验，无需重复派发批准。
你继续原 conversation d273fe58-78ea-4a0a-98ce-f8d0721f742b、原 S2 卡，不重命名或重置次数。
仓库绝对路径：/home/muqiao/桌面/obsidian/my-programming-world/编程/SpecMesh。
run_command 初始 cwd 可能是 scratch，所有命令显式 cd 本仓。保持配置模型，不跳过权限。

先读同目录 review-1.md，保留首次候选/测试日志，记录修正前相关文件 hash 和 diff。
将四类反例固化为测试，确认修复前失败；然后实施一轮完整定点修正：

1. 输入严格验证、有界读取；消费时依据可信调用范围重新观察源码/当前取消声明/证据/index/worktree，
   重算并比较覆盖与指纹，不能相信 payload 自报 executable、scope、entries、next_step。
   payload 篡改、同 HEAD source 变化、遗漏、新增相关 dirty、取消、证据删除/修改均拒绝。
2. 同时绑定 HEAD/index/worktree（含 mode/删除等状态），保留 staged 与 unstaged 两份不同版本，
   或提供可验证可恢复的 Git object locator；仅 worktree content 和 None staged SHA 不合格。
3. 显式受控 scope：只读任务文档与调用者明确选定的相关 paths，不默认遍历/打包全仓 untracked。
   未覆盖范围明确 unknown。沿用 descriptor snapshot 的根限制、symlink/特殊文件、文件大小/总量、
   Git输出/时限边界并最终重验，越界/过量 fail closed，不 schema 异常逃逸。
4. evidence 只通过授权根内有界快照读取并绑定其内容/source基线。缺证据或源失效拒绝。
   仓库文字中的 passed/reviewer 仅 asserted candidate，不能凭字符串认定外部验收真实性。

复用 snapshot/git_reader 必要的安全读取。若保存 staged blob 确需增加 Git plumbing，
只允许实现有界只读 blob 获取并配安全回归，不能开放通用 Git 命令/网络/filter；记录原因。
除此保持原 S2 写范围，旧 request/result/capabilities 与 S1公共语义不变。
不修 Map/Area，不改真实任务声明掩盖失败，不读凭据，不改 History/CM，不提交推送发布安装。
不要把原来的漏洞行为冻结成测试预期；保留既有合理验收并新增攻击反例。

运行相关套件与独立 CLI 反例，记录原始结果、修正 diff、模型可观察信息和费用unknown。
更新原计划三件套为候选待独立复验，不自称已接受或2/4。此次仅第1轮修正，不递归代理，
不自发再开修正轮次或S3。完成明确交回原审查者，主助手将继续跟进。
