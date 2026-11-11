# LangChain（一）模型调用与消息体系

> 学习日期：2026-10-06
> 课程：LangChain 1.x 入门（模型层）
> 核心主题：LangChain 1.x 中如何统一初始化对话模型、六种调用方式（同步/异步/流式/批量）、额外参数的传递方式（model_kwargs / extra_body）、可观测平台 LangSmith，以及对话消息体系 AIMessage / ToolMessage 的关键字段。
> 定位：Agent / RAG 工程落地的框架基础（此前 hello-agents 第六章用过 LangGraph，这里补 LangChain 本体）。

---

## 1.1 模型的两种初始化写法

### 1.1.1 传统写法：直接用模型类

```python
model = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)
```

特点：**绑定具体厂商类**（`ChatOpenAI`、`ChatAnthropic`…），换模型要换类。

### 1.1.2 统一写法：`init_chat_model()`（LangChain 1.x 推荐）

```python
# 获取大模型
model = init_chat_model(
    # model="deepseek-v4-flash",
    # model_provider="deepseek",
    # 或者直接写成 "provider:model" 的形式
    model="deepseek:deepseek-v4-flash",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)
```

- 两种等价写法：**`model` + `model_provider` 分开传**，或 **`"provider:model"` 合并成一个字符串**；
- 好处：**模型与代码解耦**，把模型名/厂商做成配置项，切换模型不用改调用代码（和第七章"万物皆为工具"的解耦思路一致）；
- 只要是 OpenAI 兼容协议的厂商（DeepSeek 等），可以通过 `base_url` + `api_key` 直接接入。

---

## 1.2 模型的调用方式（Invocation）

在 LangChain 中，**模型调用（Invocation）** 指通过特定方法触发大语言模型生成输出的过程。围绕「同步 / 异步」×「单条 / 批量 / 流式」两个维度，共六种：

| 方法 | 语义 | 特点 | 适用场景 |
|------|------|------|---------|
| `invoke()` | 单条调用 | **阻塞式，一次性返回完整结果** | 问答、批处理任务、无需实时反馈 |
| `ainvoke()` | 单条调用（异步） | 非阻塞，提高系统吞吐量 | 高并发 Web 应用、IO 密集型任务 |
| `stream()` | 流式输出 | **实时返回每个 token** | 聊天机器人、长文本生成、需提升体验的交互应用 |
| `astream()` | 流式输出（异步） | 非阻塞，提高系统吞吐量 | 高并发 Web 应用、IO 密集型任务 |
| `batch()` | 批量处理多个输入 | **并发处理一批任务**，但本身是同步接口，会阻塞当前线程 | 需同时处理大量请求的场景 |
| `abatch()` | 批量处理（异步） | 异步接口，等待这批任务时**事件循环可去处理别的任务** | 高并发 Web 应用、IO 密集型任务 |

> 💡 记忆口诀：**`a` 前缀 = async = 不阻塞线程**；**`stream` = 逐 token 实时**；**`batch` = 一次多输入**。
>
> ⚠️ 易错点：`batch()` 内部并发，但**接口仍是同步的**——它会把当前线程占住；要真正释放线程必须用 `abatch()`。

**性能结论（本课实测口径）**：`batch()` 比循环调用 `invoke()` **更快**（框架内部并发/批处理），但真正的并行收益要配合异步版本。

---

## 1.3 额外参数怎么传

LangChain 的封装只暴露了常见字段，模型厂商还有些"私有/扩展"参数，需要通过两个口子传：

### 1.3.1 `model_kwargs` —— 模型本身支持、但 LangChain 没列出的字段

```python
model = init_chat_model(
    model="deepseek:deepseek-v4-flash",
    model_kwargs={ ... },   # 模型原生支持但不在一等参数里的字段
)
```

判断标准：**「模型本身支持」但「LangChain 没直接列出来」** → 放 `model_kwargs`。

### 1.3.2 `extra_body` —— 厂商基于 OpenAI API 协议扩展的字段

- 用于存放**模型厂商在 OpenAI 协议之外自己扩展的字段**；
- 典型例子：`thinking` 是 **DeepSeek 扩展的字段**，用于控制是否启用思考模式（DeepSeek V3.1/V4 系列的混合思考）；
- 这些字段不属于 OpenAI 标准协议，因此走 `extra_body` 透传给服务端。

> 💡 两者区别：`model_kwargs` 偏"模型级通用参数"，`extra_body` 偏"厂商私有协议字段（请求体扩展）"。

---

## 1.4 LangSmith：LLM 应用的可观测平台

**LangSmith** 是 LangChain 生态中专门用于 LLM 应用 **调试、监控、评估和管理** 的平台。

| 能力 | 说明 |
|------|------|
| 🔍 **追踪 (tracing)** | 记录每次 LLM 调用的详细信息（输入、输出、耗时、token、中间链路） |
| 📊 **监控 (monitoring)** | 实时查看应用性能 |
| 🐛 **调试 (debug)** | 排查问题、优化性能 |
| 📈 **评估 (evaluate)** | 系统化测试 LLM 应用（数据集 + 评分器，回归对比） |

> 💡 工程意义：Agent 是"多步调用 + 工具链"的复杂链路，**没有 tracing 基本无法排查问题**——这也是 learn Claude Code 里"上下文/调用链可观测"思路的商业化落地版本。
> 用法通常只需配置环境变量（`LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT`），调用会自动上报，不改业务代码。

