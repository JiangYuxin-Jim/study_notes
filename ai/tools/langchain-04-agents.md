# LangChain（四）Agent：从工具到自主循环

> 学习日期：2026-10-08
> 课程：LangChain 1.x 入门（Agent 层）
> 核心主题：Agent 到底是什么（LLM + 循环 + 工具）、ReAct 的思考-行动-观察范式、`create_agent` 的用法与内部结构、中间件（middleware）扩展、记忆/持久化（checkpointer）、人在回路（HITL），以及 `create_agent` 与"手写 AgentExecutor"的取舍。
> 定位：把 LangChain（一）的模型、（二）的工具、（三）的结构化输出串起来，得到第一个真正意义上自主决策的 Agent。

---

## 4.1 Agent 是什么：一句话定义

> **Agent = 在循环中自主调用工具的 LLM。**

拆成三要素：

| 要素 | 作用 | 来自哪一章 |
|------|------|-----------|
| **LLM（大脑）** | 推理、决策、决定下一步 | LangChain（一）模型调用 |
| **工具（手脚）** | 与外部世界交互（搜索、计算、API、DB） | LangChain（二）Tool Use |
| **循环（心跳）** | 反复「决策 → 执行 → 观察」直到目标达成 | 本章 |

对比：
- **单次调用**：用户问 → 模型答（一次性，无外部能力）；
- **工具调用**：用户问 → 模型提议调工具 → 你执行（**但只走一轮**，之后要不要继续是你自己写的）；
- **Agent**：用户问 → 模型决策 → 执行 → **结果回灌 → 模型再决策** → … → 直到模型认为可以作答（**循环由框架驱动**）。

> 💡 和 hello-agents 第一章的「Workflow vs Agent」呼应：把 if-else 写死的流程编排是 Workflow；让 LLM 在循环里自主决定「下一步干嘛」才是 Agent。

---

## 4.2 经典范式：ReAct（Reasoning + Acting）

ReAct = **Thought → Action → Observation** 循环，是所有 Agent 范式的原祖：

```
Thought:  用户想知道杭州天气，我需要调用天气工具。
Action:   get_weather(city="杭州")
Observation: 杭州今天晴，25℃
Thought:  信息够了，可以回答。
Final Answer: 杭州今天晴，25℃。
```

LangChain 里的对应关系：
- **Thought** → 模型的推理文本（或 tool_calls 前的思考）；
- **Action** → `AIMessage.tool_calls`（第二章学过）；
- **Observation** → `ToolMessage`（回灌结果）；
- **循环终止** → 模型不再产出 `tool_calls`，转为输出最终回答。

其他常见范式（hello-agents 第七章已经实现过）：
- **Reflection**：生成 → 自我批评 → 修订；
- **Plan-and-Solve**：先出计划，再逐步执行；
- **Function Calling 范式**：直接用原生 tool_calls（LangChain 现代表的主流做法）。

> 💡 **现代 LangChain 的 Agent 就是「原生 Function Calling 版 ReAct」**：不再靠解析文本里的 "Action:" 字段，而是靠模型原生输出的结构化 `tool_calls`——稳定性大幅提升（这就是结构化输出的价值）。

---

## 4.3 `create_agent`：开箱即用的 Agent

```python
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

def get_weather(city: str) -> str:
    """查询指定城市的天气"""
    return f"{city}今天晴，25℃"

agent = create_agent(
    model=model,                        # 或 "deepseek:deepseek-v4-flash"
    tools=[get_weather],
    system_prompt="你是一个乐于助人的助手，需要时主动使用工具。",
)

result = agent.invoke({
    "messages": [HumanMessage("杭州今天天气怎么样？")]
})

# 输出包含完整中间过程
for msg in result["messages"]:
    print(type(msg).__name__, "|", getattr(msg, "content", "")[:60])
```

输出消息序列大致是：

```
HumanMessage
AIMessage        ← tool_calls: get_weather
ToolMessage      ← 杭州今天晴，25℃
AIMessage        ← 最终回答
```

