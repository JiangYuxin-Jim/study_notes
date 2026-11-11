# LangChain（三）结构化输出（Structured Output）

> 学习日期：2026-10-08
> 课程：LangChain 1.x 入门（输出层 / Structured Output）
> 核心主题：为什么要让模型「按格式说话」、三种落地方式（`with_structured_output` / `ToolStrategy` / Pydantic 校验）、Schema 设计要点、常见报错与兜底策略。
> 定位：接续《LangChain（二）工具调用》——工具调用解决「模型怎么动手」，结构化输出解决「模型怎么按你要的形状说话」。这两个能力是同一个底层机制（Function Calling）的两面。

---

## 3.1 为什么需要结构化输出

自由文本对机器不友好：

```
「好的，订单号是 A1234，预计 3 天后送达，金额 89 元。」
```

你想要的是：

```json
{"order_id": "A1234", "eta_days": 3, "amount": 89}
```

典型场景：
- **数据抽取**：从一段自然语言里抽出实体、字段（合同、简历、工单）；
- **分类/路由**：把用户问题打上标签（`intent: "退款"`），交给下游分支处理；
- **Agent 内部决策**：让模型输出「下一步做什么」的结构化指令；
- **API 填充**：模型输出直接作为函数参数 / 数据库写入的值。

> 💡 核心价值：**把非确定性的自然语言，收敛成确定的、可校验的、可编程的数据结构**。

---

## 3.2 底层机制：还是 Function Calling

**关键认知**：结构化输出并不是什么新魔法——底层就是让模型「调用一个虚拟工具」，而这个工具的参数 schema 就是你要的输出结构。

```
普通工具调用：   模型 → tool_calls: {"name": "get_weather", "args": {...}}
结构化输出：     模型 → tool_calls: {"name": "ExtractedInfo", "args": {...}}  ← 你只取 args
```

所以：
- **工具调用**与**结构化输出**共享同一套「提议 JSON」的能力；
- 区别在于：前者你会真的去**执行**那个工具，后者你只把参数**当成结果收下**。

> 💡 这是第二章之后最值得记的一句：**「让模型输出 JSON」的工程化做法，本质是给它一个只有参数没有实现的工具。**

---

## 3.3 方式一：`with_structured_output()`（首选）

### 3.3.1 最小示例

```python
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

class OrderInfo(BaseModel):
    """订单信息"""
    order_id: str = Field(description="订单号")
    eta_days: int = Field(description="预计送达天数")
    amount: float = Field(description="订单金额（元）")

model_structured = model.with_structured_output(OrderInfo)

result = model_structured.invoke([
    HumanMessage("订单 A1234，预计 3 天后送达，金额 89 元")
])
# result 是一个 OrderInfo 实例，不是字符串！
print(result.order_id, result.eta_days, result.amount)
# A1234 3 89.0
```

要点：
- 传 **Pydantic 模型**进去，**出来直接是实例**（不是 dict、不用 `json.loads`）；
- **每个字段都要写 `description`**——它就是模型看到的那个「字段说明书」，跟工具参数的 args_schema 是同一件事；
- 传 dict / TypedDict 也可以，但 Pydantic 能用 `Field` 做校验和约束，优先用它。

### 3.3.2 Schema 设计要点

| 要点 | 做法 | 为什么 |
|------|------|--------|
| 字段描述要具体 | `Field(description="订单号，形如 A1234")` | 描述越具体，抽取越准 |
| 用枚举收窄取值 | `Literal["退款", "换货", "咨询"]` | 避免模型自由发挥造标签 |
| 必填 vs 可选 | 允许缺失的用 `Optional[...] = None` | 否则模型会硬编一个值（幻觉） |
| 嵌套结构 | 用嵌套 Pydantic 模型 | 支持复杂对象（如 `List[Item]`） |
| 别过度嵌套 | 层级控制在 2–3 层 | 太深模型容易漏字段 |

**用 `Literal` 做分类的典型写法**：

```python
from typing import Literal

class Classify(BaseModel):
    """用户意图分类"""
    intent: Literal["退款", "换货", "物流查询", "其他"] = Field(description="用户意图类别")
    confidence: float = Field(description="置信度 0-1")
```

### 3.3.3 结构化输出与工具调用能共存吗？

可以——但要注意**同一个模型对象上两者有竞争关系**：如果 schema 叫得比工具还「像工具」，模型可能误调真工具。实践建议：
- **任务单一化**：要么这一轮做结构化抽取，要么这一轮做工具决策，别在同一个 prompt 里既要又要；
- 确实要混用时，把结构化输出的 schema 描述写得**明显不像可执行工具**（比如名字用 `ExtractedData`、描述写「用于承载从用户输入提取的信息」）。

