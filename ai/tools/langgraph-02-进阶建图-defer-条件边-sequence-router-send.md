# LangGraph（二）· 图构建进阶：defer / add_conditional_edges / add_sequence / Router / Send

> 学习日期：2026-10-25
> 环境：本机 `langgraph 1.2.16`（所有结论均为实际运行验证，非文档摘抄）
> 承接：[LangGraph（一）图基础与状态管理](./langgraph-01-图基础与状态管理.md)

---

## 一、总览：本篇在解决什么问题

第一篇讲的是**最小可用的图**：State → Node → Edge → compile → invoke。
本篇补齐"真实项目里天天要用，但第一篇没讲"的五个建图能力：

| API / 概念 | 解决什么 | 一句话 |
|-----------|---------|--------|
| `add_sequence` | 一串线性节点写太多 `add_edge` | **批量连链**，自动命名自动串边 |
| `add_conditional_edges` | 下一步不确定 | **路由分叉**（本篇重点） |
| **Router**（路由函数） | 上面那个 `path` 参数 | 决定走哪条路的**纯函数大脑** |
| `Send` | 分叉数量在运行时才知道 | **动态并行扇出**（map-reduce 的 map） |
| `defer` | 收尾工作（写报告/存库）拖慢主链 | **推迟到本次运行即将结束时才执行** |

记忆锚点：**`add_sequence` 管"直线"，`add_conditional_edges`+Router 管"岔路"，`Send` 管"分身"，`defer` 管"压轴"。**

---

## 二、add_sequence：批量连链

### 2.1 用法与实测

```python
def fetch(s): return {"steps": ["fetch"]}
def parse(s): return {"steps": ["parse"]}
def store(s): return {"steps": ["store"]}

g = StateGraph(S)
g.add_node("start_node", lambda s: {"steps": ["start"]})
g.add_sequence([fetch, parse, store])      # ← 一行顶三条边
g.add_edge(START, "start_node")
g.add_edge("start_node", "fetch")
g.add_edge("store", END)
```

实测输出 `['start', 'fetch', 'parse', 'store']`，图节点为 `['fetch','parse','start_node','store']`。

它内部做了两件事：
1. **自动命名**：没给名字就用函数 `__name__`（`fetch`/`parse`/`store`）；
2. **自动连边**：`fetch→parse→store` 三条边一次建好。

也可以显式给名字（当函数同名或是 `lambda` 时必须这么做）：

```python
g.add_sequence([("step1", fetch), ("step2", parse)])
```

### 2.2 踩坑（我实测踩到的）

```python
g.add_node("a", a); g.add_node("b", b)
g.add_sequence([a, b])
# ValueError: Node names must be unique: node with the name 'a' already exists.
```

`add_sequence` **不是"连接已有节点"，而是"注册节点 + 连成一串"**。节点已经 `add_node` 过就会撞名报错。所以它适合"一条新流水线整段加进去"的场景，不适合"把已有的散节点串起来"——后者还是老老实实写 `add_edge`。

### 2.3 深层含义：**图构建本身就是代码**

`add_sequence` 最大的价值不是省字，而是它揭示了一个事实：**建图是普通 Python 代码**。这意味着你可以：

```python
for name, fn in STEP_DEFINITIONS:      # 从配置/数据库读步骤
    g.add_node(name, fn)
g.add_sequence([STEP_DEFINITIONS[0][1], *[f for _, f in STEP_DEFINITIONS[1:]]])
```

**步骤由配置驱动，而不是写死在代码里**。这是 LangGraph 相比"手写 if-else 流程"最被低估的优势——图的形状可以是数据。

---

## 三、add_conditional_edges：条件边

### 3.1 三要素（第一篇讲过，这里补全细节）

```python
g.add_conditional_edges(
    source,      # ① 从哪个节点出来时触发
    path,        # ② 路由函数：读 state，返回 Hashable 或 Sequence[Hashable]
    path_map,    # ③ 可选：把"路由函数返回值"映射到"真实节点名"
)
```

### 3.2 `path_map` 的两种形态

```python
# 形态 1：dict —— 路由返回值是"逻辑标签"，映射到真实节点
g.add_conditional_edges("classify", lambda s: "HIGH", {"HIGH": "vip", "LOW": "normal"})
# 实测：走进 vip

# 形态 2：list —— 白名单，路由函数直接返回节点名
g.add_conditional_edges("planner", fan_out, ["worker"])
```

