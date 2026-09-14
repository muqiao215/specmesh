# S2 第 1 轮修正后的独立复验：拒绝

审查者 `/root/s1_independent_review`；主助手完整回归 93 项中 5 项失败，独立审查者另行
运行 5 条合法路径回归（5/5 失败，exit 1）及受控攻击 fixture。未改真实仓或缓存。

1. P1：生成指纹包含 coverage，输出 baseline 却缺失 coverage、schema 不允许该字段。
   LEGAL: verified=False executable=False，scope_fingerprint_mismatch。位置 handoff.py 413/474/543。
   另一方面指纹不绑定目标/约束/决定/下一步；替换语义并自算空 coverage 指纹后，
   FORGED_SEMANTICS: verified=True executable=True issues=[]，下一步为攻击者替换文本。
2. P1：仅 untracked 经过 scope 筛选，staged/unstaged 仍全仓读取；101 个相关文件静默截至100，
   build ready，重新计算 payload 指纹后 verify=True 且 omitted=True。无关 tracked 合成私密内容
   被纳入。schema 允许 ../ 路径，verify 直接根路径拼接/read_bytes，根外 dirty 反例通过。
   位置 handoff.py 88/104/105/630/644，schema 192。
3. P1：evidence 仍由普通 read_bytes 读取，按 accepted/pass/Reviewer 文本猜状态/身份，
   无证据仍可 ready；消费侧直接读取 payload 指定路径。位置 handoff.py 224/241/438/572。
4. P1：clean_success、staged_and_unstaged、relevant_untracked、p1_staged_blob、cli_handoff_and_verify
   五条合法路径失败；CLI 合法 verify exit 3。CLI 输入仍 sys.stdin.read/Path.read_text 无界。

S2-A/B/C/D/E fail，S2-F reject。总计仍1/4；S2一次实现、第1轮修正已用，剩余最多1轮。
费用/token unknown；旧通过日志不代表当前候选。

被审查 SHA-256：

```text
handoff.py 74863deb59d1c4bf9b57fff925a9c977d7d33c0bc3dac29bd6e56460223978a0
schema 0c6e1fc6e0ddfda454a0f772c30f27acae7de5339671fccc5e4eb32e224732e5
service.py 50efdb6f251409ec98b065fb4a06a97ef962ac09740aa5696bf504def46954b8
git_reader.py 2c234a300d514c7c70b0b228aa9a8f700aa536fdd223a6e4e5ae929a49f97dc8
CLI 08675dba9d3d764d8898da9fdd3cad2c185e731a29a06862c3b800cbb55bd5c8
tests e91aa2c0ad6186decae6a232880829696e0a2be9d947057dded122e7a8bbf6c9
```

本文件由主助手依据独立返回结果整理，不冒充原始完整stdout。源码不在本次审查中修改。
