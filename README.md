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

## License

[MIT](LICENSE)
