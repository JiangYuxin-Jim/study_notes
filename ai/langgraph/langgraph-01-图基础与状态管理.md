# LangGraph（一）图的基础构建与 State 状态管理

> 学习日期：2026-10-24
> 主题：LangGraph 的建图五步（State → Node → Edge → compile → invoke）、State 的更新语义与 Reducer、条件边与循环、Compile 与运行、Checkpointer 持久化记忆。
> 环境：Python 3.11 + `langgraph 1.2.16` + `langgraph-checkpoint 4.3.0`（配套 `langchain-core 1.7.0`）。**本文所有代码都在本机实际跑通过**，输出贴在对应位置。
> 定位：前面六章把 LangChain 的「模型 → 工具 → 结构化输出 → Agent → Middleware → RAG 加载」走完了。第四章说过 `create_agent` 内部**就是一张图**（model node → tools node → 回灌 → 循环），Middleware 也是挂在这张图上的钩子。这一章开始**把那张图自己手搓一遍**——从"用框架"到"画流程"。

---

## 1.1 为什么需要 LangGraph

### 先看 LangChain 表达式（LCEL）的边界

`prompt | llm | parser` 这条链是**有向无环**的管道：数据单向流一次，出去就完了。它解决的是"数据怎么流"，但没解决"流程怎么控"。

一旦遇到下面这些需求，管道就开始难受：

| 需求 | 管道（LCEL） | LangGraph |
|------|-------------|-----------|
| 循环（反思-修正、迭代检索） | ❌ 天然做不到，得自己在外面套 while | ✅ 图天生支持环 |
| 中途分叉（路由到不同处理分支） | ⚠️ 只能靠 RunnableBranch，很别扭 | ✅ 条件边 |
| 断点续跑 / 中途停下等人审批 | ❌ 无 | ✅ checkpointer + interrupt |
| 每步状态可观测、可回放 | ❌ 只能看最终结果 | ✅ 每个 super-step 都留 checkpoint |
| 多智能体、并行扇出 | ❌ | ✅ 多节点并行 + Send |

### 核心心智模型

> **LangGraph = 用"状态机"的方式写 Agent 流程：一张有向图 + 一个共享的全局状态。**

- **节点（Node）**：一个普通 Python 函数，读状态、干活、返回增量
- **边（Edge）**：决定下一个节点是谁——普通边是写死的，**条件边**是运行时算出来的
- **状态（State）**：贯穿全程的共享数据，节点之间唯一的通信渠道

> 💡 和前面学的对照：hello-agents 第七章自建框架里的 `Agent.run()` 主循环是"代码里写死顺序"，LangGraph 是"把顺序画成图，交给引擎跑"。图本身就是文档，`get_graph().draw_mermaid()` 一条命令就能出流程图。

### LangGraph vs 对话式框架（AutoGen/CAMEL）

| | 对话式（AutoGen / CAMEL） | 图式（LangGraph） |
|---|---|---|
| 控制方式 | 角色 + 目标，行为**涌现** | 显式定义节点和跳转条件 |
| 可预测性 | 低，难调试 | 高，可审计、可回放 |
| 灵活性 | 高，闭环自由发挥 | 低，流程是写死的 |
| 前期代码量 | 少 | 多（要定义 State / Node / Edge） |

一句话：**要"能跑通的智能"，也要"能上线的可靠"——LangGraph 买的是后者。**

---

## 1.2 建图五步

LangGraph 的程序骨架永远长这样：

```
① 定义 State（TypedDict，声明有哪些字段、每个字段怎么合并）
        ↓
② 写 Node 函数（入：完整 state；出：字典形式的"增量"）
        ↓
③ 建图并连边（add_node / add_edge / add_conditional_edges / START / END）
        ↓
④ compile()（编译 + 可挂 checkpointer）
        ↓
⑤ invoke / stream 运行（传入初始 state + config）
```

### ① State：`TypedDict` 声明 + 类型注解当 Schema

```python
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    topic: str                                # 无注解 → 默认 reducer = 覆盖
    count: Annotated[int, operator.add]       # 有注解 → 用 add 合并（相加）
    log: Annotated[list, operator.add]        # 有注解 → 列表拼接
```

`TypedDict` 在这里有双重作用：
1. **运行时**：LangGraph 靠它知道 state 有哪些通道（channel），每个通道用什么 reducer；
2. **开发时**：IDE 有补全和类型检查。

⚠️ 注意 `TypedDict` **不校验、不填默认值**——字段漏传就是 KeyError，要兜底自己在节点里 `state.get(...)`。