---

## 1.5 消息体系：AIMessage 与 ToolMessage

Agent 的每一轮交互都是**消息列表**的传递，消息类型决定模型如何理解上下文。

### 1.5.1 消息类型总览

| 消息类型 | role | 谁产生 | 作用 |
|---------|------|--------|------|
| `SystemMessage` | system | 开发者 | 系统指令 / 角色设定 |
| `HumanMessage` | user | 用户 | 用户输入 |
| `AIMessage` | assistant | 模型 | 模型输出（可能含工具调用） |
| `ToolMessage` | tool | 工具执行结果 | 把工具返回值喂回模型 |

### 1.5.2 AIMessage 参数列表

**`content`**：模型输出的原始内容，字段名可以省略。

```python
AIMessage("你好~")
# 等价于
AIMessage(content="你好~")
```

**`response_metadata`**（AIMessage 特有）：LLM 响应中附加的元数据，**不同模型内容不同**，常见如本次 token 使用量等信息。

**`tool_calls`**（AIMessage 特有）：工具调用信息。当 LLM 决定调用工具时，AIMessage 里就会带这个属性，**没有工具调用则为空**。结构：

```python
tool_calls = [
    {
        'name': 'get_weather',        # 应调用的工具名
        'args': {'city': '杭州'},      # 调用工具的参数
        'id': 'call_00_gIXYOD1Q1OkEXmdDBqXR1578',  # 工具调用的唯一标识 ID
        'type': 'tool_call'
    },
    {
        'name': 'get_news',
        'args': {},
        'id': 'call_01_jD3phD5PEaIzF0mvLhkT0861',
        'type': 'tool_call'
    }
]
```

> 💡 一次 AIMessage 可以携带**多个** tool_calls → 模型一次决策可并行调多个工具。

### 1.5.3 ToolMessage 参数列表（拓展）

| 参数 | 说明 |
|------|------|
| `content` | 工具返回的内容 |
| `name` | 工具名称 |
| `tool_call_id` | 工具调用唯一 ID |

**硬性规则**：`ToolMessage` 必须**紧邻匹配的 AIMessage**，且 `tool_call_id` 要和前者 `tool_calls` 中的 `id` **一致**。

### 1.5.4 消息连接示例（id 匹配是关键）

```python
ai_message = {
    "role": "assistant",
    "content": "",
    "tool_calls": [{
        "name": "get_weather",
        "args": {"location": "北京"},
        "id": "call_00_nUD2NC9QRN5Cg1GaoIkBJQ4s"
    }]
}

tool_message = {
    "role": "tool",
    "content": "今天北京天气晴朗，万里无云~",
    "tool_call_id": "call_00_nUD2NC9QRN5Cg1GaoIkBJQ4s"   # ← 与上面 id 对上
}
```

> 💡 这里的 `id` 就是**工具调用的"回执单号"**：模型发出请求（带 id）→ 执行方返回结果（带同一个 id）→ 框架靠 id 配对，确保结果不会串到别的调用上。这正是 hello-agents 里 Function Calling / ReAct 循环的底层消息格式；learn Claude Code 第五章提到的"tool_result 回带 ID"也是同一件事。

---

## 1.6 本章总结

1. **统一初始化**：`init_chat_model()` 是 LangChain 1.x 推荐写法，`"provider:model"` 或 `model` + `model_provider` 两种等价写法，实现模型与代码解耦。
2. **六种调用**：`invoke / ainvoke / stream / astream / batch / abatch`，按"是否阻塞 + 是否流式 + 是否批量"选择；`batch` 更快但仍是同步阻塞接口，异步要用 `abatch`。
3. **额外参数**：`model_kwargs` 放"模型支持但框架没列"的字段；`extra_body` 放"厂商基于 OpenAI 协议扩展"的私有字段（如 DeepSeek 的 `thinking`）。
4. **LangSmith**：LangChain 生态的可观测平台，提供 tracing / monitoring / debug / evaluate 四大能力，是排查 Agent 多步链路的刚需。
5. **消息体系**：AIMessage 特有 `response_metadata`（元数据，如 token 用量）和 `tool_calls`（工具调用，可多个）；ToolMessage 必须紧邻对应 AIMessage 且 `tool_call_id` 与 `tool_calls[].id` 一致。

### 🔗 与主线的衔接
- **Agent 底层 = 消息列表 + 工具调用**：本章的 `tool_calls` / `tool_call_id` 就是 hello-agents 各章"工具调用回路"的框架实现；
- **LangGraph 的地基**：hello-agents 第六章学过的 LangGraph（图式状态机）正是构建在 LangChain 的消息与模型抽象之上的。

---
## 习题自检
- `init_chat_model()` 相比直接 `ChatOpenAI(...)` 的优势是什么？
- `batch()` 和 `abatch()` 的本质区别？（答：batch 内部并发但同步阻塞线程；abatch 异步，等待期间事件循环可处理其他任务）
- 模型支持但 LangChain 未列出的字段放哪？厂商私有扩展字段放哪？（答：`model_kwargs` / `extra_body`）
- 为什么 ToolMessage 必须带 `tool_call_id`？（答：与 AIMessage 的 tool_calls[].id 配对，保证结果不串号）
