# LangChain 学习笔记

> LangChain 是 LLM 应用的**基础抽象层**：模型、消息、工具、结构化输出、Agent、中间件。
> 本目录 6 篇是 LangGraph 的前置地基 —— **LangChain 提供"零件"，LangGraph 提供"怎么把零件连成会循环的机器"**。

---

## 📖 目录

| 序号 | 主题 | 一句话 | 日期 |
|---|---|---|---|
| 01 | [模型调用与消息体系](./langchain-01-模型调用与消息体系.md) | `init_chat_model` 统一入口、六种调用方式、`model_kwargs`/`extra_body`、AIMessage·ToolMessage | 2026-10-06 |
| 02 | [工具调用 Tool Use](./langchain-02-tool-use.md) | `@tool` 三要素、**模型只提议不执行**、`bind_tools`、手动回路、`create_agent` | 2026-10-08 |
| 03 | [结构化输出](./langchain-03-structured-output.md) | `with_structured_output`、Pydantic Schema 设计、底层仍是 Function Calling | 2026-10-08 |
| 04 | [Agent](./langchain-04-agents.md) | **Agent = LLM + 工具 + 循环**、`create_agent` 内部图、checkpointer、HITL | 2026-10-08 |
| 05 | [中间件 Middleware](./langchain-05-middleware.md) | **Middleware = Agent 的 AOP**、六大钩子、18 个内置中间件、四个实战 | 2026-10-10 |
| 06 | [RAG 与文档加载](./langchain-06-rag与文档加载.md) | 微调 vs RAG、离线索引 + 在线检索、`Document`、Loader 家族、切分策略 | 2026-10-11 |

---

## 🧭 阅读顺序（这条线很直）

```
01 模型与消息  →  02 工具调用  →  03 结构化输出  →  04 Agent  →  05 中间件  →  06 RAG
     ↑ 会说话       ↑ 会动手        ↑ 会出结构化        ↑ 会循环      ↑ 能插拔      ↑ 有资料
```

每一篇都是前一篇的能力叠加，不要跳。

---

## ⭐ 核心结论速查

1. **模型只提议，不执行** —— `bind_tools` 只是把 JSON Schema 塞进请求，真正执行工具的是你的代码
2. **`ToolMessage` 靠 `tool_call_id` 与外层 `tool_calls` 配对**，配错就报错
3. **结构化输出的底层还是 Function Calling** —— 就是一个"只有 schema 没有实现的虚拟工具"，只取 args
4. **`create_agent` = model → tool_calls 判断 → tools → 回灌 → 直到无 tool_calls**
5. **Middleware 是 AOP** —— 日志/压缩/审批/重试/限流/脱敏从 agent 本体剥离成可插拔一层
6. **HITL 必须配 checkpointer**，否则中断后接不回来
7. **工具 schema 占上下文** —— 工具越多，留给任务的预算越少（MVTS）

---

## 🔗 和 LangGraph 的关系

| LangChain | LangGraph |
|---|---|
| `create_agent` | 手搓的 `model ↔ tools` 图 |
| Middleware 钩子 | 图上的 node / 节点前后插入 |
| `HumanInTheLoopMiddleware` | `interrupt()` + `ToolNode` |
| checkpointer 记忆 | 完整 checkpoint 链（replay/fork/时间旅行） |
| — | 分支、并行、扇入、子图 |

> **先学 LangChain 会用，再学 LangGraph 会造。** 顺序反过来会很痛苦。

---

_相关板块：[LangGraph 笔记](../langgraph/) · [Learn Claude Code](../learn-claude-code/) · [hello-agents](../hello-agents/)_