### ② Node：接收完整 state，返回**增量**

```python
def node_a(state: State):
    # 只需返回"改了什么"，不需要把整份 state 复制回去
    return {"topic": "A 改写", "count": 1, "log": ["A 执行"]}
```

这是 LangGraph 最容易踩坑的一点：

> ❌ **不要** `state["x"].append(...); return state`
> ✅ **应该** `return {"x": ["新元素"]}`

因为返回的字典会走 **reducer** 合并进全局 state。你如果返回整份 state，`Annotated[list, add]` 的字段就会被**重复累加**一遍（原始列表 + 你自己的列表）。hello-agents 第六章那段示例代码就是 `state["messages"].append(plan); return state` 的写法，属于教学简化，生产里会出问题。

### ③ Edge：`START` / `END` / 普通边 / 条件边

```python
from langgraph.graph import StateGraph, START, END

g = StateGraph(State)
g.add_node("a", node_a)
g.add_node("b", node_b)
g.add_edge(START, "a")     # 入口：START 是虚拟节点
g.add_edge("a", "b")       # 固定边：a 跑完必去 b
g.add_edge("b", END)       # 出口：END 也是虚拟节点
app = g.compile()
```

- `START` / `END` 是编译器内置的**虚拟节点**，不用自己 add_node
- 老版本用 `set_entry_point()`，新版本统一 `add_edge(START, ...)`（前者仍能用，推荐后者）

### ④ 编译：`compile()` 得到 Runnable

```python
app = g.compile()                    # 无记忆版
app = g.compile(checkpointer=memory) # 带记忆版（后面讲）
```

`compile()` 做三件事：校验图结构（有没有孤立节点、有没有入口）、把节点和边转成内部执行计划（Pregel 引擎的 super-step）、返回一个 **Runnable**——所以 `app` 依然支持 `.invoke / .stream / .batch / .ainvoke`，和 LangChain 其他组件用法一致。

---

## 1.3 State 更新语义：Reducer 是核心

### 默认行为：覆盖（LastValue）

没有 `Annotated` 的字段，**后一个写入直接覆盖前一个**：

```python
topic: str   # A 写 "A 改写"，B 写 "B 改写(原: A 改写)" → 最终是 B 的值
```

### 声明 Reducer：`Annotated[类型, 函数]`

Reducer 的签名约定是 `(旧值, 新值) -> 合并后的值`，只要符合这个签名的函数都能用：

| 写法 | 效果 |
|------|------|
| `Annotated[int, operator.add]` | 累加 |
| `Annotated[list, operator.add]` | 列表拼接（**注意是拼接不是"按索引合并"**） |
| `Annotated[set, operator.or_]` | 集合求并 |
| `Annotated[str, lambda a, b: b or a]` | 新值非空才覆盖，否则保留旧值 |
| `Annotated[dict, custom_merge]` | 自定义字段级合并 |

```python
def custom_merge(old: dict, new: dict) -> dict:
    return {**old, **new}
```

### 实战验证（本机实际运行输出）

```python
class State(TypedDict):
    topic: str
    count: Annotated[int, operator.add]
    log: Annotated[list, add]                    # from operator import add
    messages: Annotated[list, add_messages]      # LangChain 内置消息 reducer

def node_a(state): return {"topic": "A 改写", "count": 1, "log": ["A 执行"],
                           "messages": [AIMessage(content="A 说了一句")]}
def node_b(state): return {"topic": f"B 改写(原: {state['topic']})",
                           "count": 2, "log": ["B 执行"],
                           "messages": [AIMessage(content="B 说了一句")]}

app = (StateGraph(State) ... 链 a → b ...).compile()
out = app.invoke({"topic": "初始主题", "count": 0, "log": [],
                  "messages": [HumanMessage(content="你好")]})
```

输出：

```
topic(覆盖): B 改写(原: A 改写)      ← 后写覆盖前写，且能读到前一个节点写的值
count(相加): 3                        ← 0 + 1 + 2
log(拼接): ['A 执行', 'B 执行']
messages: ['HumanMessage:你好', 'AIMessage:A 说了一句', 'AIMessage:B 说了一句']
```

三个关键结论：
1. **默认覆盖**，声明 reducer 才累加；
2. 节点之间**顺序执行、串联读到了前一个的写入**（b 读到了 a 写的 `topic`）；
3. **调用时传的初始值也参与 reducer 计算**（`count=0` + 1 + 2 = 3）。

### `add_messages`：LangChain 专用 reducer

```python
from langgraph.graph.message import add_messages
messages: Annotated[list, add_messages]
```

