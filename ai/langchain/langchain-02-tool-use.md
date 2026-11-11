# LangChain（二）工具调用（Tool Use）

> 学习日期：2026-10-08
> 课程：LangChain 1.x 入门（工具层 / Tool Calling）
> 核心主题：如何用 `@tool` 装饰器与 `StructuredTool` 定义工具、工具的 schema 生成与控制、为什么需要绑定工具、`bind_tools()` 的用法、`tool_calls` 与 `ToolMessage` 的完整回路，以及最省心的 `create_agent` 预置 Agent（框架自动跑「模型决策 → 执行工具 → 结果回灌」循环）。
> 定位：接续《LangChain（一）模型调用与消息体系》——第一章解决了「怎么跟模型说话」，本章解决「怎么让模型动手」；也是 hello-agents 第七章「万物皆为工具」与 learn Claude Code 工具调用回路在 LangChain 里的落地版本。

---

## 2.1 是什么：工具调用（Tool Use / Function Calling）

**工具调用** = 让 LLM 不只是「生成文本」，而是能**输出一个结构化的调用请求**（调哪个工具、传什么参数），由外部代码执行后再把结果喂回模型。

关键心智模型（务必记住）：

> **模型本身不会执行任何工具**。它只负责「提议」——产出一段结构化 JSON（工具名 + 参数）；
> 真正**执行**的是你的代码，执行结果再以 `ToolMessage` 的形式回到对话里，供模型继续推理。

所以「Tool Use」本质上是三段式回路：

```
用户问题 → 模型决策（产出 tool_calls，不执行） → 应用执行工具 → ToolMessage 回灌 → 模型基于结果作答
```

> 💡 这和 hello-agents 里的 Function Calling / ReAct 循环、learn Claude Code 第二章的「提议 → 权限 → 执行 → 结果回灌」是同一套东西，只是 LangChain 把它封装成了标准接口。

---

## 2.2 定义工具的两种方式

### 2.2.1 方式一：`@tool` 装饰器（推荐，最简洁）

