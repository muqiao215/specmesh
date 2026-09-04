# SpecMesh

SpecMesh 是一套轻量的项目连续性规范，帮助人和 Agent 跨会话、跨工具、跨时间渐进恢复项目认知。

它不接管开发流程，也不规定 Agent 如何实现任务。它只定义：项目应保留哪些记忆、放在哪里，以及下一个接手者如何从少量入口逐层读取它们。

## 开始

- 阅读 [SpecMesh 规范](SPEC.md)
- 新项目可从 [templates/](templates/) 复制最小文件
- 用 `SpecMesh init` 初始化，用 `SpecMesh check` 只读检查，用 `SpecMesh sync` 同步规范，用 `SpecMesh compact` 压缩膨胀的记忆

## 最小结构

```text
repo/
├── README.md
├── PROJECT.md
├── AGENTS.md
├── CLAUDE.md
├── docs/
│   ├── ARCHITECTURE.md
│   └── DECISIONS.md
└── plans/
    └── <task>/
        ├── task_plan.md
        ├── findings.md
        └── progress.md
```

`plans/` 可以为空；只有复杂任务才创建任务文件。

## 设计边界

SpecMesh 不是 Skill、Harness、Agent 编排系统或 Spec-Driven Development 框架。代码负责解释实现；SpecMesh 只保存代码不能快速恢复、但会影响未来判断的信息。

## Map v0 实验

仓库包含一个非规范性的 Map v0 spike，用来验证“共享地址与检索、分离事实权威”：

- 代码结构由仓库自动派生，缓存可删除、可重建。
- 项目语义来自已审查的 Markdown，关系明确标记为 `asserted`。
- `code://`、`mem://`、`spec://` 共用一张检索图，但保留各自权威。
- 全局视图和任务 focus 使用同一底图，并受确定性 Token 预算约束。

```bash
python3 scripts/map_v0.py build
python3 scripts/map_v0.py check
python3 scripts/map_v0.py global
python3 scripts/map_v0.py focus "task description"
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

入口见 [`.specmesh/context.md`](.specmesh/context.md)。生成的 `.specmesh/cache/` 不进入 Git，也不属于项目事实源。

## License

[MIT](LICENSE)