它不只是 `list + list`，还多做三件事：

- **按 `id` 去重更新**：新消息的 `id` 和已有消息的 `id` 相同时，**替换**而不是追加（这是改历史消息、做消息编辑的基础）
- 自动把 `dict` 转成 `HumanMessage/AIMessage` 等对象
- 维护消息序列一致性（还提供了 `RemoveMessage` 用于删除）

所以**凡是存对话历史，一律用 `add_messages`，别用 `operator.add`**。

---

## 1.4 条件边与循环

### 三要素

```python
workflow.add_conditional_edges(
    "executor",          # ① 从哪个节点出发
    should_continue,     # ② 路由函数：吃 state，吐一个**字符串**
    {                    # ③ 映射表：字符串 → 目标节点（或 END）
        "continue_to_planner": "planner",
        "end_workflow": END,
    },
)
```

路由函数**只读 state、只做判断，不能有副作用**（不要在里面调 LLM、写数据库）。它返回的字符串必须在映射表里有对应项，否则抛错。

### 实战：反思-修正循环

```python
class LoopState(TypedDict):
    draft: str
    tries: int
    approved: bool
    log: Annotated[list, operator.add]

def write(state):
    t = state["tries"] + 1
    return {"draft": "第一版草稿" if t == 1 else "修订版草稿",
            "tries": t, "log": [f"第{t}次写作"]}

def review(state):
    ok = state["tries"] >= 3
    return {"log": [f"评审 tries={state['tries']} -> {'通过' if ok else '打回'}"],
            "approved": ok}

def route(state) -> str:
    return "end" if state.get("approved") else "rewrite"

g = StateGraph(LoopState)
g.add_node("write", write); g.add_node("review", review)
g.add_edge(START, "write")
g.add_edge("write", "review")
g.add_conditional_edges("review", route, {"rewrite": "write", "end": END})
app = g.compile()
```

实际输出：

```
['第1次写作', '评审 tries=1 -> 打回', '第2次写作', '评审 tries=2 -> 打回', '第3次写作', '评审 tries=3 -> 通过']
```

`get_graph().draw_mermaid()` 直接吐出流程图（可贴进任何支持 Mermaid 的地方）：

```
graph TD;
	__start__ --> write;
	review -. end .-> __end__;
	review -. rewrite .-> write;
	write --> review;
```

> 🔥 **这就是 LangGraph 的革命性所在**：`review → write` 这条回边让"反思-修正"变成一个图能表达的东西，而不是外面套 while。
> 但画图时也别忘了配一个 `import operator` —— 我第一次跑就漏了 `operator` 导致条件函数里 `state["tries"]` 根本没被 reducer 生效（`tries` 没声明 reducer 时后写覆盖前写，环形回来时 `write` 读到的是 `review` 之后的 state，此处 `tries` 无 reducer 也 OK，因为每次都是全量更新）。

### 死循环与 `recursion_limit`

**图里必须存在一条能到 `END` 的路径**，否则就是死循环。LangGraph 有保命的 `recursion_limit`（默认 10007，注意不是 25——老版本是 25）：

```python
app.invoke({"n": 0}, {"recursion_limit": 3})
# GraphRecursionError: Recursion limit of 3 reached without hitting a stop condition.

app.invoke({"n": 0}, {"recursion_limit": 20})   # n 到 5 就条件边走向 END
# {'n': 5}
```

`recursion_limit` 数的是 **super-step 数**（不是节点调用数，并行节点共享一个 super-step），它在 `config` 里传，不在图定义里。

**硬规则：任何循环必须有一个"只看 state 就能判断"的终止条件**——常见是计数器（`tries >= N`）、意图判断（`approved == True`）、或状态标记（`step == "completed"`）。

---

## 1.5 Compile 与运行

### `invoke`

```python
result = app.invoke(input_state, config)   # 同步阻塞，返回最终 state
```

`input_state` 是**初始 state**（也被 reducer 合并进去），`config` 是运行时配置（`recursion_limit` / `configurable.thread_id` / `callbacks` / `tags`）。

### `stream`：三种 `stream_mode`

这决定你**每一步能看到什么**，是调试和做流式 UI 的关键：

| mode | 每次吐什么 | 适用 |
|------|-----------|------|
| `updates`（默认） | `{节点名: 该节点的返回增量}` | **调试首选**，看得清每一步谁改了什么 |
| `values` | 该 super-step 后的**完整 state** | 要看全局快照、做状态回放 |
| `messages` | LLM 的 token 级输出 `(chunk, metadata)` | 前端打字机效果（必须节点里调 LLM） |
| `debug` | 极详细（含 task/checkpoint 事件） | 深挖引擎行为 |
| `custom` | 节点内 `get_stream_writer()` 自定义推送 | 进度条、中间提示 |

