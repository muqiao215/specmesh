---
name: SpecMesh
version: 1.1.0
type: project-continuity-standard
canonical: true
---

# SpecMesh v1.1

## 1. 目标

SpecMesh 只解决一件事：

> 任何人或 Agent 接手项目，都能从少量入口开始，逐层获得所需上下文，准确理解项目为什么存在、现在如何工作、为什么这样设计、当前正在做什么。

人的注意力优先用于真实需求、理解纠偏、实现差距和重大方向。代码探索、计划维护、测试、Review 和文档同步默认由 Agent 完成。

## 2. 最小文件系统

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
    └── <task-name>/
        ├── task_plan.md
        ├── findings.md
        └── progress.md
```

没有复杂任务时，`plans/` 可以为空。不默认增加 PRD、ADR 目录、handoff、review、evidence、agent role、项目级模型或 harness 配置。真实需求出现后再增加结构。

## 3. 渐进式索引

```text
L0  README.md + AGENTS.md
                 ↓
L1              PROJECT.md
                 ↓
L2   ARCHITECTURE.md + DECISIONS.md
                 ↓
L3       plans/<task>/{task_plan,findings,progress}.md
                 ↓
                相关代码
```

默认从 `AGENTS.md` 进入，再读 `PROJECT.md`；根据任务选读架构、决策和当前计划，最后只探索相关代码。不默认读取全部文档或仓库。

核心原则：上层负责索引，下层负责细节。不在 `PROJECT.md` 重复架构，不在架构文档重复代码，不在 `progress.md` 重复 Git 历史。

## 4. 文件职责

### README.md

面向第一次看到项目的人，只回答：这是什么、有什么用、如何安装和运行、从哪里继续了解。尽量保持在一到两屏，不保存复杂需求和项目历史。

### PROJECT.md

是仓库最重要的项目记忆，回答“我们到底在做什么”。应包含 `Why`、`User Intent`、`Non-goals`、`Success`、`Constraints`、`Current State`、`Current Priority` 和 `Knowledge Map`。

只在经确认的用户意图、目标、非目标、关键约束、项目阶段或最高优先级改变时更新。普通代码修改不更新它。建议保持在 100–200 行以内。

### AGENTS.md

是项目启动协议，而不是通用编程教程。只说明先读什么、记忆在哪里、何时更新什么，以及项目特有的重要规则。应尽可能稳定，通常几十行即可。

### CLAUDE.md

Claude Code 兼容入口。默认只包含 `@AGENTS.md`；只在出现 Claude Code 独有需求时追加少量内容，不复制 `AGENTS.md`。

### docs/ARCHITECTURE.md

回答“系统现在怎样工作”。保存总览、仓库地图、入口、组件、数据流、不变量、重要外部依赖、脆弱区域和 `Read Next`。保存地图，不保存街景；不逐文件解释仓库，不复制函数注释。

超过几百行后才按领域拆分到 `docs/architecture/`，并让 `ARCHITECTURE.md` 继续作为总索引。

### docs/DECISIONS.md

回答“为什么是现在的方案，而不是另一个同样合理的方案”。只记录未来 Agent 很可能重新争论的重要决定：决定、原因、被否决方案和重访条件。不记录普通 Bug 修复、改名、小重构和一般依赖升级。

### plans/<task>/task_plan.md

回答“这次要完成什么”。包含目标、背景、需求、非目标、可执行计划、成功标准和当前状态。方向明显变化时说明原因，但不写成设计长文。

### plans/<task>/findings.md

回答“任务中发现了哪些值得保留的事实”。记录实际所有权、外部行为、被证伪的假设等对后续有价值的信息。任务结束时，将长期有效的内容晋升到对应的长期记忆。

### plans/<task>/progress.md

回答“已经做到哪里，下一步是什么”。只保存 `Current`、`Done`、`Remaining`、`Issues` 和 `Next`，不重复 Git 已经保存的完整工作日志。

## 5. 何时创建任务记忆

任务可能跨会话、需要明显探索、涉及多个文件或模块、中途容易丢失方向，或可能由其他接手者继续时，才创建 `plans/<task>/`。简单任务直接完成。

## 6. 分层沉淀

```text
临时发现
  ↓
findings.md
  ↓ 确认与当前任务相关
继续使用
  ↓ 证明具有长期价值
PROJECT.md / ARCHITECTURE.md / DECISIONS.md
```

先局部、后全局；先暂存、后晋升。不在信息第一次出现时就污染长期文档。

## 7. 更新映射

| 变化 | 更新 |
|---|---|
| 用户真正想要什么 | `PROJECT.md` |
| 系统怎样工作 | `docs/ARCHITECTURE.md` |
| 为什么选这条路 | `docs/DECISIONS.md` |
| 这次准备怎么做 | `task_plan.md` |
| 这次发现了什么 | `findings.md` |
| 这次做到哪里 | `progress.md` |

## 8. 工作流

```text
Human Intent
    ↓
