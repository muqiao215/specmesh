# R1 发行与安装证据 — 2026-09-15

Status: release/install observed; final independent acceptance pending.

## Identity chain

- Source commit/tag: 0bfdfd1d4c79bdefc5926b87877253e69a6f93a7, v1.3.0；远端main与tag已核对。
- CI: https://github.com/muqiao215/specmesh/actions/runs/34896336208 — 对应上述SHA，Python3.11/3.12两job success。
- Release: https://github.com/muqiao215/specmesh/releases/tag/v1.3.0 — 非draft、非prerelease；ZIP与SHA256SUMS两asset uploaded。
- ZIP SHA256: 5656c29e993a8bf521fb3d70fb93839bbcd787f7adc1d433d64633c7635db844。
- Manifest: version1.3.0，candidate=false，dirty_paths=[]，29files，source_identity 3a2a3fb2be89c36f808907781b072639e6f9ca267653a4b37a492d356b96ed03。
- Python3.11/3.12各自从精确提交构建ZIP，cmp逐字节一致。GitHub asset digest与本地SHA一致。
- gh release download到dist/remote-1.3.0，sha256sum -c SHA256SUMS为OK；下载包解包29/29完整性通过，两Python各6项smoke通过，module_root为该下载解包目录。

## Installation / rollback

首次安装前确认用户没有.local/bin/specmesh或.local/share/specmesh，不覆盖旧入口。

- 运行时：/home/muqiao/.local/share/specmesh/releases/1.3.0
- 保留回退演练基线：releases/1.3.0rc1-baseline（本任务旧candidate，不冒称v1.2.1正式发行升级已验收）。
- 入口：/home/muqiao/.local/bin/specmesh，隔离Python加载/home/muqiao/.local/share/specmesh/current。
- 实际切换：rc1 → 1.3.0 → rc1 → 1.3.0，每次--version正确，最终current指向releases/1.3.0。
- 安装目录29/29完整性通过；Python3.11/3.12 smoke均通过并显示实际版本化安装目录，而非源码checkout。

切换前后保护值完全相同：A-note worktree SHA7df7a9aff05ae3da065f6bcca1d651084d59a5ce9ae714ca5cbadb9e23288e1f；固定测试SHA67646a89734cb14e160de9c4b61abf40a6c2830012a0198d6a47f947afe80509；index仍000000→88c5995新增A-note。标准链接仍指向原SPEC，SHA5ba5820f1d6ab67b6977520dd0cb2be6e02bbe7b45ce077de1eb35743f8d80ca。未迁移或删除项目记忆。

## Errors and limits

源码准备首审的两个文档问题经一次修正后获source-ready。提交前cached diff检查发现新纳入Git的历史原始.log/.patch空白警告（patch上下文空格有意义）；组合命令仍创建了提交。没有重写原始证据来掩盖记录；排除这两种原始证据后的全部代码/文档diff检查exit0。这些记录不进入发行包。此前未暂存diff check没有覆盖它们，不能冒称整体原始证据无空白警告。

首次下载后sha256sum在仓库根误找SHA256SUMS，报不存在；下载成功未受影响。改到下载目录重验OK。没有覆盖既有release/tag/工件，没有强推或清理dirty。

本轮无新增AGY/B调用，R1修正1轮；完整费用/token unknown。最终独立接受前整体仍3/4。后续4/4文档收口提交不改变已发布runtime文件或v1.3.0标签。
