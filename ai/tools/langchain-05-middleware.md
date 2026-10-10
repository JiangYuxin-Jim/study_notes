# LangChain（五）中间件 Middleware

> 学习日期：2026-10-10
> 课程：LangChain 1.x 入门（Agent 进阶）
> 核心主题：middleware 是什么、六大钩子（node-style / wrap-style）、两种编写方式（装饰器 / 类）、自定义 state、执行顺序与 jump_to、内置中间件全览、四个经典实战（动态 prompt / 动态模型 / 动态工具 / 工具监控）、与 Claude Code Hook 的对照。
> 定位：第四章 Agent 里只提了一句「Middleware 插钩子」，这一章把它讲透——**这是把 create_agent 从「能跑」做到「能上生产」的关键一层**。

---

## 5.1 为什么需要中间件

第四章说到 `Agent = LLM + 工具 + 循环`，而 `create_agent` 把循环封装好了。但真实生产里，循环里**每个环节都得插东西**：

- 调模型前想压缩上下文（不然几轮就爆 token）；
- 调模型前想注入动态系统提示（今天是哪个用户、什么权限）；
- 敏感工具（删库、转账、发邮件）执行前要人工审批；
- 工具挂了想自动重试、模型挂了想自动降级到备用模型；
- 想把每个 tool call 打点上报，做监控和成本统计。

这些逻辑**不该写进 Agent 本体**（否则 Agent 变成一锅粥），而应该像 **Web 框架的中间件**一样，一层层包在外面、可插拔、可复用。

> 💡 官方的定义：middleware 提供了一种方式，更精细地控制 agent 内部发生的事情。适用于：日志/分析/调试、转换 prompt 与工具选择、加重试与回退、限流与护栏/PII 检测。

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware

agent = create_agent(
    model="gpt-5.5",
    tools=[...],
    middleware=[
        SummarizationMiddleware(...),      # 上下文压缩
        HumanInTheLoopMiddleware(...),     # 人工审批
    ],
)
```

**一句话：middleware 是 Agent 的 AOP（面向切面）。**

---

## 5.2 中间件住在哪儿：agent loop 与钩子位置

`create_agent` 内部是一张 LangGraph 图（第四章讲过）：**model node → 判断 tool_calls → tools node → 回灌 → 循环 → 终止**。

middleware 的钩子就挂在这张图的每一步前后：

```
              ┌─────────────── before_agent ───────────────┐
              │                                             │
   ┌──────────▼──────────┐   before_model   ┌───────────┐   │
   │      model node     │◄─────────────────│ wrap_model │   │
   │  （调用 LLM）       │─────────────────►│   _call    │   │
   └──────────┬──────────┘   after_model    └───────────┘   │
              │                                             │
       有 tool_calls ? ──否──► end ────────────────► after_agent
              │是
   ┌──────────▼──────────┐                    ┌───────────┐
   │      tools node     │◄───────────────────│wrap_tool_ │
   │  （执行工具）       │───────────────────►│   call    │
   └──────────┬──────────┘                    └───────────┘
              └──────► 回灌消息，回到 model node
```

> ⚠️ 重要认识：**middleware 不是独立运行时**。钩子就跑在 `create_agent` 返回的那张编译好的 LangGraph 图里面。所以你可以把整个 agent（含全部 middleware）当成一个 node / 子图塞进更大的 `StateGraph`，钩子照常生效。这在「先分类再路由到不同 agent」「并行 fan-out」这类拓扑里非常有用。

---

## 5.3 六大钩子：node-style 与 wrap-style

middleware 的钩子分两派，**职责边界要分清**：

### 5.3.1 Node-style（节点式）：在固定时间点顺序执行

| 钩子 | 触发时机 |
|------|----------|
| `before_agent` | agent 开始前（每次 invoke 一次） |
| `before_model` | **每次**调模型前 |
| `after_model` | **每次**模型返回后 |
| `after_agent` | agent 结束后（每次 invoke 一次） |

**适合**：日志、校验、状态更新、提前终止。

```python
from langchain.agents.middleware import before_model, after_model, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