PROJECT
    ↓
Agent 渐进理解项目
    ↓
必要时创建 Plan
    ↓
Explore + Implement + Verify
    ↓
更新 Findings / Progress
    ↓
沉淀长期知识
    ↓
Human Review
    ↓
新反馈重新进入 PROJECT
```

模型如何使用 Subagent、测试、Review 或 Harness Loop 不属于 SpecMesh。工具解决执行，项目文档解决记忆，人解决方向。

### 变更收口纪律

开放变更是项目记忆的一部分：每个开放 PR 都在声称“这件事正在以这条路径进行”。保持该记忆真实需要两条纪律：

1. **单一轨道**：修复要么始终通过 PR 合并，要么直推 main 后立即关闭对应 PR。禁止“直推吸收 + PR 悬挂”的双轨——它会同时制造已完成与未完成的混合信号。
2. **定期收口**：main 持续演进时，开放 PR 会不可逆腐化（冲突、语义过时、基线漂移）。每个发布周期至少盘点一次开放变更，逐项判定“已被吸收 / rebase / 重写 / 放弃”，并把判定依据留在 PR 上。

判定必须基于证据（`git cherry` 补丁等价性、代码落点、测试覆盖位置），不基于标题相似度。

## 9. 标准动作

### SpecMesh init

在受控仓库中调查真实项目后，创建缺失的最小记忆文件。不对空模板做机械复制，不为简单、vendor 或不受控仓库制造结构。

### SpecMesh check

只读检查，不修改文件。至少报告规范版本、核心文件是否存在、当前计划、渐进索引是否连通、内容是否明显过时或重复，以及最小必要建议。

建议输出：

```text
SpecMesh: detected (vX.Y.Z)
PROJECT.md      present / missing / stale
ARCHITECTURE.md present / missing / stale
DECISIONS.md    present / missing / stale
active plan     <path> / none

Assessment:
...

Recommended actions:
...
```

### SpecMesh sync

根据当前版本检查已采用 SpecMesh 的仓库，只同步规范变化确实影响的项目记忆。保留项目特有内容，不机械重写文档。

### SpecMesh compact

当记忆文档明显膨胀、重复或层级失效时，去重、删除可从代码快速恢复的细节，将深层内容下沉，并修复上层索引。不删除仍影响未来判断的意图、约束或决策。

## 10. 优先级

显式用户指令优先于仓库本地指令，仓库本地指令优先于用户级 SpecMesh 默认约定。SpecMesh 不应被用来悄然重解释或弱化用户需求。

## 11. 最终原则

1. 人的注意力优先用于需求和判断，不用于监督机械流程。
2. 项目文档只保存代码无法快速恢复、但会影响未来判断的信息。
3. 所有知识渐进加载，入口只负责索引，不容纳全部内容。
4. 临时信息先进入任务文件，确认长期有效后才进入长期记忆。
5. 任何新接手者都应能依靠 `PROJECT`、`ARCHITECTURE`、`DECISIONS` 和当前 Plan，在很短时间内恢复项目认知。

SpecMesh 的唯一成功指标是：

> 换一个 Agent，开一个新终端，甚至隔几个月回来，不需要重新讲一遍项目。

## 12. 实验性 Map v0 边界

本节记录仓库中的实验方向，不是 SpecMesh v1.0 的必需结构。项目没有真实检索缺口时，不应机械增加 `.specmesh/` 或派生索引。

Map v0 验证一套极小的共享地址协议：

```text
code://src/auth.py#Session.validate
mem://decision/auth-boundary
spec://acceptance/R-001
```

一张上下文图可以同时检索两类事实，但不能混淆权威：

- 文件、符号、import、reference 和测试关系来自代码与 Git，标记为 `derived`；缓存过期时重新生成。
- 意图、约束、决策和显式关系来自已审查的 Markdown，标记为 `asserted`；修改需要正常 Review。
- 派生索引不进入 Git，不反向覆盖人工记忆。
- 全局 Map 用于定向，任务 focus 用于执行；两者使用同一底图和硬预算。
- v0 使用文件名、符号名、显式关系和 personalized PageRank。没有实测缺口前不增加向量数据库、MCP 服务、后台进程或每目录 Map。

参考实现和实验入口位于 `scripts/map_v0.py` 与 `.specmesh/context.md`。只有跨多个真实任务重复证明有效后，相关机制才可成为后续规范版本的候选。