**关键点**：
- 入参/出参都是 **`{"messages": [...]}`**（标准状态字典）；
- `result["messages"]` 保留**全部中间消息**——调试、审计、tracing 全靠它；
- **没有 `AgentExecutor` 了**：LangChain 1.x 用 `create_agent` 取代了老的 `AgentExecutor` + `create_react_agent`，更简洁、更可控。

### 4.3.1 内部到底做了什么（黑盒拆解）

`create_agent` 内部是一条 **图（graph）**（因为它基于 LangGraph）：

```
       ┌──────────────┐
       │  model node  │──── 有 tool_calls? ────┐
       └──────────────┘                        │否
              ↑                                ↓
              │                        ┌──────────────┐
         ToolMessage 回灌               │   END（回答） │
              │                        └──────────────┘
       ┌──────────────┐        是
       │  tools node  │←────────────┘
       └──────────────┘
```

- **model node**：调模型；
- **条件边**：判断有没有 `tool_calls` → 有就去 tools node，没有就结束；
- **tools node**：执行工具、产出 `ToolMessage`，再回到 model node。

> 💡 这就是第二章「手动回路四步」的**自动化 + 循环化**版本。看懂这张图，你就看懂了 Agent。

### 4.3.2 常用参数

| 参数 | 作用 |
|------|------|
| `model` | 模型实例或 `"provider:model"` 字符串 |
| `tools` | 工具列表（`@tool` 定义或 `StructuredTool`） |
| `system_prompt` | 系统提示（角色、行为准则、何时用工具） |
| `response_format` | 结构化输出（接第三章） |
| `middleware` | 中间件列表（见 4.4） |
| `checkpointer` | 持久化（见 4.5） |

---

## 4.4 中间件（Middleware）：在循环里插入你的钩子

Middleware 让你**不改核心循环**的前提下，在关键位置插逻辑。常见钩子类型：

| 钩子 | 触发位置 | 典型用途 |
|------|---------|---------|
| `before_model` | 每次调模型前 | 压缩历史、注入动态上下文、限流 |
| `after_model` | 模型返回后 | 审核输出、改写 tool_calls |
| `wrap_tool_call` | 工具执行前后 | 日志、缓存、重试、沙箱限制 |
| `before_agent` / `after_agent` | 整个 Agent 起止 | 初始化、结果落盘 |

**最典型的应用场景**：

1. **上下文压缩**：历史太长时，在 `before_model` 里做摘要——这正是 learn Claude Code 第七章「上下文压缩」的 LangChain 版；
2. **工具调用审批（HITL）**：在 `wrap_tool_call` 里拦截敏感工具（如 `delete_file`、`send_email`），要求人工确认后才执行——对应 learn Claude Code 第四章「权限接管」；
3. **动态工具集**：根据当前任务在 `before_model` 里切换可用工具，控制上下文预算——对应 hello-agents 第九章的 MVTS。

> 💡 **Middleware = LangChain 版的 Hook 系统**。learn Claude Code 里 Hooks/PreToolUse 能做的一切，这里都有对应位置。

---

## 4.5 记忆与持久化：checkpointer

默认情况下 `agent.invoke` 是**无状态**的——你不传历史，它就不知道上一轮聊了什么。

解决方式：给它一个 **checkpointer**，按 `thread_id` 保存对话状态：

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model=model,
    tools=[get_weather],
    checkpointer=InMemorySaver(),        # 生产环境换成 SQLite / Postgres saver
)

config = {"configurable": {"thread_id": "user-123"}}

agent.invoke({"messages": [HumanMessage("杭州天气？")]}, config)
agent.invoke({"messages": [HumanMessage("那明天呢？")]}, config)   # ← 记得上文，能接上
```

要点：
- **`thread_id` 是记忆的隔离键**：同一个 id 共享历史，不同 id 互不影响（= 多用户/多会话隔离）；
- 开发用 `InMemorySaver`，**生产必须换持久化后端**（SQLite/Postgres），否则进程重启记忆全丢；
- 这就是 learn Claude Code 第八章「记忆系统」的分层——**会话记忆（checkpointer）vs 长期文件记忆（外部存储）**，两者互补。

---

## 4.6 人在回路（HITL）：让 Agent 停下来问一句

敏感操作（删库、转账、发邮件）必须人工确认。做法通常是 **middleware + 中断（interrupt）**：

```python
# 伪代码：工具调用前请求审批
def approval_middleware(request, handler):
    if request.tool_call["name"] in SENSITIVE_TOOLS:
        approved = ask_human(request.tool_call)   # 阻塞等待人工决策
        if not approved:
            return "操作已被用户拒绝"
    return handler(request)
