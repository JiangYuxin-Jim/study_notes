# Learn Claude Code 学习笔记

> 跟着「Learn Claude Code」系列拆解 Claude Code 的内部机制：**Agent Loop、工具调用、权限体系、Hooks、TodoWrite、Subagent/Skill、上下文压缩、记忆系统**。
> 这个系列的价值不在"学会用 Claude Code"，而在**看懂一个生产级 Agent 产品是怎么被工程化的** —— 后面学 LangChain / LangGraph 时你会反复看到同一套设计换了个名字。

---

## 📖 目录

| 序号 | 主题 | 一句话 | 日期 |
|---|---|---|---|
| 00 | [前三章：Agent Loop · 工具调用 · 权限隔离](./learn-claude-code-前三章.md) | TAO 循环的工程化、工具 name/description/schema 三要素、三层权限（白名单→参数校验→人工确认） | 2026-09-17 |
| 04 | [钩子函数 Hooks](./learn-claude-code-04-钩子函数.md) | 生命周期事件、三层配置结构、5 种 handler、退出码 0/2、`PreToolUse` 四决策与权限接管 | 2026-09-18 |
| 05 | [TodoWrite](./learn-claude-code-05-todowrite.md) | 元工具（只写自身状态）、四态生命周期、**提醒机制**、模型可用性反直觉事实 | 2026-09-20 |
| 06 | [Subagent 与 Skill 加载](./learn-claude-code-06-subagent与skill加载.md) | 上下文隔离、按需加载、五级作用域、**上下文成本总表与选型** | 2026-09-21 |
| 07 | [上下文压缩](./learn-claude-code-07-上下文压缩.md) | 四级降级策略：结果截断 → 消息数量 → 内容引用化 → LLM 摘要兜底 | 2026-09-22 |
| 08 | [记忆系统](./learn-claude-code-08-记忆系统.md) | LLM 无状态 → 记忆是工程问题；CLAUDE.md 显式长期记忆；与压缩互补 | 2026-10-04 |

> 注：第 1~3 章合并为「前三章」一篇；第 4~8 章各一篇。

---

## 🧭 建议阅读顺序

```
前三章 → 04 钩子 → 05 TodoWrite → 06 Subagent/Skill → 07 压缩 → 08 记忆
  ↑            ↑           ↑                ↑              ↑         ↑
 地基       可插拔扩展   规划能力        上下文隔离      事前预防   长期沉淀
```

第 07 章和第 08 章是一对：**压缩是"事后补救"，记忆是"事前沉淀"**，合起来才是完整的上下文管理闭环。

---

## ⭐ 和其它板块的对照关系（这套设计的复用价值）

| Claude Code 概念 | LangChain / LangGraph 里的对应物 |
|---|---|
| Agent Loop（TAO） | `create_agent` 内部图 / 手搓 ReAct 图 |
| Hooks（`PreToolUse` 等） | Middleware 的 node-style / wrap-style 钩子 |
| 工具审批弹窗 | `interrupt()` + `ToolNode`（HITL） |
| TodoWrite | LangChain `TodoListMiddleware` |
| Subagent | LangGraph Subgraph / `SubAgentMiddleware` |
| 上下文压缩四级 | `SummarizationMiddleware` / `ContextEditingMiddleware` |
| CLAUDE.md 长期记忆 | LangGraph `Store`（固定 namespace） |

> **换个框架不换思路** —— 这是这一整个系列最值钱的地方。

---

## 📌 几条踩过就忘不掉的结论

1. **Agent Loop 的终止条件**才是核心，不是 prompt
2. **工具的 description 就是 prompt**，写得含糊模型就一定调错
3. **权限要分层**：白名单 → 参数级校验 → 人工确认，越往后越贵
4. **Hook 是免费的上下文外包** —— 用代码做的事，别让模型想
5. **压缩要"能机械就别调 LLM"**，摘要兜底是最后手段
6. **该记的记、该忘的忘、该想起来时想得起来** —— 记忆系统的三句话设计心法

---

_相关板块：[LangGraph 笔记](../langgraph/) · [hello-agents](../hello-agents/) · [Transformer 实战](../transformer/)_