**为什么要多一层映射？** 因为**路由逻辑和图的拓扑应该解耦**。
业务代码里 `return "HIGH"` 比 `return "vip_agent_node_2"` 可读得多；改拓扑时（把 vip 换成 `vip_v2`）只改 `path_map`，路由函数一行不动。这就是**业务语义**与**图结构**的分层。

### 3.3 返回 list = 并行扇出

```python
g.add_conditional_edges("fan", lambda s: ["w1", "w2"])   # 返回列表
# 实测：['fan', 'w1', 'w2', 'merge']  ← w1/w2 同一步执行
```

返回 `Sequence` 时，**多个目标是同一个 super-step 并行执行的**，之后汇合。这就是"扇出/扇入"的静态版——**分几路在建图时就写死了**。分几路要到运行时才知道？用 `Send`（见第五章）。

### 3.4 错误行为（实测）

| 情况 | 结果 |
|------|------|
| 路由函数抛异常 | 异常**直接向上抛**（`ValueError: router failed`），不会自动兜底 |
| 返回值不在 `path_map` 里 | `KeyError: 'unknown'` |
| 返回 `END` / `"__end__"` | 图正常结束 |

⚠️ **后果**：路由函数是整个图的"单点故障"。生产环境必须写成**万能兜底**形式：

```python
def safe_route(state) -> Literal["a", "b", "__end__"]:
    try:
        intent = classify(state["query"])
    except Exception:
        intent = None
    return {"order": "a", "refund": "b"}.get(intent, "__end__")   # 未知 → 兜底出口
```

**再加一条：`path_map` 的键必须和路由函数可能返回的所有值对齐**，否则线上就是 500。建议路由函数**显式标注返回类型 `-> Literal[...]`**——既能让 IDE 检查覆盖度，也能让 LangGraph 画出正确的图（源码注释原话：不加类型提示又不给 `path_map`，可视化会假设它能去任何节点）。

### 3.5 与第一篇条件边的区别

第一篇的条件边是 `条件边三要素` 概念 + 反思循环；本篇补的是 **`path_map` 的分层价值、并行返回、错误行为、类型标注**这四个工程细节。

---

## 四、Router：路由函数的正式身份

**Router = 路由函数**（`add_conditional_edges` 的 `path` 参数）。它不是新 API，而是 LangGraph 里一个独立概念——**图里的"决策层"**。

### 4.1 为什么要把 Router 当真对待

一个典型的 Agent 图是三层的：

```
执行层  node ── 干活，读写 state（有副作用）
决策层  router ── 只读 state，返回下一步（纯函数，无副作用）
结构层  edge ── 把两者连起来
```

**Router 必须保持纯函数**：
- 不调 API、不查数据库、不改全局变量——否则（a）不可重放（checkpointer 恢复时会再执行一遍），（b）难以测试。
- 需要外部信息？**在 node 里先取好、写进 state**，router 只负责"看 state 做判断"。

### 4.2 Router 与 Router-as-Node 的取舍

LangGraph 也允许**节点返回 `Command`** 直接跳转（实测通过，见 4.3）。两种方式对比：

| | Router（条件边） | Node 返回 `Command(goto=...)` |
|---|---|---|
| 职责 | 只决策，不干活 | 干活 + 决策混在一起 |
| 可测试性 | ✅ 传个 dict 就能测 | ❌ 要跑整个节点 |
| 可视化 | ✅ 图能画出分支 | ⚠️ 分支是隐式的，图上看不出 |
| 适用 | 决策逻辑简单澄清 | 需要"边执行边决定"（如工具调用后跳转） |

**默认用 Router。** 只有当"做什么"和"去哪"天然不可分割时才用 `Command`。

### 4.3 `Command` 跳转（对照实验）

```python
def go_b(s) -> Command:
    return Command(goto="b", update={"log": ["goto->b"]})
```

实测：`['classify', 'goto->b', 'b']`，`Command(goto=END)` 也能直接终止。
`Command` 四个字段：`graph`（跳子图）、`update`（改 state）、`goto`（去哪）、`resume`（恢复 interrupt，见第六章）。
注意 `Command` **既能跳转又能更新 state**，而 Router 只能跳转——这是它唯一比 Router 强的地方。

---

## 五、Send：动态并行扇出（真正的 map-reduce）

### 5.1 问题：`add_conditional_edges` 返回 list 不够用

list 形式的分支数是**建图时写死**的（`["w1","w2"]`）。但很多场景是：**用户上传了 37 个文档，我要每个文档并行处理一遍**——37 在运行时才知道，图不能为 37 写死。

