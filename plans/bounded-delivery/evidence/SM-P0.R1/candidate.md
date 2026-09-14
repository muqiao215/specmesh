# R1 本地候选准备（不是发行验收）

> 2026-09-15 方向同步：下述 ZIP 保留原构建快照与 hash，未覆盖重打包。随后接口文档补充了“独立发展、无 CM 接轨义务”的边界，因此该候选不包含最新文档措辞；代码未因本次方向调整变化。正式发行前须按已验收源码及最新文档重新构建并验证新工件。

用户要求主助手完成所有SpecMesh进度后，已准备可复现发行工具、版本入口与安装自检。
S2独立审查因平台调用失败未完成，因此S3未运行、R1未提交/推送/tag/发布。

- 运行时版本：1.3.0rc1；规范正文仍1.1.0；当前远端最新Release已用gh核对为v1.2.1。
- 基础HEAD：d393c548a2a58989d65e6cdbd60a36e9a81a444f。
- 构建：`python3 -B scripts/build_release.py --version 1.3.0rc1 --allow-dirty --output dist/specmesh-1.3.0rc1.zip`，exit0。
- Artifact SHA256：b3e6b1cd107b0cd361f27176344dc90dac76a11cae1bec93b0f2fc0c85f29637。
- Source identity：55fdb19f07c7449d9a0161fe01969bd452ff98f45e2d999277d3d48a656372e9。
- manifest.json明确candidate=true、source_head、dirty_paths和每个文件hash；没有把dirty归入HEAD。
- 默认构建拒绝未提交输入；不覆盖同名artifact。候选允许开关仅用于本地准备，不代表发布许可或验收。
- 包仅含runtime/contracts、两条发行脚本、README/SPEC/LICENSE、接口说明与templates；
  不含原生历史、任务日志、.git、Map cache或其他项目。

测试：Python3.11/3.12各104/104；其中distribution回归验证重复构建逐字节一致、
manifest逐文件hash、版本一致、拒绝覆写和解包目录独立运行。

实际解包到dist/unpacked-1.3.0rc1。在/tmp分别运行Python3.11和3.12：
`python -I -B <unpacked>/scripts/smoke_release.py --package-root <unpacked>`。
两者均exit0，status=pass，module_root=<unpacked>，版本1.3.0rc1，
checks=isolated_import/project_state/clean_handoff/dirty_preservation/same_head_change_rejected/cancelled_rejected。
没有覆盖用户原安装或全局SpecMesh链接。

未完成：S2独立验收、S3全新B、精确提交SHA的CI、正式tag/Release/工件、
长期本机入口/升级撤回对账。准备结果不关闭R1。费用/token unknown。