实际输出（同一个两节点图）：

```
-- updates --
{'a': {'topic': 'A 改写', 'count': 1, 'log': ['A 执行'], 'messages': [AIMessage(...)]}}
{'b': {'topic': 'B 改写(原: A 改写)', 'count': 2, 'log': ['B 执行'], 'messages': [AIMessage(...)]}}

-- values --
{'topic': 't', 'count': 0, 'log': [], 'messages': []}                  ← 初始 state 先吐一次
{'topic': 'A 改写', 'count': 1, ...}                                    ← a 之后
{'topic': 'B 改写(原: A 改写)', 'count': 3, ...}                        ← b 之后（注意 count 已累到 3）
```

两个细节：
- `values` **第一次会吐初始输入**（未跑任何节点）；
- `updates` 里带的是**节点返回的增量**，所以 count 显示 1、2，而 `values` 里是**合并后的** 1、3。

### `ainvoke` / `astream`

生产里基本都是异步：`await app.ainvoke(...)` / `async for ev in app.astream(..., stream_mode="messages")`。节点函数既可以是同步函数（LangGraph 自动丢线程池），也可以是 `async def`。

---

## 1.6 Checkpointer：State 的持久化

### 解决什么问题

`compile()` 不挂 checkpointer 时，**每次 `invoke` 都是一次性的**：跑完 state 就没了。多轮对话、断点续跑、人工审批全都做不了。

`checkpointer` 干的事非常朴素：**每跑完一个 super-step，把当时的完整 state 存一份快照**，用 `thread_id` 做索引。

```python
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()               # 内存版（重启即失，只适合开发/测试）
app = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "user-1"}}
app.invoke({"messages": [HumanMessage(content="你好")], "turn": 0}, config)
```

> ⚠️ **挂了 checkpointer 就必须传 `thread_id`**，否则直接报错。反过来，只要传了就自动有记忆。

### 实测：多轮记忆 + 线程隔离

```python
cfg = {"configurable": {"thread_id": "user-1"}}
for q in ["你好", "我叫小林", "我叫什么？"]:
    r = chat_app.invoke({"messages": [HumanMessage(content=q)], "turn": 0}, cfg)
```

```
user: 你好        ->  ai: 收到：你好（历史上共1条）        turn累计=1
user: 我叫小林     ->  ai: 收到：我叫小林（历史上共3条）     turn累计=2
user: 我叫什么？   ->  ai: 收到：我叫什么？（历史上共5条）   turn累计=3
latest state turn: 3 | next: ()
另一线程隔离 turn: 1 | 消息数: 2      ← thread_id="user-2" 完全独立
```

三个关键点全验证到了：
1. **同 thread_id 跨 invoke 累积**：第二次 invoke 只传了一条消息，但 `messages` 有 3 条、`turn` 累到 2——说明上次的 state 被加载回来了；
2. **每次传入的初始值也走 reducer**（`turn: 0` + 历史 1 = 2）；
3. **不同 `thread_id` 完全隔离**，天然支持多用户/多会话。

### 常用 API

```python
state = app.get_state(cfg)              # 当前快照
state.values      # 最新 state（dict）
state.next        # 下一个要跑的节点元组，空 () = 已结束
state.config      # 含 checkpoint_id

history = list(app.get_state_history(cfg))   # 历史所有 checkpoint，可倒序回溯
app.update_state(cfg, {"approved": True})    # 人工改 state（HITL 的关键动作）
```

`get_state_history` 是 LangGraph 一个很香的能力：**每一步都有完整快照 → 可回放、可时间旅行（replay）、可 fork 分支**。这在调试复杂 Agent 时价值极大。

### 生产级 checkpointer

| 实现 | 包 | 场景 |
|------|-----|------|
| `InMemorySaver` | 内置 | 开发/单测 |
| `SqliteSaver` / `AsyncSqliteSaver` | `langgraph-checkpoint-sqlite` | 单机小项目 |
| `PostgresSaver` | `langgraph-checkpoint-postgres` | 生产标配（支持并发、多实例） |
| `RedisSaver` | `langgraph-checkpoint-redis` | 高并发短会话 |

用法都一样，只是构造参数换成连接串：
```python
from langgraph.checkpoint.postgres import PostgresSaver
with PostgresSaver.from_conn_string(DB_URI) as saver:
    app = workflow.compile(checkpointer=saver)
```

