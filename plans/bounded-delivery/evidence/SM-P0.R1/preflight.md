# R1 源码准备与复验 — 2026-09-15

Status: awaiting source-ready review; not published.

S3已验收脚本/测试按原SHA整合。runtime1.3.0，构建allowlist新增verify_install.py；distribution测试使用当前runtime版本并在解包中执行校验器。规范SPEC及用户标准链接不改。

主助手Python3.12：112/112，11.446秒；Python3.11：112/112，11.236秒。两者exit0。
本地preflight ZIP标candidate=true；29/29完整性通过、6/6 smoke通过，加载路径为dist/unpacked-1.3.0-preflight。

独立首审代码通过：两种Python各distribution3/3、发行相关71/71；跨Python构建字节一致，29文件hash一致，无.git/plans/cache；SPEC无diff。但拒绝source-ready：接口文档旧S2等待状态及包内指向未打包文件的相对链接。

定点修正1：同步S2/S3接受状态，仓库专用链接改GitHub URL，Map命令明确仅源码checkout适用；新增包内README/接口文档相对链接完整性断言。distribution3/3（0.619秒），diffcheck0。未修改交接实现或放宽测试，交原审查者续验。

R1原candidate.md工件仅为历史候选，版本及源码已被本次准备取代，不覆盖旧包。不把本地准备当正式发行、安装或最终接受。R1修正轮数1；费用unknown。