把普通 Python 函数变成 LangChain 工具，**函数名即工具名，docstring 即工具描述，类型注解即参数 schema**：

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气情况。

    Args:
        city: 城市名称，例如「杭州」
    """
    return f"{city}今天晴，25℃"
```

要点：
- **docstring 是刚需**——它就是喂给模型的「工具描述」，模型靠它判断「什么时候该用这个工具」（描述写得含糊，模型就选错工具）；
- **类型注解是刚需**——LangChain 靠它生成参数的 JSON Schema（`Args:` 段落里的说明也会被提取）；
- 返回值统一建议转成 `str`（结构化数据用 `json.dumps`），因为最终要进上下文。

### 2.2.2 方式二：`StructuredTool`（需要精细控制时）

当工具的参数不止一两个、需要更严格的字段约束时，用 Pydantic 定义入参模型，再用 `StructuredTool` 组装：

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    city: str = Field(description="城市名称")
    unit: str = Field(default="celsius", description="温度单位：celsius 或 fahrenheit")

def get_weather(city: str, unit: str = "celsius") -> str:
    ...

weather_tool = StructuredTool.from_function(
    func=get_weather,
    name="get_weather",
    description="查询指定城市的天气",
    args_schema=WeatherInput,
)
```

> 选择原则：**能用 `@tool` 就别上 `StructuredTool`**；只有当参数复杂（嵌套对象、强校验、默认值语义）或需要动态构造工具时才用后者。

### 2.2.3 工具底层结构（拆开看）

无论哪种方式，最终都归一成一个 **`BaseTool`** 对象，核心字段：

| 字段 | 含义 | 作用 |
|------|------|------|
| `name` | 工具名 | 模型靠它指定「调哪个」 |
| `description` | 工具描述 | 模型靠它判断「要不要调」 |
| `args_schema` | 参数 Schema（Pydantic） | 模型靠它知道「参数长什么样」 |
| `func` / `coroutine` | 同步/异步实现 | 真正执行的代码 |

> 💡 这三个字段（name / description / schema）正是 learn Claude Code 第二章讲的「工具定义三要素」，LangChain 把它们做成了自动生成——你写 Python 函数，框架替你翻译成模型能看懂的说明书。

### 2.2.4 查看与调试工具的 schema

```python
print(weather_tool.name)          # get_weather
print(weather_tool.description)   # 查询指定城市的天气情况。
print(weather_tool.args_schema.model_json_schema())  # 参数 JSON Schema
print(weather_tool.args)          # {'city': {'title': 'City', 'type': 'string'}}
```

**为什么必须会看 schema**：模型选错工具 / 参数传错，八成是 schema 或 description 写得有问题——**排查工具调用问题，第一步永远是打印 schema**。

---

## 2.3 为什么要「绑定工具」

### 2.3.1 模型 API 层的本质：调用时多传一个 `tools` 参数

从 OpenAI 协议看，一次带工具的请求长这样：

```json
{
  "model": "...",
  "messages": [...],
  "tools": [
    {"type": "function", "function": {"name": "get_weather", "description": "...", "parameters": {...}}}
  ]
}
```

也就是说：**工具说明书是「跟着每一次请求」发给模型的**——模型不是天生知道你有哪些工具，而是每次调用时被告知。

于是 LangChain 的 `bind_tools()` 干的事就很好理解了：

> **`bind_tools()` = 把工具定义「预绑定」到模型对象上，之后每次 `invoke` 都自动带上 `tools` 参数。**

```python
model_with_tools = model.bind_tools([get_weather, get_news])
```

### 2.3.2 绑定后会发生什么（关键行为）

`model_with_tools.invoke(...)` 返回的是一个 **`AIMessage`**，此时有两种可能：

1. **模型认为不需要工具** → `content` 是正常文本，`tool_calls` 为空；
2. **模型决定调用工具** → `content` 通常为空字符串，**`tool_calls` 里带着结构化调用请求**：

```python
ai_msg.tool_calls
# [
#   {'name': 'get_weather', 'args': {'city': '杭州'},
#    'id': 'call_00_xxx', 'type': 'tool_call'},
# ]
```

> ⚠️ **这里模型并没有真的查天气**！它只是「说了一声要查」，并且把回执单号（`id`）也开好了。
> 执行是**下一步、你自己的代码**要做的事。

### 2.3.3 绑定的几点注意事项

- **可重复绑定/追加**：需要按场景给不同工具集时，可以重新 `bind_tools`（每次绑定生成的是新的 runnable，不会污染原模型对象）；
- **`tool_choice` 可控制策略**：`"auto"`（默认，模型自定）、`"any"` / `"required"`（必须调工具）、指定工具名（强制调某个）；
- **工具数量别太多**：工具越多，schema 占用的上下文越大、模型选错的概率越高——这就是 hello-agents 第九章说的**「最小可行工具集（MVTS）」**问题；
- **name / description 要「人类工程师也能一眼分得清」**：如果你自己都说不准该用哪个工具，别指望模型判断得比你准。

---

## 2.4 完整回路：手动执行工具 + ToolMessage 回灌

LangChain **不会**自动帮你执行工具（除非用后面的 `create_agent`）。手动回路的四步：

```python
from langchain_core.messages import HumanMessage, ToolMessage

messages = [HumanMessage("杭州天气怎么样？")]

# ① 模型决策：产出 tool_calls（不执行）
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

# ② 应用执行：遍历 tool_calls，找到工具并调用
tool_map = {t.name: t for t in [get_weather, get_news]}
for tool_call in ai_msg.tool_calls:
    result = tool_map[tool_call["name"]].invoke(tool_call["args"])
    # ③ 结果回灌：包装成 ToolMessage，tool_call_id 必须与调用 id 一致
    messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

# ④ 模型基于工具结果生成最终回答
final = model_with_tools.invoke(messages)
print(final.content)   # 「杭州今天晴，25℃……」
```

### 关键规则（与第一章呼应）

- **`ToolMessage.tool_call_id` 必须与 `AIMessage.tool_calls[].id` 一一对应**——这是「回执单号」，配不上就会报错（框架靠它保证结果不串号）；
- **一次 `AIMessage` 可以带多个 `tool_calls`** → 循环里要全部执行并各回一条 `ToolMessage`；
- `ToolMessage` 还有一个 `name` 字段（工具名），虽然主要靠 id 配对，但显式写上更利于调试与 tracing。

> 💡 手动写这四步会很啰嗦——这正是 `create_agent` 存在的意义。

---

## 2.5 用 `create_agent` 一步到位（推荐做法）

LangChain 提供预置 Agent，**内置「模型决策 → 执行工具 → 结果回灌 → 再决策」的循环**，直到模型不再调用工具为止：

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,                      # 或 "deepseek:deepseek-v4-flash" 字符串
    tools=[get_weather, get_news],
    system_prompt="你是一个乐于助人的助手。",
)

result = agent.invoke({"messages": [HumanMessage("杭州天气怎么样？帮我查一下最新的科技新闻")]})
print(result["messages"][-1].content)
```

要点：
- 入参/出参都是 **`messages` 列表**（出参里包含完整的中间消息：HumanMessage → AIMessage(tool_calls) → ToolMessage(×N) → AIMessage(最终回答)）；
- 想流式：`agent.stream(...)`，逐节点吐出中间过程，方便做「工具调用直播」效果；
- **框架替你做的事**：解析 `tool_calls` → 匹配工具 → 执行 → 生成 `ToolMessage` → 追加 → 再次调用模型 → 判断是否还要继续（这正是我们 2.4 手写的那一套，只不过做成了循环 + 容错）；
- 想加记忆/持久化/人工审批（HITL），是在 `create_agent` 基础上挂 **checkpointer / middleware** 实现（后续章节内容）。

### `create_agent` vs 手动回路，怎么选

| 场景 | 建议 |
|------|------|
| 常规 Agent / 快速原型 | ✅ `create_agent`：省掉样板代码，自带循环与容错 |
| 需要精细控制（自定义审批、非标准循环、特殊中断逻辑） | 手动回路或将 `create_agent` 拆开定制（middleware） |
| 只想「单次调用模型让它产出 tool_calls」，执行交给别的系统 | ✅ `bind_tools` + 手动回路 |

---

## 2.6 常见坑与排查清单

| 现象 | 大概率原因 | 排查动作 |
|------|-----------|---------|
| 模型从不调用工具 | description 太含糊 / 没 bind_tools | 打印 `tool.description`，检查是否 `bind_tools` |
| 工具选错 | 工具职责重叠、命名不清 | 收敛工具集，让 name/description 互不重叠 |
| 参数传错/缺字段 | 类型注解缺失或类型不对 | 检查 `args_schema.model_json_schema()` |
| 报错「tool_call_id 不匹配」 | `ToolMessage` 没带对应 id | 用 `tool_call["id"]` 而不是自己编 |
| 上下文被工具 schema 撑爆 | 工具太多 | 精简工具集（MVTS），或按场景动态绑定 |
| 工具报错导致整个循环崩 | 工具内部没做异常处理 | 工具内部 try-except，返回错误文本让模型自己纠偏 |

---

## 2.7 本章总结

1. **工具调用的本质**：模型只「提议」，不执行；执行在应用侧，结果靠 `ToolMessage` 回灌——三段式回路。
2. **定义工具两种方式**：`@tool`（首选，函数名/docstring/类型注解三要素自动生成）+ `StructuredTool`（参数复杂或需动态构造时用）。
3. **名字/描述/schema 是工具的三张名片**：写不清 → 模型选错工具、传错参数；**排查工具问题第一步就是打印 schema**。
4. **`bind_tools()`**：本质是把工具的 JSON Schema 预绑定到模型，让每次 invoke 自动带上 `tools` 参数；绑定后返回的 `AIMessage` 可能带 `tool_calls`。
5. **手写回路四步**：invoke（拿 tool_calls）→ 找工具执行 → `ToolMessage(tool_call_id=...)` 回灌 → 再 invoke 出最终回答。
6. **`create_agent`**：把这套循环封装成开箱即用的 Agent，入出参都是 `messages`，适合绝大多数场景；要审批/记忆/持久化再挂 middleware / checkpointer。

### 🔗 与主线的衔接
- **hello-agents 第七章「万物皆为工具」**：Memory、RAG 在 LangChain 里同样是「挂到 Agent 上的工具」，本章的 `@tool` 就是把任意能力包装成工具的通用手法；
- **hello-agents 第九章「上下文工程」**：工具的 name/description/schema 会常驻上下文，工具集臃肿 = 直接吃掉注意力预算 → MVTS 与「渐进式披露」正是解药；
- **learn Claude Code 第二章 / 第五章**：本章的 `tool_calls` → 执行 → `tool_result`（含 id 回带）与 Claude Code 的工具调用回路完全同构，区别只在封装层级。

---

## 习题自检
- 模型收到 `tools` 后会「执行」工具吗？（答：不会，只输出结构化调用请求 `tool_calls`，执行在应用侧）
- `@tool` 装饰器下，哪三样东西决定了工具能否被正确调用？（答：函数名 name、docstring description、类型注解 args_schema）
- `bind_tools()` 到底绑定了什么？（答：把工具的 JSON Schema 绑定到模型对象，使后续每次 invoke 自动携带 tools 参数）
- `ToolMessage` 里最不能省的字段是什么？（答：`tool_call_id`，必须与 `AIMessage.tool_calls[].id` 一致）
- 什么时候用 `create_agent`，什么时候该手写回路？（答：常规场景用 create_agent；需精细控制审批/中断/非标准循环时手写或定制 middleware）