---

## 3.4 方式二：`ToolStrategy` / 基于工具的方式

当你的 LangChain 版本或模型后端对 `with_structured_output` 支持不完整时，可以退到「自己造一个工具，然后强制/引导模型调用它」：

```python
from langchain_core.tools import tool

@tool
def extract_order_info(order_id: str, eta_days: int, amount: float) -> str:
    """从用户输入中提取订单信息。"""
    return "ok"

model_with_tool = model.bind_tools([extract_order_info], tool_choice="extract_order_info")
ai_msg = model_with_tool.invoke("订单 A1234，预计 3 天后送达，金额 89 元")
print(ai_msg.tool_calls[0]["args"])   # {'order_id': 'A1234', 'eta_days': 3, 'amount': 89}
```

对比：
- **`tool_choice="extract_order_info"`** 强制模型必须调这个工具 → 稳定拿到结构化参数；
- 这就是第二章 `bind_tools` 的直接复用，也是理解「结构化输出底层是 Function Calling」的最直观看法；
- 代价是要自己处理 `tool_calls` 的解析（比 `with_structured_output` 多一层胶水）。

> 有的课程/版本里这会被称为 **ToolStrategy**：即「用一个只定义 schema、不真正执行业务的工具」来承载输出结构。

---

## 3.5 校验、失败与兜底

### 3.5.1 为什么会失败

- 模型输出的 JSON **不符合 schema**（漏字段、类型错、枚举值非法）；
- 模型**不调工具**而是直接回自然语言（尤其 prompt 含糊时）；
- 字段语义模糊导致**抽错值**（不是格式问题，是理解问题）。

### 3.5.2 兜底策略（按性价比排序）

1. **加校验器**：Pydantic 的 `field_validator` / `model_validator` 拦住非法值，报错信息本身就可以反馈给模型重试；
2. **重试**：LangChain 支持对结构化输出配置重试（部分封装带 `max_retries` 语义），失败时把校验错误回灌让模型自我纠正；
3. **收窄 schema**：能用 `Literal` 就别用自由 `str`，能必填就别留一堆 `Optional`；
4. **给示例（few-shot）**：在 prompt 里给一条「输入 → 期望 JSON」，比反复描述字段有效得多；
5. **降级兜底**：极端情况退回「让模型输出 JSON 字符串 + 自己 `json.loads` + 失败重试」的土办法，虽然丑但可控。

> ⚠️ 工程意识：**结构化输出的失败率不为零**，生产环境必须设计兜底分支（重试、默认值、人工兜底），不能假设「一定成功」。

---

## 3.6 本章总结

1. **目的**：把自由文本收敛成可校验、可编程的数据结构（抽取 / 分类 / 路由 / API 填充）。
2. **底层**：结构化输出 = Function Calling 的变体——给模型一个「只有参数、没有实现」的虚拟工具，只取 `args`。
3. **首选方式**：`model.with_structured_output(PydanticModel)`，进出都是强类型对象，不用手动解析 JSON。
4. **Schema 设计**：字段 description 要具体、用 `Literal` 收窄分类、`Optional` 标注可缺失、嵌套不超过 2–3 层。
5. **备用方式**：`bind_tools([...], tool_choice="xxx")` 强制模型调你定义的抽取工具，自己解析 `tool_calls`。
6. **必须兜底**：校验器 + 重试 + 收窄 schema + few-shot；不要假设一定会成功。

### 🔗 与主线的衔接
- **与第二章同源**：`tool_calls` 是两者共同的血脉；理解了工具调用，结构化输出就是「不执行、只收参数」。
- **对 Agent 的意义**：Agent 的「规划输出」「路由决策」几乎都靠结构化输出落地——这也直接引出本章兄弟篇《Agent 与 AgentExecutor》。
- **hello-agents 第七章**：「万物皆为工具」在输出侧的反面应用——**把「输出」也包装成一个工具**，统一了输入与输出的抽象。

---

## 习题自检
- 结构化输出的底层机制是什么？（答：Function Calling——让模型调用一个只有 schema、无实现的虚拟工具，只取 args）
- `with_structured_output` 的返回值是什么类型？（答：直接是传入的 Pydantic 模型实例，不是字符串/dict）
- 想限制分类只取固定几个值时用什么？（答：`Literal[...]` / Enum 字段）
- 为什么字段最好都写 `description`？（答：它就是模型看到的字段说明书，直接决定抽取准确率）
- 结构化输出失败怎么兜底？（答：Pydantic 校验器 + 重试 + 收窄 schema + few-shot + 降级解析）
