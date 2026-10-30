# LangGraph · 静态扇入：或节点扇入 vs 与节点扇入

> 学习日期：2026-10-30
> 环境：本机 `langgraph 1.2.16` + `langchain-core`，全部结论由**实际运行**验证
> 承接：[LangGraph（二）· 进阶建图](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md)（`Send` 动态扇出）

---

## 一、这篇代码要回答什么

先看今天要分析的图：

```
                                     ┌─── node_b ─── node_d ───┐
START ──► node_a ────────────────────┤                         ├──► node_e ──► END
                                     └─── node_c ──────────────┘
```

`node_a` 之后分成两路（`node_b → node_d` 和 `node_c`），最后两路都要汇到 `node_e`。
**汇合处怎么写这一条边，决定了 `node_e` 会被执行几次。**

代码里给了两种写法，只差一行：

```python
# 写法一：或节点扇入关系
builder.add_edge("node_c", "node_e")
builder.add_edge("node_d", "node_e")

# 写法二：与节点扇入关系
builder.add_edge(["node_c", "node_d"], "node_e")   # ← 注意是 list
```

看起来只是"两条边"和"一条边写两个源头"的语法差别，**实际运行结果完全不同**：

| 写法 | `node_e` 执行次数 | `node_e` 拿到的状态 |
|------|------------------|-------------------|
| 或扇入（两条 `add_edge`） | **2 次** ✅ 实测 | 前一次看得到 `node_d` 的结果，后一次只看得到 `node_c` 的结果 |
| 与扇入（list `add_edge`） | **1 次** ✅ 实测 | 同时看得到 `node_c` 和 `node_d` 的结果 |

这就是本篇的核心：**扇入不是"两条线连到一个点"这么简单，它决定的是"要不要等齐"。**

---

## 二、先跑一遍看结果

### 2.1 完整可运行代码

```python
from typing import TypedDict
from loguru import logger
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

# 1. 定义状态
class EmptyState(TypedDict):
    pass

# 2. 声明节点
def node_a(state: EmptyState, config: RunnableConfig) -> EmptyState:
    cur_step = config["metadata"]["langgraph_step"]
    logger.info(f"当前步骤: {cur_step}")
    return {}

def node_b(state: EmptyState, config: RunnableConfig) -> EmptyState:
    cur_step = config["metadata"]["langgraph_step"]
    logger.info(f"当前步骤: {cur_step}")
    return {}

def node_c(state: EmptyState, config: RunnableConfig) -> EmptyState:
    cur_step = config["metadata"]["langgraph_step"]
    logger.info(f"当前步骤: {cur_step}")
    return {}

def node_d(state: EmptyState, config: RunnableConfig) -> EmptyState:
    cur_step = config["metadata"]["langgraph_step"]
    logger.info(f"当前步骤: {cur_step}")
    return {}

def node_e(state: EmptyState, config: RunnableConfig) -> EmptyState:
    cur_step = config["metadata"]["langgraph_step"]
    logger.info(f"当前步骤: {cur_step}")
    return {}

# 3. 构建图
builder = StateGraph(state_schema=EmptyState)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_node("node_c", node_c)
builder.add_node("node_d", node_d)
builder.add_node("node_e", node_e)

builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_a", "node_c")
builder.add_edge("node_b", "node_d")

# 或节点扇入关系
# builder.add_edge("node_c", "node_e")
# builder.add_edge("node_d", "node_e")

# 与节点扇入关系
builder.add_edge(["node_c", "node_d"], "node_e")

builder.add_edge("node_e", END)

graph = builder.compile()
graph.invoke({})

from IPython.display import display
display(graph)
```

### 2.2 实测输出

把 `logger.info` 换成 `print`（我们只要看执行顺序），其他一字不改，跑出来的结果：

**写法一：或扇入（两条独立 `add_edge`）**

```
[run] node_a  langgraph_step=1
[run] node_b  langgraph_step=2
[run] node_c  langgraph_step=2
[run] node_d  langgraph_step=3
[run] node_e  langgraph_step=3     ← 第一次
[run] node_e  langgraph_step=4     ← 第二次
node_e 出现次数: 2
```