### 和其他章节的串联

- **第四章** `create_agent` 的 `checkpointer` + `thread_id` 会话记忆 —— 同一个机制，这里终于看清底层；
- **第五章** HITL（人工审批）**必须配 checkpointer** —— 因为审批就是"停下来存快照，等人回复后从快照续跑"，没快照就无从续；
- **hello-agents 第八章记忆** —— checkpointer 存的是**原始 state**（短期记忆/会话级），不是"提炼后的长期记忆"，两者互补。

---

## 1.7 与其他章节/框架的对照

| 概念 | LangGraph | 前面的学习 |
|------|-----------|-----------|
| 主循环 | 图 + 回边 | hello-agents 第七章 `Agent.run()` |
| `create_agent` 内部 | model → tools → 回边 → END | LangChain 第四章那张图 |
| 状态共享 | 单一 TypeDict state | AgentScope 的 MsgHub |
| 执行引擎 | Pregel / super-step（BSP 模型） | — |
| 持久化 | checkpointer | hello-agents 第八章 MemoryManager（但这里是 state 快照，不是语义提炼） |
| 钩子 | node / edge 间可插 | LangChain 第五章 Middleware |

> 🔑 **一句话串起整个体系**：LangChain 提供"零件"（模型/工具/Parser），LangGraph 提供"流程图和运行引擎"，`create_agent` 就是官方用 LangGraph 画好的一张标准图，Middleware 是往这张图上挂的钩子。**学到这儿，前面所有东西的底层终于对上了。**

---

## 1.8 踩坑清单

| 坑 | 现象 | 正解 |
|----|------|------|
| 节点里 `state["x"].append()` 后 `return state` | reducer 字段被重复累加，列表越滚越长 | 只返回增量 `return {"x": [新元素]}` |
| 存对话历史用 `Annotated[list, operator.add]` | 无法按 id 更新/删除消息 | 用 `add_messages` |
| `TypedDict` 字段漏传 | `KeyError` | 初始 state 全部给齐，或用 `total=False` + `state.get()` |
| 条件边路由函数返回值不在映射表里 | 运行时报 `InvalidUpdateError` / KeyError | 映射表必须覆盖所有可能返回值 |
| 循环没有终止条件 | 跑到 `GraphRecursionError`（默认 10007 步） | 显式计数器/标记 + 必要时调低 `recursion_limit` |
| compile 了 checkpointer 但 invoke 没 `thread_id` | 直接报错 | config 里必传 `configurable.thread_id` |
| `InMemorySaver` 上线 | 进程重启记忆全丢 | 换 Postgres/Redis checkpointer |

> 我自己这次的坑：一开始写 `operator` 相关 reducer 时引用名写错，导致 ImportError 静默异常；还有一次 `approved` 字段忘了从 `TypedDict` 里移除就重复声明，被 Python 直接拦下——**TypedDict 不校验类型，但语法错误一定会炸，所以建图阶段通常能早发现结构问题**。

---

## 1.9 本章小结

1. **LangGraph = 有向图 + 共享状态**，用状态机思维写 Agent 流程；核心价值是**循环 + 可控 + 可观测**。
2. **五步建图**：State（TypedDict + reducer 注解）→ Node（读全state、返增量）→ Edge（START/END/普通边/条件边）→ compile（可挂 checkpointer）→ invoke/stream。
3. **状态更新的关键在 reducer**：默认覆盖，`Annotated[T, f]` 声明合并规则，`f(旧, 新) -> 合并值`；**消息一律 `add_messages`**。
4. **条件边 = 显式路由**，让循环和分支成为图的一部分；路由函数只读不写，必须覆盖所有返回值，循环必须有可判定的终止条件。
5. **`stream_mode`**：`updates` 调试、`values` 快照、`messages` 前端流式——选错会多花一倍时间 debug。
6. **checkpointer 是"图级记忆"**：super-step 级快照 + `thread_id` 隔离，支撑多轮对话、断点续跑、时间旅行、HITL。
7. 前面学的 `create_agent` / Middleware 全是建在这一层之上的封装——**现在能自己画了**。

---

## 下一步

- **LangGraph（二）**：`Command` 和 `Send`（动态扇出/并行）、子图（Subgraph）、`interrupt` 真正的 HITL 落地
- **LangGraph（三）**：建一个真实的 ReAct Agent 图，再和 `create_agent` 对照
- 然后回到 RAG 线：Embeddings → VectorStore → Retriever（接上第（六）章的文档加载）