### 5.2 `Send` 的解法

```python
from langgraph.types import Send

def fan_out(state):
    # 每条 Send 都指定"送到哪个节点 + 给它什么输入"
    return [Send("worker", {"topic": t, "subtasks": [], "results": []})
            for t in state["subtasks"]]

g.add_conditional_edges("planner", fan_out, ["worker"])
```

实测（`subtasks = ["A","B","C"]`）：

```
['A-handled', 'B-handled', 'C-handled', 'total=3']
```

**三个 worker 实例并行跑完，结果通过 reducer 汇聚**。

### 5.3 关键机制：`Send` 的 payload 是**独立 state**

这一点最容易误解。`Send("worker", payload)` 里：

1. **payload 直接成为该 worker 实例的 state**，不是合并进主 state；
2. 所以 worker 读 `s["topic"]` 读到的是**你塞进去的那份**，而不是全局 state；
3. worker 的返回值**才**按 reducer 合回主 state（这里 `results: Annotated[list, operator.add]` 拼接）。

**类比**：`Send` 是"派单"，每张单子上写清楚货物；worker 按单子干活，干完把成品丢回总仓（reducer 汇总）。

### 5.4 `Send` vs list 分支

| | 返回 `["w1","w2"]` | 返回 `[Send("worker", x) for x in ...]` |
|---|---|---|
| 分支数 | 建图时固定 | **运行时动态** |
| 每个分支的输入 | 同一份 state | **各自独立 payload** |
| 典型用途 | 固定的两路并行（如同时查两个库） | map-reduce：N 个文档/N 个搜索结果逐个处理 |

### 5.5 这个模式和昨天学的 MQE 完全同构

回顾 [MQE/HyDE 笔记](../hello-agents/08-进阶检索-MQE与HyDE.md)：**扩展 → 并行检索 → 合并去重**。

```
MQE 手写版                         LangGraph 图版
─────────────────────────         ─────────────────────────
expansions = [q] + mqe + hyde  →   planner 节点产出 expansion 列表
for q in expansions:            →   fan_out 返回 [Send("retrieve", q) ...]
    store.search(q)                  worker 节点 = 检索一路
去重 + 按分数排序              →   results: Annotated[list, operator.add]
```

**这就是 LangGraph 存在的意义**：昨天那些 `for` 循环 + 手动合并，在这里变成了**可观测、可中断、可重放**的图。并行是真的并行、失败可重试、中间状态可快照。

---

## 六、interrupt + Command(resume)：与 defer 容易搞混的另一件事

学员今天把 `defer` 和这张图放一起学，很容易和 `interrupt` 混淆，这里放一起对照。

### 6.1 `interrupt` 实测

```python
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

def review(s):
    decision = interrupt({"question": "批准吗?", "draft": s["draft"]})   # 在这里暂停
    return {"approved": bool(decision), "log": [f"review:{decision}"]}

app = g.compile(checkpointer=InMemorySaver())
cfg = {"configurable": {"thread_id": "t1"}}

app.invoke({...}, cfg)                        # 第一次 → 停在 review
app.invoke(Command(resume=True), cfg)         # 人工批准 → 继续
```

实测结果：

```
首次运行中断 → 下个节点: ('review',)
interrupt payload: {'question': '批准吗?', 'draft': '这是草稿'}
已执行: ['draft']                      ← review 节点本身没跑完
resume(True) → ['draft', 'review:True', 'published']   approved = True
resume(False) → ['draft', 'review:False']  next = ()   ← 走 END 分支
```

### 6.2 三条铁律

1. **`interrupt` 必须配 checkpointer**。没有 checkpointer 就没有"暂停点"，无从恢复（和第一篇 HITL 结论一致）。
2. **`interrupt` 是"重放型"**：`resume` 后，**整个 `review` 节点会从头再执行一遍**，只是这次的 `interrupt(...)` 直接返回你给的 resume 值。所以节点内 `interrupt` **之前**的代码必须幂等——不要写 `db.insert()` 再 `interrupt`。
3. **`resume` 值必须能序列化**（走 checkpoint 存盘）。

### 6.3 `defer` vs `interrupt` vs `Command` 三者对照