**写法二：与扇入（list `add_edge`）**

```
[run] node_a  langgraph_step=1
[run] node_b  langgraph_step=2
[run] node_c  langgraph_step=2
[run] node_d  langgraph_step=3
[run] node_e  langgraph_step=4     ← 只有一次，而且推到了第 4 步
node_e 出现次数: 1
```

**关键信息全在 `langgraph_step` 上。** 下一节专门拆它。

---

## 三、读懂 `langgraph_step`：它数的是 super-step

`config["metadata"]["langgraph_step"]` 是 LangGraph 内部注入的一个元数据，**它等于"当前执行到第几个 super-step"**，从 1 开始。

### 3.1 super-step 是什么

- **一个 super-step = 一轮可并行的执行**（Pregel 模型里的 tick）
- 同一 super-step 里的节点**同时**执行（多线程 / 异步并发）
- 一个节点执行完写入 state 后，**下一个 super-step 才能看到它的结果**
- 所以 `langgraph_step` 相同的节点 = 同一个 super-step 里并行跑

### 3.2 两种写法下的步骤分解

**或扇入（两条边）**

| step | 跑的节点 | 说明 |
|------|---------|------|
| 1 | node_a | |
| 2 | node_b、node_c | node_a 分两路，并行 |
| 3 | node_d、**node_e** | node_b 完成 → node_d；**node_c 完成 → node_e 第一次** |
| 4 | **node_e** | node_d 完成 → **node_e 第二次** |

注意 step 3：`node_d` 和 `node_e` 同属一个 super-step。也就是说，**`node_e` 在 `node_d` 还在跑的时候就已经执行了第一遍**。它当时看到的 state 里只有 `node_c` 的写入，`node_d` 的结果还没进来。

**与扇入（list 边）**

| step | 跑的节点 | 说明 |
|------|---------|------|
| 1 | node_a | |
| 2 | node_b、node_c | 并行 |
| 3 | node_d | 只有这一路在动；`node_c` 完成后**在 node_e 门口等着** |
| 4 | node_e | node_c 早就到了，node_d 也到了 → **等齐，跑一次** |

**`node_e` 被推到了 step 4**——这就是"等待"的代价，也是"等待"的证明。

### 3.3 一句话口诀

> **`langgraph_step` 是扇入语义的照妖镜：**
> `node_e` 出现在**同一个 step 的不同值** → 或扇入（各自到达各自跑）；
> `node_e` 只出现**一次且 step 靠后** → 与扇入（等齐了才跑）。

---

## 四、两种扇入的机制差异

### 4.1 或扇入：`add_edge(src, tgt)` × N —— "谁到谁跑"

```python
builder.add_edge("node_c", "node_e")
builder.add_edge("node_d", "node_e")
```

**LangGraph 内部发生了什么：**

`node_e` 的入边有两条（`node_c → node_e`、`node_d → node_e`），它们是**两个独立的触发条件**。
每条边单独在自己的源节点完成后触发一次对 `node_e` 的调度。

- `node_c` 在 step 2 完成 → 触发 `node_e`，排进 step 3
- `node_d` 在 step 3 完成 → 再次触发 `node_e`，排进 step 4

两次触发 **不互相等待**，所以 `node_e` 跑了两遍。

**语义本质：这是"或"——任一路到达就执行。**

**适用场景：**

- 多路输入互斥（一条 if、一条 else），走哪条都汇合到同一个后处理
- 多个上游可能随时产出，下游应该"来一个处理一个"
- **不关心是否齐活**的场景

**⚠️ 但在这个图上用它，很可能是 bug。** 因为 `node_e` 语义上是"两路都完了之后的总汇总"，跑两遍通常不是你要的：
- 如果 `node_e` 里有副作用（写库、发消息、调 LLM），就会**重复执行两次**
- 第一次执行时 `node_d` 的结果压根不在 state 里，逻辑会出错

### 4.2 与扇入：`add_edge([src1, src2], tgt)` —— "全部到齐才跑"

```python
builder.add_edge(["node_c", "node_d"], "node_e")
```

**LangGraph 内部发生了什么：**

