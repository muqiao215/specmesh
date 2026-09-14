# S3 实际任务冻结 — 2026-09-15

Status: prepared; B not dispatched; requires S2 independent acceptance.

## Actual task

给独立发行补充可直接使用的解包完整性校验命令 `scripts/verify_install.py`，读取现有 `manifest.json` 中的文件 SHA-256，报告版本、源码标识及校验结果。它用于 R1 解包后判断文件是否与发行工件一致，不把完整性当作来源签名或任务验收。

## Acceptance fixed before B

- Python 3.11/3.12，仅标准库；无网络、不调用模型、不写被检查的安装目录。
- `--package-root` 指定安装根，JSON输出；全部声明文件匹配返回0。
- 内容不匹配、声明文件缺失、manifest缺失/无效结构时返回非零并给出可诊断结果，不输出成功。
- 不跟随manifest路径到安装根之外，不接受绝对路径、`..`或符号链接文件。
- 只核对声明文件；额外用户文件不删除、不改写，不把它们声称为已验证。
- 保留A已写的测试和dirty资料，补完既有脚手架；实际逻辑必须由全新B完成，不做marker演示。
- 固定单元测试、真实候选解包上的校验、损坏副本上的失败、输入前后hash及独立review共同验收。

## Execution boundary

在受控临时SpecMesh源码副本中进行，记录其来源及完整代码hash；不覆盖本仓已有dirty内容。A先准备任务入口、验收测试、未完成脚手架及保留资料，再用S2生成交接。B只收到副本路径、任务入口、交接位置、范围和本次授权，不继承A会话。

允许B修改副本 `scripts/verify_install.py`；测试和保留资料只读。默认当前AGY配置，不传模型覆盖、不resume/fork；1次全新B执行，1次独立审查，最多2轮指定修正。费用不可读记unknown。入口验证不通过、权限/认证/额度失败则停，不新开替代会话。

本冻结文件只是准备，不证明S3已发生。S2接受前不派发B。