@before_model(can_jump_to=["end"])
def check_message_limit(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    if len(state["messages"]) >= 50:
        return {
            "messages": [AIMessage("Conversation limit reached.")],
            "jump_to": "end",          # 提前跳出去
        }
    return None                        # 返回 None = 不做任何修改

@after_model
def log_response(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"Model returned: {state['messages'][-1].content}")
    return None
```

### 5.3.2 Wrap-style（包裹式）：包住每一次模型/工具调用

| 钩子 | 包裹对象 |
|------|----------|
| `wrap_model_call` | 每次模型调用 |
| `wrap_tool_call` | 每次工具调用 |

**关键差异**：这个 handler 由你决定 **调用几次**——

- 调用 **0 次** → 短路（比如直接返回缓存、直接拒绝）；
- 调用 **1 次** → 正常流程（先改 request，再放行）；
- 调用 **多次** → 重试、降级。

**适合**：重试、缓存、请求/响应改写、审批拦截。

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")
```

### 5.3.3 一句话对照

| | node-style | wrap-style |
|---|---|---|
| 时间点 | 固定切面（前/后） | 包住调用本身 |
| 能否改 request | 通过 state | ✅ 直接改 `request`（`request.override(...)`） |
| 能否控制调用次数 | ❌ | ✅ 0 / 1 / N 次 |
| 典型用途 | 日志、校验、计数、跳转 | 重试、缓存、审批、动态 prompt/tools |

> 📌 和第四章那句话对上：**wrap-style 才是实现 HITL 工具审批的正确姿势**（在 handler 调用前拦一道）。

---

## 5.4 两种编写方式：装饰器 vs 类

### 5.4.1 装饰器式（简单、单钩子）

```python
from langchain.agents import create_agent
from langchain.agents.middleware import before_model, wrap_model_call

@before_model
def log_before_model(state, runtime):
    print(f"About to call model with {len(state['messages'])} messages")
    return None

@wrap_model_call
def retry_model(request, handler):
    for attempt in range(3):
        try:
            return handler(request)
        except Exception:
            if attempt == 2:
                raise

agent = create_agent(model="gpt-5.5", middleware=[log_before_model, retry_model], tools=[...])
```

可用装饰器：`@before_agent` / `@before_model` / `@after_model` / `@after_agent` / `@wrap_model_call` / `@wrap_tool_call`，外加便利装饰器 `@dynamic_prompt`（生成动态系统提示）。

**什么时候用装饰器**：只需要一个钩子、没有复杂配置、快速原型。

### 5.4.2 类式（复杂、多钩子、可配置）

```python
from langchain.agents.middleware import AgentMiddleware, AgentState
from typing import Any

class LoggingMiddleware(AgentMiddleware):
    def before_model(self, state: AgentState, runtime) -> dict[str, Any] | None:
        print(f"About to call model with {len(state['messages'])} messages")
        return None

    def after_model(self, state: AgentState, runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None

    # 同步/异步双实现：同名加 a 前缀
    async def abefore_model(self, state, runtime): ...
    async def aafter_model(self, state, runtime): ...
```

**类还能声明三个类属性**（编译期被 agent factory 拾取）：

| 类属性 | 作用 |
|--------|------|
| `state_schema` | 扩展 agent state，加自定义字段 |
| `tools` | 给 middleware 自带工具（比如 TodoListMiddleware 的 `write_todos`） |
| `transformers` | 注册流式转换器（scope-aware stream transformer） |

**什么时候用类**：需要同步+异步双实现、一个 middleware 含多个钩子、需要复杂配置（阈值、自定义模型）、跨项目复用。

---

## 5.5 自定义 state：让钩子之间能传数据

middleware 常常需要**跨钩子/跨 middleware 共享数据**（计数器、用户身份、审计标记）。做法是扩展 `AgentState`：

```python
from typing_extensions import NotRequired

class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]
```

**两种钩子的更新机制不一样（易踩坑）：**

- **Node-style**：直接 return 一个 dict，用图的 reducer 合并进 state；
- **Wrap-style**：模型调用要返回 `ExtendedModelResponse(model_response=..., command=Command(update={...}))`；工具调用直接返回 `Command`。

```python
# node-style：直接 return dict
@after_model(state_schema=TrackingState)
def increment_after_model(state, runtime):
    return {"model_call_count": state.get("model_call_count", 0) + 1}

# wrap-style：要用 Command 包一层
@wrap_model_call(state_schema=UsageTrackingState)
def track_usage(request, handler) -> ExtendedModelResponse:
    response = handler(request)
    return ExtendedModelResponse(
        model_response=response,
        command=Command(update={"last_model_call_tokens": 150}),
    )
```

**多个 middleware 同时更新时的组合规则**：

1. **走 reducer**：每个 `Command` 是一次独立更新；`messages` 走加法 reducer，所以是**累加**而非覆盖；
2. **非 reducer 字段冲突时「外层赢」**：内层先应用，外层后应用，最外层 middleware 的值最终生效；
3. **重试安全**：如果外层实现了重试（handler 被调多次），**早先几次调用产生的 command 会被丢弃**。

---

## 5.6 执行顺序与 jump_to（生产调试必看）

多个 middleware 的执行顺序：

```python
create_agent(middleware=[mw1, mw2, mw3], ...)
```

| 阶段 | 顺序 |
|------|------|
| `before_*` | mw1 → mw2 → mw3（**正序**） |
| `wrap_*` | mw1 包 mw2 包 mw3 包 model（**嵌套，像函数调用**） |
| `after_*` | mw3 → mw2 → mw1（**逆序**） |

> 🎯 记忆口诀：**before 正序、after 逆序、wrap 嵌套**。和 Web 中间件、装饰器栈完全一致。

**jump_to（提前跳出）**：返回值里带 `jump_to` 就能改流程走向：

| 目标 | 含义 |
|------|------|
| `'end'` | 跳到 agent 执行末尾（或第一个 `after_agent` 钩子） |
| `'tools'` | 跳到 tools node |
| `'model'` | 跳到 model node（或第一个 `before_model`） |

```python
@after_model
@hook_config(can_jump_to=["end"])
def check_for_blocked(state, runtime):
    if "BLOCKED" in state["messages"][-1].content:
        return {"messages": [AIMessage("I cannot respond to that request.")], "jump_to": "end"}
    return None
```

> ⚠️ 想让 `jump_to` 生效，需要用 `@hook_config(can_jump_to=[...])` 或装饰器参数预先声明**允许跳到哪几处**——这是一种设计上的「白名单」，防止 middleware 乱跳。

**顺带一提（源码级小细节）**：装饰器内部也是转成 `AgentMiddleware` 的——`wrap_tool_call(func=None, *, state_schema=None, tools=None, name=None)`，传了 func 直接返回实例，没传就返回装饰器。所以「装饰器式」和「类式」本质是**同一个东西的两种语法糖**。

---

## 5.7 内置中间件全览（生产必备清单）

官方+Deep Agents 提供了一大批开箱即用的 middleware，**全部 provider 无关**（Anthropic/AWS/OpenAI 另有专属的，如 prompt caching）：

| 中间件 | 作用 |
|--------|------|
| `ToolErrorMiddleware` | 捕获工具异常，转成 error `ToolMessage` 给模型看，而不是直接崩 |
| `ToolRetryMiddleware` | 工具调用失败自动重试，指数退避 |
| `ModelRetryMiddleware` | 模型调用失败自动重试 |
| `ModelFallbackMiddleware` | 主模型挂了自动降级到备用模型 |
| `SummarizationMiddleware` | 接近 token 上限时自动摘要压缩历史 |
| `HumanInTheLoopMiddleware` | 工具调用前暂停，等人工审批 |
| `ModelCallLimitMiddleware` | 限制模型调用次数，防跑飞/控成本 |
| `ToolCallLimitMiddleware` | 限制工具调用次数 |
| `PIIMiddleware` | 检测/脱敏个人身份信息（redact / mask / block） |
| `TodoListMiddleware` | 给 agent 装上 `write_todos` 计划和进度跟踪能力 |
| `LLMToolSelectorMiddleware` | 调主模型前，先用 LLM 选出相关工具（工具多时的降本利器） |
| `ProviderToolSearchMiddleware` | 工具延迟加载，由 provider 服务端按需浮现 |
| `ShellToolMiddleware` | 给 agent 一个持久 shell 会话 |
| `FilesystemMiddleware` | 给 agent 文件系统（存上下文/长期记忆） |
| `SubAgentMiddleware` | 提供 `task` 工具，能派子 agent（上下文隔离） |
| `RubricGradingMiddleware`（Beta） | LLM-as-a-judge，按评分标准自我迭代 |
| `FileSearchMiddleware` | 提供 Glob / Grep 文件搜索工具 |
| `ContextEditingMiddleware` | 到期清理旧的工具调用输出，保留最近 N 条 |
| `LLMToolEmulatorMiddleware` | 用 LLM 模拟工具执行（测试用） |

### 5.7.1 重点拆三个

**① SummarizationMiddleware —— 上下文压缩（≈ learn Claude Code 第七章）**

```python
agent = create_agent(
    model="gpt-5.5",
    tools=[your_weather_tool, your_calculator_tool],
    middleware=[
        SummarizationMiddleware(
            model="gpt-5.4-mini",        # 用便宜的小模型做摘要
            trigger=("tokens", 4000),    # 超过 4000 token 触发
            keep=("messages", 20),       # 保留最近 20 条原文
        ),
    ],
)
```

⚠️ 注意它**只压文本**，不压图片/音视频——保留的多模态消息仍带原始块，被摘要掉的老消息只剩文本摘要。图多的应用要把媒体放对象存储、只传 URL/引用。

**② HumanInTheLoopMiddleware —— 人在回路（≈ learn Claude Code 第四章权限系统）**

```python
agent = create_agent(
    model="gpt-5.5",
    tools=[your_read_email_tool, your_send_email_tool],
    checkpointer=InMemorySaver(),          # ⚠️ HITL 必须配 checkpointer
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "your_send_email_tool": {"allowed_decisions": ["approve", "edit", "reject"]},
                "your_read_email_tool": False,     # 自动放行
            }
        ),
    ],
)
```

配置语义（`interrupt_on` 是 `dict[tool_name, bool | InterruptOnConfig]`）：

- 工具名 → `True`：允许 approve / edit / reject / respond 全部决策；
- 工具名 → `False`：自动放行；
- 工具名 → `InterruptOnConfig`：精细指定允许的决策，还能给 `description`（自定义提示文案）和 `when` 谓词（**动态决定这次是否要打断**）；
- **没列进字典的工具默认自动放行**；
- 匹配的是工具 `.name`——`@tool` 装饰的函数名就是工具名。

> ⚠️ **HITL 必须有 checkpointer**：中断要跨调用保存状态，否则恢复不回来。这也是第四章 checkpointer 的进阶用法（同一套机制既做会话记忆，也做中断恢复）。

**③ ContextEditingMiddleware —— 只清旧工具输出（比摘要更轻）**

```python
ContextEditingMiddleware(
    edits=[ClearToolUsesEdit(trigger=100000, keep=3)],
)
```

- `trigger`：超过多少 token 触发清理（默认 100000）；
- `keep`：必须保留的最近工具结果条数（默认 3）；
- `clear_at_least`：每次至少回收多少 token。

**和 Summarization 的分工**：Summarization 是「把老对话压成摘要」（保语义、贵）；ContextEditing 是「把又臭又长的旧工具输出直接清掉」（保结构、便宜）。长跑 agent 常常两个一起上。

---

## 5.8 四个经典实战（官方 Examples）

### 5.8.1 动态系统提示（Dynamic prompt）—— 最常用

运行时按用户/上下文注入系统提示。**关键 API**：`ModelRequest.system_message`（**永远是 `SystemMessage` 对象**，哪怕创建 agent 时传的是字符串）+ `request.override(...)`。

```python
@wrap_model_call
def add_context(request: ModelRequest, handler):
    new_content = list(request.system_message.content_blocks) + [
        {"type": "text", "text": f"当前用户：{request.state.get('user_id')}，请使用中文回答。"}
    ]
    new_system_message = SystemMessage(content=new_content)
    return handler(request.override(system_message=new_system_message))
```

要点：
- 用 `content_blocks` 读写，**保留原有结构**（字符串/列表都安全）；
- 改完用 `request.override(...)` 生成新 request，**不要原地改**；
- 高级用法（如 Anthropic cache control）可以直接给 `create_agent(system_prompt=SystemMessage(...))`。

### 5.8.2 动态模型选择（Dynamic model selection）

按任务难度/成本选模型：简单问题走小模型，难问题走大模型。同样是 `wrap_model_call` + `request.override(model=...)`。

### 5.8.3 动态工具集（Dynamically selecting tools）

```python
@wrap_model_call
def select_tools(request, handler):
    relevant_tools = select_relevant_tools(request.state, request.runtime)
    return handler(request.override(tools=relevant_tools))
```

三个收益：**prompt 更短**、**模型选得更准**、**能做权限过滤**（不同用户给不同工具）。

> 💡 两种「减工具」路线对比：
> - **规则/代码式**（本节）——自己写筛选逻辑，确定性强、零额外成本；
> - **LLM 式**（`LLMToolSelectorMiddleware`）——用 LLM 判断相关性，更智能但多一次调用；
> - 工具多到几百个时还有第三条路：**ProviderToolSearch**（工具留在服务端，用到才浮现）。

### 5.8.4 工具调用监控（Tool call monitoring）

```python
@wrap_tool_call
def monitor_tool(request: ToolCallRequest, handler) -> ToolMessage | Command:
    print(f"Executing tool: {request.tool_call['name']}")
    print(f"Arguments: {request.tool_call['args']}")
    try:
        result = handler(request)
        print("Tool completed successfully")
        return result
    except Exception as e:
        print(f"Tool failed: {e}")
        raise
```

> 📌 注意 import 差异：`wrap_tool_call` 的 `ToolCallRequest` 来自 `langchain.tools.tool_node`（不是 agents.middleware），要求返回 `ToolMessage | Command`。

**其他官方示例**：Prompt caching（Anthropic 专属，把长 system prompt 标记为可缓存省成本）。

---

## 5.9 对照 learn Claude Code：这是同一种设计

这一章几乎是 learn Claude Code 第四章「钩子函数」的 LangChain 版本，两边可以互相印证：

| 能力 | Claude Code | LangChain |
|------|-------------|-----------|
| 生命周期钩子 | PreToolUse / PostToolUse / UserPromptSubmit… | before/after_agent、before/after_model、wrap_model_call、wrap_tool_call |
| 权限接管 | Hooks 拦截工具调用、allow/deny/ask/defer 四决策 | `HumanInTheLoopMiddleware`（approve/edit/reject/respond） |
| 上下文压缩 | 四级降级 + LLM 摘要兜底 | `SummarizationMiddleware` + `ContextEditingMiddleware` |
| 任务清单 | TodoWrite | `TodoListMiddleware`（自带 `write_todos`） |
| 子 agent | Subagent（上下文隔离） | `SubAgentMiddleware`（`task` 工具） |
| 记忆/文件 | CLAUDE.md / 文件系统 | `FilesystemMiddleware` + checkpointer |

> 🎯 **本质结论**：主流 agent 框架都在同一位置收敛——**把「循环里的横切逻辑」抽成可插拔的一层**。Claude Code 叫 Hook，LangChain 叫 Middleware，Spring 叫 AOP / 拦截器，Web 框架叫中间件。**理解了这一层，换任何框架都能一眼看懂它在干嘛。**

---

## 5.10 最佳实践

1. **职责单一**——一个 middleware 只干一件事（压缩就压缩，审批就审批）；
2. **别让 middleware 的错误炸掉 agent**——内部 try/except，失败要优雅降级；
3. **选对钩子类型**——顺序逻辑用 node-style，控制流（重试/缓存/拦截）用 wrap-style；
4. **自定义 state 字段要写清楚文档**（多个 middleware 共享 state 时尤其重要）；
5. **先独立单测 middleware**，再接到 agent 上；
6. **注意顺序**——关键 middleware 放列表前面（`before_*` 正序执行，且 wrap 时外层最先包住）；
7. **能用内置就用内置**，别重复造轮子。

---

## 5.11 本章总结

1. **Middleware = Agent 的 AOP**：把日志、压缩、审批、重试、限流、脱敏这些横切关注点从 agent 本体里剥出来，可插拔、可复用。
2. **两类钩子**：node-style（`before/after_agent`、`before/after_model`，顺序执行、管状态和跳转）；wrap-style（`wrap_model_call`、`wrap_tool_call`，包住调用、能控制调用 0/1/N 次）。
3. **两种写法**：装饰器（简单单钩子）vs 类（多钩子/配置/同步异步双实现，可声明 `state_schema` / `tools` / `transformers`）。
4. **state 扩展有讲究**：node-style 直接 return dict；wrap-style 要 `ExtendedModelResponse` + `Command`；多 middleware 组合时「messages 累加、非 reducer 字段外层赢、重试丢弃旧 command」。
5. **执行顺序**：before 正序、after 逆序、wrap 嵌套；`jump_to`（end/tools/model）可提前跳出，但要先用 `hook_config` 声明白名单。
6. **内置库很全**：重试/降级（Tool/Model Retry、Model Fallback）、压缩（Summarization、ContextEditing）、安全（HITL、PII）、成本（Model/Tool Call Limit、LLMToolSelector）、能力扩展（Todo、SubAgent、Filesystem、Shell、FileSearch）。
7. **HITL 必须配 checkpointer**；Summarization 只压文本不压多模态。
8. **和 Claude Code Hook 是同一设计**：换框架不换思路。

### 🔗 与主线的衔接
- **第四章 → 第五章**：第四章说 Agent=LLM+工具+循环、middleware 插钩子；第五章把「钩子」这层讲透。两章合起来 = `create_agent` 的完整用法。
- **learn Claude Code 第四/五/七章**：Hook 权限 / TodoWrite / 上下文压缩 → 在这里分别对应 HITL、TodoList、Summarization+ContextEditing。**同一批工程问题的两种实现**。
- **hello-agents 第七/八章**：自建框架「万物皆为工具」——middleware 正是「把横切能力做成可插拔组件」的工程化落地版。
- **hello-agents 第九章（ContextBuilder / GSSC 流水线）**：上下文构建的流水线，和 `SummarizationMiddleware` + `ContextEditingMiddleware` + 动态 prompt 解决的是同一个问题。
- **天机学堂（Java 落地）**：Spring AI 里做「对话记忆/工具审批/多智能体路由」，思路可直接搬这套职责划分。

---

## 习题自检
- Middleware 解决的核心问题是什么？（答：把 agent 循环里的横切关注点——日志/压缩/审批/重试/限流——抽成可插拔一层，不污染 agent 本体）
- node-style 和 wrap-style 最本质的区别？（答：wrap-style 能控制 handler 调用 0/1/N 次，可直接改 request；node-style 只在固定切面顺序执行、改 state）
- 想让模型调用失败自动重试 3 次，用哪个钩子？（答：`wrap_model_call`，或用内置 `ModelRetryMiddleware`）
- 工具审批为什么必须配 checkpointer？（答：中断要跨调用持久化状态，否则恢复不回来）
- 三个 middleware 的 `before_model` / `after_model` 分别按什么顺序跑？（答：before 正序 mw1→mw2→mw3，after 逆序 mw3→mw2→mw1，wrap 嵌套）
- 想按用户权限动态收窄工具集，用哪个钩子？（答：`wrap_model_call` + `request.override(tools=...)`，或用 `LLMToolSelectorMiddleware`）
- 改系统提示要注意什么？（答：`ModelRequest.system_message` 永远是 SystemMessage 对象，用 `content_blocks` 保留结构，改完用 `request.override()`）
- Summarization 和 ContextEditing 的分工？（答：前者把老对话压成摘要保语义，后者直接清掉旧工具输出保结构，二者互补）

### 📎 参考
- Middleware overview: https://docs.langchain.com/oss/python/langchain/middleware/overview
- Custom middleware: https://docs.langchain.com/oss/python/langchain/middleware/custom
- Prebuilt middleware: https://docs.langchain.com/oss/python/langchain/middleware/built-in
- Human-in-the-loop: https://docs.langchain.com/oss/python/langchain/human-in-the-loop
