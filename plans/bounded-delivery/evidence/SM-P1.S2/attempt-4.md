# S2 主助手接手续修 — 原任务累计第 4 次

> 最新：本地修复与验证完成，独立验收未完成。最终候选与全局进度见本文件末段；
> 下方100项/早期hash是本次接手中的检查点，不冒充最终候选。

2026-09-15 用户明确追加“你亲自搞定全部，是所有 SpecMesh 进度”。主助手接替 AGY，
原一次实现、两次修正及超时记录保留；没有重新命名任务或清零消耗。

## 改动与合同

- 消费端必须提供独立可信 task_path 和可选 paths；CLI 使用 --task-path、重复 --scope-path。
  不再由 payload 的 task/candidates 决定读范围。这是未发布 S2 候选的接口收紧；
  旧 specmesh.port request/result/capabilities 与默认 CLI 未改。
- 在一个活跃 DocumentSnapshot 内完成源、证据、dirty 读取与生成；重扫 index/membership，
  然后验证快照与 HEAD。恢复原 64 文档边界，额外文件最多50，dirty超过100显式失败；
  总JSON限制1MiB。超限、删除、非普通文件不伪造空内容；未覆盖范围不称全仓clean。
- 消费时按调用者scope重建当前材料，比较完整语义、coverage、证据、内容和index；
  fingerprint为完整canonical材料SHA。locator使用根相对code://，绑定哈希且可跨工作树。
- 内联Evidence绑定其声明源文件；链接证据绑定目标文件。只有明确Result/HEAD/Reviewer
  字段作为声明保留，is_external恒false；无Evidence或缺目标拒绝。它们不是外部验收。
- CLI stdin和普通文件最多读取1MiB+1；文件使用已打开descriptor、普通文件检查及读取后身份检查。

## 验证与过程中失败

原候选93项为78 pass/14 error/1 failure，见review-3。接手先修实现后，
旧15项测试有10fail/1error：正常验证调用缺新必需scope、root级文件未获显式scope，
以及证据测试未区分绑定声明源与链接目标。保留其成功、拒绝、内容和index断言，
只补可信task/files参数和明确证据目标。

新增7项定点测试（多subtest）：自签语义/emptycoverage/空证据、调用者scope、
无关tracked泄露/101项、缺证据/current冲突、父目录symlink/oversize、
读取中变化、CLI文件/stdin超限。首次新测试remaining_work本来为空，
“修改为空”并未产生篡改；改为注入一条实际新声明后复现检测，未修改产品来迎合空操作。

最终命令：PYTHONPATH=tests python3 -B -m unittest test_map_v0 test_machine_port test_area_overlay test_handoff -v
100/100 pass，exit0，10.276秒；原78项+handoff22项。git diff --check通过。
独立复验待返回，不自行把整体计数改为2/4。

## 候选绑定

HEAD仍d393c548a2a58989d65e6cdbd60a36e9a81a444f，未提交。

```text
handoff.py 5f7450c7dadc1361891158dc289f4238cd4076abbc5bea2a25641520a645056d
service.py 14addca3f573d758a34ae5df18f872e6434aeba36f9383ac8aa24f5cd745265c
__main__.py 8c52d0884efa81e6dca83524ad35a8bfa28ad8611ed7d25c8c2bdebecf87c054
tests/test_handoff.py e4ca3de0900bf046645886c72bbdbd0672f6b9de3746f12fb68d59bffad0af66
```

主助手和独立审查token/费用unknown；AGY新增调用0。旧历史聚合检查点仍在review-3，
不把不可读取的累计总量填零。未来产品阶段另列验收，不合并父子计数。

## 最终本地候选与实际阻塞

又修复显式选中的gitignored文件未保留内容问题；默认发现仍遵守.gitignore，
但调用者明确指定的文件进入dirty内容与后续漂移检查。新增该回归后handoff共23项。
插入测试时一度将文件大小测试的末尾误放入新方法，产生NameError；已恢复两测试边界，
未删除大小限制断言。随后23/23通过。

主助手继续准备发行工具（不是执行S3）：确定性allowlist ZIP + manifest，
源码/版本对账，解包安装自检，runtime版本1.3.0rc1与 --version。独立验证身份未冒充：
smoke_release 的子进程是确定性测试，不是全新Agent B。

最终 `python3 -B -m unittest discover -s tests`：
Python3.12.3，104/104，exit0，10.830秒。
`python3.11 -B -m unittest discover -s tests`：
104/104，exit0，10.603秒。
两次解包自检均从/tmp运行 -I -B，分别使用3.11/3.12；6项check均通过，
module_root准确指向dist/unpacked-1.3.0rc1，不是源码checkout。

```text
handoff.py 30898b7087ae4a2ea88b858a414f5cbb22ac5471518c1ad3a239f54ba63bf970
service.py 14addca3f573d758a34ae5df18f872e6434aeba36f9383ac8aa24f5cd745265c
__main__.py 8d072496aed4abe208552d18879228bdb2a7ded547daffb8616efbc67feb254b
__init__.py 0e787395fbe5f237aab9bd558efbac5d2498a9398fe5792448a0df56b4fc57bd
tests/test_handoff.py 210319999cb75993da30d43ade73dbb7d17d9f1611e2dd380dbe8a5dad3ca7de
build_release.py 8921775ecbcb6fd8b410422224d15b1252b09446c3864554b07ba9dd406d40a8
smoke_release.py 9dfca9410a0c7f497d34516d9628786219d61dbd59cc51e10d89357564ea29eb
tests/test_distribution.py 7e6781941b29d26095817397b8b17e0073c470088daf5bd9873ad882f2051761
```

原审查者的两次续接均被平台中止，返回
`This content was flagged for possible cybersecurity risk`，没有验收结果。
第二次已限定为普通功能/合同检查，仍中止；未继续重试、换模型或改道执行同一审查。
这是平台调用失败，不是对当前代码的独立拒绝或接受。S2保持等待独立验收，
S3不执行，R1只准备本地候选，不正式发布。既有审查门槛不由主实现者自己取消。
当前及累计完整token/费用unknown，失败调用也不视为免费或从计数中抹去。

文档收口后Map/Area/distribution相关41项通过，exit0；map build/check fresh，
git diff --check通过。候选ZIP哈希未变；桌面已有SpecMesh目录软链接准确指向本仓，
当前计划从plans/README进入。期间一次接口说明补丁因长行上下文不匹配未应用，
已改用精确内容更新；没有部分代码改变。没有新建任务、Goal或AGY调用。
