# S2 第 2 次修正后的最终独立复验：拒绝

日期：2026-09-15。审查者：`/root/s1_independent_review`，沿用原审查者。
主助手整理独立审查返回的结果；下列探针为审查报告摘要，不冒充完整原始 stdout。
原始主助手回归输出见 [correction-2-tests.log](correction-2-tests.log)。

## 结论

SM-P1.S2 **blocked / rejected**，S2-A～E 均未全部满足，S2-F 最终拒绝。
S1 仍 accepted，整体仍 **1/4**。不开始 S3、R1，不新增修复。

## 当前失败

1. 生成入口断裂：`service.py:324,337` 向 `build_handoff` 传入 snapshot，
   `handoff.py:273–287` 的签名没有该参数；实际产生
   `TypeError: build_handoff() got an unexpected keyword argument 'snapshot'`。
   独立定点检查 4 ERROR、1 FAIL，exit 1；合法 CLI 生成 exit 2。
   snapshot 参数又位于 with 生命周期之外。schema:83 已要求 baseline.coverage，
   但 builder:474–479 未输出；仅删除参数也不足以恢复合同。
2. 语义与证据仍可自签：`handoff.py:26` 的指纹不绑定目标、约束、决策、工作状态和下一步；
   verifier 没有从受控权威 Markdown 重建并比较这些语义。构造真实 coverage 哈希、
   schema 合法、语义被替换且 evidence 为空的 payload，实际得到：
   `SELF_SIGNED_SEMANTICS True True [] evidence_count=0`。
   Markdown 的 accepted/pass/Reviewer 仍被推断成证据状态（:224），无证据不阻止 ready（:438）。
3. dirty 范围与截断未修：只有 untracked 被 scope 筛选（:88）；
   staged/unstaged 全仓加入（:104），结果静默截为 100 项（:105）。
   低层探针得到 `LOWLEVEL_101 100 ... omitted_extra_100=True`，
   以及 `LOWLEVEL_TRACKED_SCOPE 1 TOP-SECRET-TRACKED`（仅合成内容）。
   这些是当前低层实现探针；因生成入口崩溃，不把它们称为端到端交接通过。

## 部分变化与未关闭边界

- stdin 超限已拒绝：`CLI_STDIN_LIMIT 2 {"error_type":"ValueError","error":"request_rejected"}`。
- schema 相对路径模式限制了上一轮 ../outside payload；不证明普通 read_bytes、父目录
  symlink 或读取竞态已经通过 descriptor 安全验收。
- staged blob 绑定保留，但正常交接入口故障阻断合法前后验证。
- CLI 文件分支仍在 stat 后普通 read_bytes；snapshot 路径上限从 64 增到 256，
  没有本轮独立通过依据。原缺失的攻击回归未新增。

## 前后结果与验收

| 对照 | 第 1 次修正候选 | 第 2 次修正后的当前候选 |
|---|---|---|
| 相关总回归 | 93 项，88 pass / 5 fail | 93 项，78 pass / 14 error / 1 failure |
| 五条合法路径 | 5/5 失败，主要为 scope_fingerprint_mismatch | 4 error + CLI 1 failure，生成阶段 TypeError |
| 原 Map / machine-port / Area | 78 项通过 | 78 项通过 |
| handoff.py / handoff 测试 | review-2 指纹 | 相同，核心实现和回归未完成修正 |
| 独立判定 | reject | reject |

S2-A 生成与schema不一致；S2-B 语义与证据不足；S2-C scope泄露/静默遗漏；
S2-D 不能拒绝语义自签；S2-E 相关回归失败；S2-F 拒绝。

完整回归命令：
`PYTHONPATH=tests python3 -B -m unittest test_map_v0 test_machine_port test_area_overlay test_handoff -v`
主助手 exit 1，93 项，8.314 秒。独立审查另跑上述五条合法路径及临时合成探针。
`git diff --check` 双方均 exit 0；这只证明空白检查通过。
环境：Python 3.12.3、Git 2.43.0。本次验证无产品 provider/网络调用，未改产品源码。

## 候选与运行绑定

main / HEAD：`d393c548a2a58989d65e6cdbd60a36e9a81a444f`，dirty、未提交。
[累计源码候选](correction-2-candidate.patch)相对这个 HEAD；service/CLI 包含已有 S1 增量，
不是单独第 2 次修正 diff。前一候选指纹及失败仍见 [review-2](review-2.md)，初始材料不删除。
第 1 次修正的完整独立 diff/最终交付缺失，不据指纹声称已恢复全部历史。

```text
handoff.py 74863deb59d1c4bf9b57fff925a9c977d7d33c0bc3dac29bd6e56460223978a0
service.py 51e66f107abd3b7d1be3086d718bc233cdfbcdd166503f685520e834cfaf8420
git_reader.py 2c234a300d514c7c70b0b228aa9a8f700aa536fdd223a6e4e5ae929a49f97dc8
__main__.py ba3fb9c07b3a2e522b8a4c6a67f6cfcd26b926b44b4f34041c2378ccdd0d60c3
snapshot.py d2026e5ca5ecf13db958b5059b8fd6cd81cca5c8f719b35285328c3b928d2802
handoff schema 240e6d4601ab357b8241446197111a683b455038993fe9a49f18d060ef815976
tests/test_handoff.py e91aa2c0ad6186decae6a232880829696e0a2be9d947057dded122e7a8bbf6c9
```

原 AGY conversation：`d273fe58-78ea-4a0a-98ce-f8d0721f742b`。
局部日志 `/home/muqiao/.gemini/antigravity-cli/log/cli-20260915_021407.log`
第 228 行记载 02:44:15 `print timeout after 30m0s with turn in progress`，
随后 stream 完成、Language server shutting down。原 db/lock 无 lsof 持有者，
db 的末次写入仍为 02:44:15；旧 exec 句柄已失效。未把其他 AGY 进程视为本任务仍在执行，
也未因超时重新调用模型。

## 次数、消耗与停止

- S1 累计尝试 3，已有独立接受，不重置。
- S2 一次实现 + 两次修正调用均已使用，第二次超时未完成；这是该轮最终独立复验。
- 本轮 AGY 新增调用 0，新建代理 0；复用原审查者一次。没有 Goal、递归代理或模型覆盖参数。
- 前次已保存的会话流检查点曾报告 total_tokens 2,547,373（input 2,427,014 /
  output 120,359；另有 cache_read 15,076,789、thinking 53,215）。这是会话聚合历史检查点，
  不是本轮新增或完整最终消耗；本次旧流句柄不可读，不重复加总或称为当前余额。
- 第 2 次修正、当前独立审查、完整累计 token 和费用：unknown。产品测试无 provider 调用不等于开发免费。
- 未提交、推送、发布或安装。已到原两轮上限；继续实现需要显式追加 S2 续修授权，
  并沿用原任务/会话/累计次数。S3 已有单次范围授权，仍因 S2 未接受而不可执行。

## 主助手文档收口验证

只同步原计划三件套、PROJECT、计划索引、接口候选状态与本 evidence 入口，未修复产品。
七个 S2 实现/测试指纹再次与上表一致；S1 的 Map/状态模块与 SPEC 指纹未变。
文档变化后 `PYTHONPATH=tests python3 -B -m unittest test_map_v0 test_area_overlay`
38/38 通过，exit 0。Map build/check fresh，cache 仍 ignored；git diff --check 通过。
这组索引验证不替代上述失败的 handoff 验收，也不增加通过分子。