`add_edge` 的第一个参数**接受 list**，这时它注册的是**一条"多源汇合边"**：

- 这条边会**记录** `node_c` 和 `node_d` 两个源头
- 只有当**两个源头都在之前某个时刻完成过**，才会触发 `node_e`
- 而且触发**只触发一次**——不会因为 `node_c` 完成触发一次、`node_d` 完成又触发一次

实测正是这个结果：`node_e` 在 step 4 被调度，只跑一次，且此时 `node_c`（step 2）和 `node_d`（step 3）的结果都在 state 里。

**语义本质：这是"与"——所有输入的边都完成了才执行。**

**适用场景（这才是本图的正确写法）：**

- **并行分支的汇聚点**：几路并行统计 / 几路并行检索 / 几路并行调工具，最后汇总
- 汇总逻辑必须看到**所有分支**的结果
- 汇总节点有副作用，**只能执行一次**

### 4.3 机制对照表

| 维度 | 或扇入 `add_edge(a,t); add_edge(b,t)` | 与扇入 `add_edge([a,b], t)` |
|------|-------------------------------------|---------------------------|
| 注册的是什么 | **两条独立边** | **一条多源汇合边** |
| 触发条件 | 任一源完成 | **所有源都完成过** |
| 执行次数 | 每个源完成各触发 1 次 → **N 次** | **1 次** |
| 每次看到的状态 | 只有**当次触发路径**的写入 | **所有源**的写入 |
| 调度时机 | 最早可执行的 super-step | 最后一个源完成后的**下一个** super-step |
| 语义 | 或 | 与 |
| 本图正确用法 | ❌ 会跑两遍 | ✅ |

---

## 五、为什么 `add_edge` 能接受 list？

这是 LangGraph 里很容易被忽略的一个 API 细节。`add_edge` 的签名大致是：

```python
def add_edge(self, start_key: str | list[str], end_key: str, *, data=None) -> Self:
```

`start_key` 是 `str | list[str]`：

- **传 `str`** → 普通边，单源单目标
- **传 `list[str]`** → **多源汇合边**，所有源都完成后才触发一次目标

这跟 `add_node` / `add_edge` 平时的用法完全一致，只是没人告诉你第一个参数还能给个 list。

> **记忆锚点：`add_edge(["A","B"], "C")` = "A 和 B 都到齐了，C 才开始"。**

---

## 六、改成"有状态"的版本，看得更清楚

前面的 `EmptyState` 是空的，所以只能靠 `langgraph_step` 观察。把 state 变成有内容，差异会直接摆在脸上。

```python
from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, START, END

class S(TypedDict):
    log: Annotated[List[str], operator.add]   # ← 注意 reducer

def na(s): return {"log": ["a"]}
def nb(s): return {"log": ["b"]}
def nc(s): return {"log": ["c"]}
def nd(s): return {"log": ["d"]}

def ne(s):
    print(f"node_e 看到的 log = {s['log']}")
    return {"log": ["e"]}

def build(mode):
    b = StateGraph(S)
    for n, f in [("node_a", na), ("node_b", nb), ("node_c", nc),
                 ("node_d", nd), ("node_e", ne)]:
        b.add_node(n, f)
    b.add_edge(START, "node_a")
    b.add_edge("node_a", "node_b")
    b.add_edge("node_a", "node_c")
    b.add_edge("node_b", "node_d")
    if mode == "or":
        b.add_edge("node_c", "node_e")
        b.add_edge("node_d", "node_e")
    else:
        b.add_edge(["node_c", "node_d"], "node_e")
    b.add_edge("node_e", END)
    return b.compile()
```

**`or` 模式实测：**

```
node_e 看到的 log = ['a', 'b', 'c']           ← 第一次：node_c 到了，node_d 还没到
node_e 看到的 log = ['a', 'b', 'c', 'd', 'e'] ← 第二次：node_d 到了，还看到了自己上次写的 'e'
final: {'log': ['a', 'b', 'c', 'd', 'e', 'e']}
```

两个关键观察：

