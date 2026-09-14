# S2 首次独立审查 — rejected

2026-09-15，审查者 `/root/s1_independent_review`。S2 首次实现 1，修正轮数 0/2；
总进度 1/4，S1 累计 3 次保留。89/89 测试通过不覆盖以下真实反例。

## 四项 P1（独立 fixture 复现）

1. 消费 verifier 信任 payload，不 validate 合同、不重算 fingerprint、不重读 source/cancel/evidence、
   不发现覆盖遗漏。同 HEAD 修改 PROJECT 或 progress 改 cancelled 后仍
   `verified=True executable=True state=ready issues=[]`。把 cancelled payload 改为 ready/true，
   fingerprint=零、entries=[] 也通过。落点 handoff.py 原 466–517。
2. index 内容未绑定：staged_sha256 恒 None；staged-v1 + worktree-v2 仅保存 worktree-v2。
   git add 改 index、HEAD/worktree 不变，验证仍通过。落点原 128–148、38–41。
3. 全仓 dirty 扫描读取无关 untracked `private-token.txt` 的合成内容并输出；101 untracked 抛
   `ValidationError $.dirty_coverage.entries: array too large`。read_bytes 先全量读取再限 inline，
   绕过 snapshot。落点原 76–122。审查未读取真实凭据。
4. evidence 绝对链接可读取 /tmp 外部文件并按 accepted + Reviewer 猜 passed/is_external；
   无 evidence 或生成后删除 evidence，verify 仍 ready/true。落点原 174–208、400–419。

S2-A/B/C/D/E 均 fail，S2-F reject。legacy/S1 回归通过，但不替代消费门禁和安全边界。
实际命令：`PYTHONPATH=tests python3 -B -m unittest test_map_v0 test_machine_port test_area_overlay test_handoff -v`，
89/89 exit 0；`git diff --check` exit 0。以上为审查者返回的报告摘录，不冒充完整原始 stdout。
未改真实仓或缓存，未访问网络/provider；费用/token unknown。

候选 SHA-256：handoff.py `4365f16f35a393a37ce6b01e094c55fad32b4dbd0f919578b88cbcab1cc730da`；
schema `c1b814eea61da61978bbd4be23d867e272c1a4209bad1d026280a4c635c89d10`；
service `eb5b50e93bc6bc0c745ae6c726da9c4fdba6c402949f55022019414d34a42676`；
CLI `08675dba9d3d764d8898da9fdd3cad2c185e731a29a06862c3b800cbb55bd5c8`；
tests `a28556b2a6a788afd48005cf22e404f3598551537f5908998d0a9ebf37236ebe`。