| 机制 | 暂停图吗 | 谁决定下一步 | 典型场景 |
|------|---------|-------------|---------|
| **`defer=True`** | ❌ 不暂停，只是**排队到末尾** | 图自己 | 收尾任务（写日志/生成报告/上报指标） |
| **`interrupt`** | ✅ 真暂停，等人 | **人** | HITL 审批、敏感工具确认 |
| **`Command(goto)`** | ❌ 不暂停 | **节点自己** | 动态跳转、跳子图 |

---

## 七、defer：推迟到"本次运行即将结束"

### 7.1 签名与语义

```python
g.add_node("report", slow_report, defer=True)
```

源码原话：**"Whether to defer the execution of the node until the run is about to end."**

### 7.2 实测对照（三种场景）

**场景 A：纯线性链**

```
defer=True  顺序: ['main_a', 'main_b', 'report(deferred)']
defer=False 顺序: ['main_a', 'main_b', 'report(deferred)']
```

→ 无差异。**因为线性链里它本来就是最后一个。defer 在线性链上毫无作用。**

**场景 B：并行分支（关键差异，用耗时区分）**

```
主线 m1(200ms) → m2(200ms)，旁支 q(100ms) 设 defer=True
defer=True  顺序: ['start', 'm1', 'm2', 'q(100ms)']   耗时 0.51s
defer=False 顺序: ['start', 'm1', 'q(100ms)', 'm2']   耗时 0.41s
```

→ **差异出现了**：
- 不 defer：`q` 在第一个 super-step 就跑完（100ms 先于 200ms 的 m1）；
- defer：`q` **被压到最后一个 super-step 才跑**（等 m2 收工）。

代价是**总耗时变长**（0.51s vs 0.41s）——因为原本能并行的旁支被串到了最后。

**场景 C：长主链 5 步**

```
顺序: ['n1', 'n2', 'n3', 's']   ← s 虽然和 n2 同一步被触发，仍被推到最末
```

**场景 D：defer 节点在中间位置**

```
g3: START → d(defer=True) → after → END
顺序: ['D-defer', 'AFTER']
```

→ **defer 并没有跨 super-step 重排**。它只在"它本来触发的那一步"内部被推迟到该 super-step 的最后执行；如果后续还有节点，`after` 照常在下个 super-step 跑。

### 7.3 结论：defer 到底什么时候有用

**defer 的有效期只在"同一个 super-step 内"**。所以真正有意义的场景是：

✅ **有用**：
- 一个 super-step 里有多个节点并行（扇出），其中某个是**慢的收尾工作**（写报告、上报统计），你希望它别在并行队列里抢资源；
- 观测/日志类节点，希望它在**其他节点都跑完之后**才记录（记录到的是完整 state，不是半成品）。

❌ **没用**：
- 线性链（它本来就在最后）；
- 中间节点（后面还有节点的话，defer 无法跨越 super-step）。

⚠️ **重要副作用（实测）**：defer 节点**不会因为主链提前 END 而被跳过**。

```
场景：a 走条件边到 END，但另有一条 add_edge("a","rep") 指向 defer 节点 rep
实测: ['a', 'rep']        ← 主链明明 END 了，rep 还是执行了
```

也就是说 **defer 节点是"必然执行"的**（只要它被触发），而主链提前结束**不会**取消它。这对"收尾任务"是好事（保证报告一定写），但如果你以为"提前 return 能跳过收尾"，那就会出意外。

### 7.4 与 LangChain Middleware 的对照

| LangChain Middleware | LangGraph defer |
|---------------------|-----------------|
| `after_agent` 钩子 | 语义上最接近：都表示"主体跑完再做" |
| 但 middleware 钩子**一定**在 agent 结束后执行 | defer 只是**同一步内**的最后，不跨 super-step |

→ **想要"真·收尾"，用 `after_agent` middleware 或单独一个尾节点；`defer` 只是"同批里的最后一个"。** 这是今天纠正的一个认知偏差。

---

## 八、五个 API 的关系图（心智模型）

```
                     ┌─────────────────────────────┐
                     │      StateGraph 构建层       │
                     └─────────────────────────────┘
                                  │
        ┌─────────────┬───────────┼───────────┬─────────────┐
        ▼             ▼           ▼           ▼             ▼
  add_sequence   add_node    add_edge   add_conditional_  add_node
   (批量连链)   (defer/     (直线)      edges (岔路)     (defer=True)
                retry/                    │
                cache)                    ├── Router 纯函数 ── 返回单值 → 一路
                                          ├── 返回 │       ── 返回 list → 固定并行
                                          │   └── Send ──── 返回 N 个 Send → 动态并行
                                          └── 返回 END → 结束

              ┌───────────────────────────────────────────┐
              │  运行期控制：interrupt → Command(resume)  │  人机协同暂停/恢复
              │  节点内跳转：Command(goto)                │  隐式路由
              └───────────────────────────────────────────┘
```

