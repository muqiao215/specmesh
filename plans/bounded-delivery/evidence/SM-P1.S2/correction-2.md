# S2 第 2 轮指定修正（最后一轮）

用户明确要求“继续 agy 对话，打回继续改”。继续原 conversation
d273fe58-78ea-4a0a-98ce-f8d0721f742b，原 S2，不重命名、不重置次数。
保持原配置模型和权限模式，不跳过权限、不递归代理、不自动开启第3轮。
仓库绝对路径：/home/muqiao/桌面/obsidian/my-programming-world/编程/SpecMesh。

先读同目录 review-2.md、review-1.md、原 S2 冻结验收清单。第1轮留下不完整候选，
原进程已结束但没有完整修正交付；不要依赖旧89/89日志或进程 SUCCESS 来认为通过。
先记录当前文件指纹与diff并重跑5条合法失败和攻击反例；保留已有源码/用户改动/所有历史证据。

必须同时修正正常路径与安全边界，不能靠全部拒绝通过安全验收：

1. 生成、序列化schema、消费三处使用一致完整coverage。指纹绑定全部需要保持的交接语义与
   HEAD/index/worktree/source/evidence。仅对调用者提供的对象重算哈希不建立真实性：
   消费时必须按受控调用范围重新读取权威源并对照语义/覆盖/当前取消或冲突状态；
   修改下一步/目标/约束、删coverage、伪造ready并自行重算指纹仍必须拒绝。
2. 所有 staged/unstaged/untracked 都受显式任务/调用者scope限制，不只是untracked。
   不把payload自报scope当作扩大权限的依据。101项不能静默截断并ready；超限显式blocked/unknown。
   不吞扫描异常。所有路径（含dirty/evidence/父目录symlink）通过授权根内descriptor snapshot，
   有界读取并在返回前重验，禁止任意Path.read_bytes绕开根限制。保留已完成的index版本绑定。
3. 证据必须存在且绑定当前内容/来源基线；缺失、删除、更改拒绝。Markdown的passed/reviewer
   只能是asserted候选，不能伪称外部接受；不要引入新的认证服务，保持既有权威边界。
4. CLI文件/stdin输入有界，超量明确拒绝；旧默认CLI、S1协议和安全测试不破坏。

先复现再新增持久回归，包括合法clean/dirty/CLI成功、语义篡改+自算指纹、同HEAD源修改、
取消、index漂移、无关tracked泄露、相关101项、根外dirty/evidence/父目录symlink、
缺失/修改证据、超量CLI输入。不可降低预期、删除失败测试、改真实任务文档掩盖冲突。

限原S2范围及为安全快照/有界Git blob必要的本包支持；不改Map/Area、SPEC、History/CM、
全局配置、凭据。产品验证不访问网络/provider，不提交推送发布安装，不开启S3。
采用一次有界修正过程，执行相关全套与实际CLI验证，保存精确命令/退出码/结果/相对修正前diff。
同步原计划三件套与本卡证据，交付明确最终回复和候选hash，不自称独立接受或2/4。
若无法完成，写清剩余失败并停止；这是第2轮，主助手将独立复验，不自动追加修正额度。