1. **第一次执行时 `'d'` 不在**——`node_d` 还没跑完。如果 `node_e` 的逻辑是"汇总 b 和 c 两路的结果"，第一次执行就是在**拿残缺数据算一个错答案**。
2. **`'e'` 出现了两次**——`node_e` 确实执行了两遍，两次的写入都进了 state。**有副作用的节点（写库 / 发消息 / 扣费 / 调 LLM）就会重复发生两遍。**

而且第二次触发时读到的是**上一个 super-step 合并后的快照**（能看到第一次写的 `'e'`），这印证了」super-step 之间才做 state 合并「这个机制。

**`and` 模式实测：**

```
node_e 看到的 log = ['a', 'b', 'c', 'd']   ← 两路都在，只跑一次
final: {'log': ['a', 'b', 'c', 'd', 'e']}
```

干净的一次汇总：`'b'`、`'c'`、`'d'` 全在，`'e'` 只有一个。

**这才是你想要的"汇总节点"。**

> ⚠️ 这里 `log` 必须用 `Annotated[List[str], operator.add]`。
> 如果你在**或扇入**下用了一个**没有 reducer** 的 key，而两个上游恰好同时写它（同 super-step），会直接抛
> `InvalidUpdateError: Can receive only one value per step`。这一点在[LangGraph（一）](./langgraph-01-图基础与状态管理.md)讲过，这里再强调一次。

---

## 七、什么时候该用哪个？（决策清单）

拿着这张图问自己：

1. **`node_e` 是不是要做"总汇总"？**（需要看到所有分支结果）
   → **与扇入** `add_edge(["node_c","node_d"], "node_e")`

2. **`node_e` 是不是"谁先来先处理谁"？**（每个上游产出独立处理）
   → **或扇入** 两条独立 `add_edge`

3. **`node_e` 有副作用吗？**（写库 / 发消息 / 调 LLM / 扣费）
   → **有就一定要与扇入**，或至少保证幂等。或扇入会跑 N 次。

4. **等待成本能接受吗？**
   → 与扇入的代价是**慢一整个 super-step**（要等最慢的那路）。如果两路耗时差异极大，且你确实不需要齐活，那或扇入才合理。

5. **两路是不是互斥的（走 A 就不走 B）？**
   → 这种情况下用**条件边**分叉更合适，而不是 `node_a` 同时连两条边。
   因为现在这个图里 `node_b` 和 `node_c` 是**并行、都必然执行**的。

---

## 八、这个图的几个隐藏陷阱

### 陷阱 1：这个图里 `node_b` 和 `node_c` 是并行，不是分支

```python
builder.add_edge("node_a", "node_b")
builder.add_edge("node_a", "node_c")     # 两条 add_edge，= 并行扇出
```

`node_a` 完成后，`node_b` 和 `node_c` **都会执行**（step 2 同时跑）。如果你本意是"二选一"，应该用：

```python
builder.add_conditional_edges("node_a", router, {"b": "node_b", "c": "node_c"})
```

**判断口诀：`add_edge` 发两次 = 并行都要跑；`add_conditional_edges` 一次 = 二选一。**

### 陷阱 2：`node_b` 比 `node_c` 多一跳

拓扑上 `node_b → node_d` 是两跳，`node_c` 是一跳。所以：
- `node_c` 在 step 2 就完事了，`node_d` 要等到 step 3
- **这就是或扇入会跑两次的直接原因**：两路完成时间不同步

**只要两路长度不同，或者两路耗时不同，或扇入就一定会重复执行。**

### 陷阱 3：`langgraph_step` 不是节点执行次数

`langgraph_step` 是 **super-step 编号**，不是"第几个节点"。
同一个 step 里可以同时跑多个节点（本例 step 2 同时跑 `node_b` 和 `node_c`）。
所以不能拿它去数节点——第一次跑的人很容易搞混。

### 陷阱 4：`EmptyState` 下的"扇入"其实什么都没汇总

`EmptyState` 里 `pass`，没有任何字段，所以两种写法在**这个空图里功能上没区别**，唯一能观测到的就是执行次数和 step。
**这恰恰是最好的教学设计**——把"扇入"这件事从"数据合并"里剥出来，纯粹看调度语义。