```

工程要点：
- **审批粒度**：按工具名、按参数（金额 > 1000）、按路径（非 workspace 文件）分级；
- **拒绝也要回灌**：拒绝的结果要作为 `ToolMessage` 返回，让模型知道「这条路走不通」并换方案，而不是直接崩；
- 参考 learn Claude Code 第四章的四决策：`allow / deny / ask / defer`。

---

## 4.7 `create_agent` vs 手写循环：怎么选

| 场景 | 建议 |
|------|------|
| 常规 Agent、快速落地 | ✅ `create_agent`：循环/容错/流式都帮你搞定 |
| 需要自定义循环形状、特殊中断语义 | 用 `create_agent` + middleware 定制，或直接上 LangGraph 画图 |
| 只想跑一次模型决策、执行在外部系统 | ✅ `bind_tools` 手动回路（第二章） |
| 教学 / 理解原理 | ✅ 手写一遍循环（hello-agents 第七、八章做过） |

> 💡 一句话：**`create_agent` 是 LangGraph 的「高层 API」**——先用它跑通，不够用了再往下降一层画图。

---

## 4.8 本章总结

1. **Agent = LLM + 工具 + 循环**；区别于 Workflow 的关键在于「下一步由 LLM 在循环里自主决定」。
2. **ReAct** 是原祖范式（Thought-Action-Observation）；现代 LangChain Agent = 原生 Function Calling 版 ReAct（靠结构化 `tool_calls`，不解析文本）。
3. **`create_agent`** 是 1.x 的推荐入口，取代了老的 `AgentExecutor`；入出参都是 `{"messages": [...]}`，保留完整中间过程便于调试。
4. **内部是一张图**：model node → 判断 tool_calls → tools node → 回灌 → 循环 → 终止。这就是第二章手动回路的自动化版本。
5. **Middleware** 在循环关键位置插钩子：上下文压缩、工具审批（HITL）、动态工具集——对应 learn Claude Code 的 Hook / 权限系统。
6. **Checkpointer** 给 Agent 装上会话记忆，`thread_id` 做隔离；生产环境必须换持久化后端。
7. **HITL** 是生产 Agent 的必需品：敏感工具必须人工确认，拒绝也要回灌给模型。

### 🔗 与主线的衔接
- **四章连成一条线**：模型（一）→ 工具（二）→ 结构化输出（三）→ Agent（四）。Agent 就是把前三者装进一个循环里。
- **hello-agents 第七/八章**：自建框架里的 SimpleAgent / ReActAgent / FunctionCallAgent 就是本章 `create_agent` 的手工版；理解框架封装了什么，才知道什么时候不该用它。
- **hello-agents 第九章 + learn Claude Code 第七/八章**：Agent 的「长时程稳定运行」靠的是上下文工程 + 记忆 + 压缩，正是 middleware 与 checkpointer 的用武之地。

---

## 习题自检
- Agent 与「单次工具调用」的本质区别？（答：Agent 是框架驱动的循环，会反复决策-执行-观察直到完成；单次调用只走一轮）
- 现代 LangChain Agent 为什么不需要解析文本里的 "Action:"？（答：用模型原生结构化 `tool_calls`，等价于原生 Function Calling 版 ReAct）
- `create_agent` 内部那张图有哪几个节点？（答：model node / tools node + 判断 tool_calls 的条件边 + 终止）
- 想让 Agent 记住上一轮对话要怎么做？（答：传 checkpointer，并用 `thread_id` 隔离会话）
- 敏感工具怎么做人工审批？（答：middleware 拦截工具调用 + 中断等待人工决策，拒绝结果也要作为 ToolMessage 回灌）