---

## 九、决策清单（写图时照着问自己）

1. 这几个节点是**一条直线**吗？→ `add_sequence`
2. 下一步要**看 state 决定**吗？→ `add_conditional_edges` + **纯函数 Router**
   - 路由返回值是业务语义吗？→ 用 `path_map` 做一层映射
   - 路由函数可能抛错吗？→ **加 try + 兜底出口 + Literal 类型标注**
3. 要**并行几路**？
   - 数量固定（同时查两个库）→ Router **返回 list**
   - 数量运行时才知道（37 个文档）→ **`Send`**，每个 payload 独立 state
4. 有**慢的收尾任务**吗？→ 先想"要不要单独一个尾节点"，再看 `defer` 是否能满足（**别指望它跨 super-step**）
5. 需要**人审批**吗？→ `interrupt` + checkpointer + `Command(resume)`（**interrupt 前的代码要幂等**）

---

## 十、踩坑清单（本篇实测汇总）

| # | 坑 | 现象 | 解法 |
|---|-----|------|------|
| 1 | `add_sequence` 重复注册 | `ValueError: Node names must be unique` | 它是"注册+连边"，不能用来连已有节点 |
| 2 | 路由函数返回值没在 `path_map` 里 | `KeyError: 'unknown'` | 兜底 `.get(key, "__end__")` |
| 3 | 路由函数抛异常 | 异常直接冒泡，整图失败 | try/except + 兜底出口 |
| 4 | 路由函数无类型标注 | 图可视化"能去任何节点"，也查不出漏分支 | `-> Literal["a","b","__end__"]` |
| 5 | `Send` 的 payload 当成"合并进主 state" | worker 读不到全局 state 而困惑 | payload **就是**该实例的完整 state |
| 6 | 以为 `interrupt` 只是"暂停一下" | resume 后节点**整段重跑** | interrupt 前的副作用必须幂等 |
| 7 | 以为 `defer` 能跨 super-step | 中间节点设 defer 毫无效果 | defer 只在同一 super-step 内生效 |
| 8 | 以为主链 END 会取消 defer 节点 | 实测 `['a','rep']`，它照跑 | 收尾任务"必达"，别指望提前取消 |
| 9 | 忘了 checkpointer 就调 `interrupt` | 无法恢复 | 编译时必须 `checkpointer=...` |

---

## 十一、自检问题

1. `add_sequence([fetch, parse, store])` 到底做了哪两件事？为什么不能用来连接已经 `add_node` 过的节点？
2. `add_conditional_edges` 的 `path_map` 用 dict 而不是 list，好处是什么？（答：业务语义与图拓扑分层）
3. Router 为什么必须是纯函数？如果它需要查数据库怎么办？
4. 返回 `["w1", "w2"]` 和返回 `[Send("worker", x) for x in xs]` 的本质区别是什么？
5. `Send` 的 payload 和主 state 是什么关系？worker 的返回值又是怎么回到主 state 的？
6. `defer=True` 在线性链上为什么不产生任何效果？
7. 主链走条件边直接 END 时，一个挂着的 defer 节点会被取消吗？（答：不会）
8. 用 `interrupt` 做人机审批，为什么节点内 `interrupt` 之前的代码必须幂等？
9. 想把昨天的 MQE「扩展→并行检索→合并」画成一张 LangGraph 图，你会用哪些 API？

---

## 🔗 衔接

- **往回**：[LangGraph（一）](./langgraph-01-图基础与状态管理.md) 的 Reducer 是 `Send` 汇聚的前提——没有 `Annotated[list, operator.add]`，多个 worker 的结果会互相覆盖。
- **往回**：[MQE/HyDE](../hello-agents/08-进阶检索-MQE与HyDE.md) 的"扩展→并行检索→合并"正是 `Send` + reducer 的经典用法，本篇把它图化。
- **往回**：[LangChain 五·Middleware](../tools/langchain-05-middleware.md) 的 `after_agent` vs 本篇 `defer`——语义相近但作用域不同，别混。
- **往前**：Subgraph 子图（`Command(graph=...)` 配合）、`retry_policy` / `cache_policy` / `timeout` / `error_handler`（`add_node` 的其余参数）、手搓 ReAct 图对照 `create_agent`。