---

## 九、可视化：`display(graph)`

代码最后用了：

```python
from IPython.display import display
display(graph)
```

在 Jupyter / Colab / VSCode Notebook 里会**内联渲染 Mermaid 图**。

注意：**两种写法画出来的图长得几乎一样**（都是 `node_c` 和 `node_d` 各有一条线指向 `node_e`）。
光看图分辨不出是或还是与——这是最容易踩的坑：

> **图上"两条线连到同一点"看着像与扇入，实际取决于你怎么注册的：**
> - 两次 `add_edge("c","e")` + `"d","e"` → **或**（画出来一样，但语义是或）
> - 一次 `add_edge(["c","d"],"e")` → **与**（画出来一样，语义是与）
>
> **必须看代码，不能看图。**

想要更清楚的流程图可以：

```python
print(graph.get_graph().draw_mermaid())
```

输出 Mermaid 源码，可以贴到任何支持的地方。

---

## 十、完整对照总结

```
                     写法一（或扇入）              写法二（与扇入）
注册的边数                 2 条                       1 条（多源）
node_e 执行次数             2 次                       1 次
node_e 首次调度 step         3                          4
node_e 看到的 node_c          ✅                         ✅
node_e 看到的 node_d          ❌（第一次看不到）           ✅
副作用发生次数               2 次                       1 次
语义                        "谁到谁跑"                  "等齐全员"
适用                       互斥输入 / 独立处理            并行分支总汇总
```

**本图（并行两路都要喂给 `node_e` 做汇总）的正确写法：与扇入。**

```python
builder.add_edge(["node_c", "node_d"], "node_e")
```

---

## 十一、踩坑清单

| # | 坑 | 现象 | 解法 |
|---|-----|------|------|
| 1 | 用两条 `add_edge` 做汇总 | 汇总节点跑 N 次，副作用重复 | 改成 `add_edge([src...], tgt)` |
| 2 | 以为画出来的图能看出语义 | 两种写法图长一样 | 看代码注册方式，不看图 |
| 3 | 把 `add_edge("a","b")` + `("a","c")` 当分支 | 两个节点都执行了 | 分支用 `add_conditional_edges` |
| 4 | 用 `langgraph_step` 数节点个数 | 步骤号与节点数对不上 | 它是 super-step 编号，同 step 可多节点 |
| 5 | 或扇入下多个上游写同一 key | `InvalidUpdateError` | 配 `Annotated[T, reducer]`，或改与扇入 |
| 6 | 与扇入里某路走了 END | 汇合点**不等齐**照样执行（退化成或） | 退出分支返占位值 / 汇合点自校验 |
| 7 | 以为并行写入顺序固定 | 动态扇出时顺序不保证 | 需要顺序就自己 sort |

---

## 十二、自检问题

1. `add_edge(["node_c", "node_d"], "node_e")` 和两条独立 `add_edge` 在**注册层面**的区别是什么？
2. 为什么或扇入下 `node_e` 的第一次执行看不到 `node_d` 的结果？
3. `langgraph_step` 数的是什么？为什么 `node_b` 和 `node_c` 的 step 相同？
4. 与扇入为什么让 `node_e` 从 step 3 推迟到 step 4？推后这一整轮在等谁？
5. 如果 `node_e` 里要发一条消息给用户，用哪种扇入？为什么？
6. 把 `node_a` 的两条 `add_edge` 改成 `add_conditional_edges` 后，这个图里还需要扇入吗？为什么？
7. `EmptyState` 为什么让两种写法的"数据差异"看不出来？这说明扇入语义的本质是什么？

---

## 🔗 衔接

- **往回**：[LangGraph（一）](./langgraph-01-图基础与状态管理.md)——Reducer 是这里做"有状态"版本的前提。
- **往回**：[LangGraph（二）](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md)——`Send` 动态扇出；本篇是它的**静态兄弟**：路数固定用 `add_edge`，路数运行时才知道用 `Send`。
- **往前**：Subgraph 作为扇入目标（多个子图汇聚到父图节点）；`Command(goto=[...])` 在节点内部做静态并行分派。
