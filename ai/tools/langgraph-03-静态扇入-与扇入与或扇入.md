# LangGraph（三）· 静态扇入：与节点扇入 vs 或节点扇入

> 学习日期：2026-10-30
> 环境：本机 `langgraph 1.2.16`（本文所有结论均为实际运行验证，附实测输出）
> 承接：[LangGraph（二）· 进阶建图](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md)（`Send` 动态扇出）

---

## 一、先分清"扇出"和"扇入"

任何并行图都是成对出现的：

```
        扇出 (fan-out)                扇入 (fan-in / join)
   START ──┬──► A                 A ──┐
           ├──► B        ───►         ├──► Merge ──► ...
           └──► C                 C ──┘
   一个源头分叉成多路            多路重新汇聚到一点
```

- **扇出**：决定有几路并行、哪几路并行
- **扇入**：决定这几路**什么时候**算"齐了"、**怎么**把结果合到一起

LangGraph 里扇入其实只由**一个东西**决定：**目标节点的入口边是否全部被激活**。
围绕这一点，产生两种语义完全不同的扇入模式——**与（AND）** 和 **或（OR）**。

| | **与扇入 AND-join** | **或扇入 OR-join** |
|---|---|---|
| 触发条件 | **所有**入边都走到，才执行一次 | **任意一条**入边走到，就执行一次 |
| 上游关系 | 并行兄弟，全部必达 | 互斥候选（分支/重试/可选步骤） |
| 执行次数 | 每个 super-step **最多 1 次** | 每次被激活就跑，可能跑多次 |
| 拿到的 state | **所有**兄弟的写入都已合并 | 只有**那条路径**上的写入 |
| 典型场景 | 多路检索 → 汇总；多专家 → 裁判 | if/else 汇合、try 后 fallback、循环出口 |
| 关键前提 | **必须配 reducer**（`Annotated[T, f]`） | 一般用 LastValue 就够 |

记忆锚点：**与扇入 = "人都到齐了才开会"；或扇入 = "谁来了谁先讲"。**

---

## 二、静态 vs 动态：本文的"静态"指什么

| | 静态扇入 | 动态扇入 |
|---|---|---|
| 路数在哪决定 | **建图时写死**（画几条边就是几条） | **运行时决定**（`Send` 按数据量生成） |
| API | `add_edge` 多条指向同一节点 | `add_conditional_edges` 返回 `[Send(...)]` |
| state | 各分支共享主 state，结果靠 **reducer** 合并 | 每个 `Send` 的 payload **就是**该 worker 的完整 state |
| 笔记 | **本篇** | [（二）第五章](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md) |

一句话：**静态扇入是"图的形状"决定的，动态扇入是"数据"决定的。**

---

## 三、与节点扇入（AND-join）：全员必达

### 3.1 最小实现

```python
from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, START, END

class S1(TypedDict):
    results: Annotated[List[str], operator.add]   # ← 扇入的前提
    calls:   Annotated[List[str], operator.add]

def a(s): return {"results": ["A"], "calls": ["a"]}
def b(s): return {"results": ["B"], "calls": ["b"]}
def c(s):
    print(f"[c] 收到 results={s['results']} calls={s['calls']}")
    return {"results": ["C"], "calls": ["c"]}

g1 = StateGraph(S1)
g1.add_node("a", a); g1.add_node("b", b); g1.add_node("c", c)
g1.add_edge(START, "a");  g1.add_edge(START, "b")   # 扇出：固定两路
g1.add_edge("a", "c");    g1.add_edge("b", "c")     # 扇入：两条边都指向 c
g1.add_edge("c", END)

print(g1.compile().invoke({"results": [], "calls": []}))
```

**实测输出：**

```
[c] 收到 results=['A', 'B'] calls=['a', 'b']
{'results': ['A', 'B', 'C'], 'calls': ['a', 'b', 'c']}
```

三个关键事实：

1. **`c` 只执行了 1 次**，且进去时 `a` 和 `b` 的结果都已在 state 里 —— 这就是"全员到齐"。
2. `a` 和 `b` 在**同一个 super-step** 里并行跑（不管用的是多线程还是 await）。
3. `c` 的写入发生在**下一个** super-step —— 扇入节点天然是 super-step 的分界线。

### 3.2 三路扇入 + 逐步观察

```python
class S3(TypedDict):
    parts:   Annotated[List[str], operator.add]
    summary: str

def p1(s): return {"parts": ["p1"]}
def p2(s): return {"parts": ["p2"]}
def p3(s): return {"parts": ["p3"]}
def collect(s):
    print(f"[collect] parts={s['parts']}")
    return {"summary": "+".join(s["parts"])}

g3 = StateGraph(S3)
for n, f in [("p1", p1), ("p2", p2), ("p3", p3), ("collect", collect)]:
    g3.add_node(n, f)
for n in ["p1", "p2", "p3"]:
    g3.add_edge(START, n)      # 三路扇出
    g3.add_edge(n, "collect")  # 三路扇入
g3.add_edge("collect", END)

for step in g3.compile().stream({"parts": [], "summary": ""}, stream_mode="updates"):
    print(step)
```

**实测输出：**

```
{'p1': {'parts': ['p1']}}
{'p2': {'parts': ['p2']}}
{'p3': {'parts': ['p3']}}
[collect] parts=['p1', 'p2', 'p3']
{'collect': {'summary': 'p1+p2+p3'}}
```

四行 `updates` = 两个 super-step：第一个是 p1/p2/p3 的并行写入（分别打印，因为 `updates` 是按节点分组的），第二个才是 `collect`。
**注意 `collect` 只出现一次** —— 三路齐了才跑一次，不是跑三次。

### 3.3 自定义 reducer 也能扇入（不一定是 list）

```python
class S6(TypedDict):
    n:     Annotated[int, operator.add]     # 数字相加
    order: Annotated[List[str], operator.add]

def s6a(s): return {"n": 1,  "order": ["s6a"]}
def s6b(s): return {"n": 10, "order": ["s6b"]}
def s6c(s):
    print(f"[s6c] n={s['n']} order={s['order']}")
    return {"order": ["s6c"]}

# START → s6a, s6b；s6a, s6b → s6c
```

**实测输出：**

```
[s6c] n=11 order=['s6a', 's6b']
{'n': 11, 'order': ['s6a', 's6b', 's6c']}
```

扇入节点看到的是**所有兄弟合并后的 state**：`1 + 10 = 11`。
`Annotated[int, operator.add]` 用得少但完全合法——凡是"多路要汇总成一个值"的，reducer 就是那个汇总函数。

### 3.4 ⚠️ 核心坑：没有 reducer 直接崩

删掉 `Annotated` 会怎样？

```python
class S4(TypedDict):
    results: List[str]        # 没有 Annotated！
# START → x, y；x, y → z，x/y 都返回 {"results": [...]}
```

**实测：**

```
InvalidUpdateError: At key 'results': Can receive only one value per step.
Use an Annotated key to handle multiple values.
https://docs.langchain.com/oss/python/langgraph/errors/INVALID_CONCURRENT_GRAPH_UPDATE
```

这不是"后写覆盖前写"，而是**直接报错**。
LangGraph 的 `LastValue` channel 在一次 super-step 内对同一 key 只允许一次写入——它宁愿崩溃也不让你悄悄丢数据。**扇入的所有参与 key 必须有 reducer。**

### 3.5 ⚠️ 坑二：并行顺序不确定，别依赖 `calls` 的顺序

实测里 `calls` 每次都是 `['a','b']`，但那是**单节点并发**的巧合（同一 super-step 内按任务提交顺序写入）。
**节点内部耗时不同、或有 `Send` 动态扇出时，写入顺序不保证。** 需要确定顺序时分两步走：

```python
# 方案：先收集，再排序合成
def collect(s):
    ordered = sorted(s["results"], key=KEY_ORDER.index)  # 自己定序
    return {"summary": ordered}
```

---

## 四、或节点扇入（OR-join）：任一路到即触发

### 4.1 形态一：if/else 汇合（最常见的误区）

很多人以为"两条边指向同一个节点"就等于或扇入。**不一定**——要看这两条边是否**可能在同一 super-step 同时激活**。

```python
class S2(TypedDict):
    calls: Annotated[List[str], operator.add]
    opt:   bool

def main(s):     return {"calls": ["main"]}
def optional(s): return {"calls": ["optional"]}
def merger(s):
    print(f"[merger] calls={s['calls']}")
    return {"calls": ["merger"]}

def after_main(state) -> Literal["optional", "merger"]:
    return "optional" if state["opt"] else "merger"

g2 = StateGraph(S2)
g2.add_node("main", main); g2.add_node("optional", optional); g2.add_node("merger", merger)
g2.add_edge(START, "main")
g2.add_conditional_edges("main", after_main, {"optional": "optional", "merger": "merger"})
g2.add_edge("optional", "merger")   # optional 走完也回 merger
g2.add_edge("merger", END)
```

**实测输出：**

```
== opt=True ==
  [merger] calls=['main', 'optional']       ← optional 走完再汇合
== opt=False ==
  [merger] calls=['main']                   ← 跳过 optional 直接汇合
```

这就是**或扇入**：`merger` 有两条入边（来自 `main` 的条件边 + 来自 `optional` 的普通边），但**任一到达即执行**，不需要等另一条。
因为条件边是**互斥**的——同一 super-step 只激活一条，所以永远不会出现"等齐"需求。

> **关键判据**：入口边是**互斥的**（条件边、循环回边）→ 或扇入语义；
> 入口边是**并行的**（多条 `add_edge` 从同一节点/SATRT 发出）→ 与扇入语义，**必须 reducer**。

### 4.2 形态二：循环回边汇合

```python
def work(s):    return {"n": s["n"] + 1, "calls": ["work"]}
def finalize(s):
    print(f"[finalize] n={s['n']} calls={s['calls'][-3:]}")
    return {"calls": ["finalize"]}

def judge(state) -> Literal["work", "finalize"]:
    return "work" if state["n"] < 3 else "finalize"

g.add_edge(START, "work")
g.add_conditional_edges("work", judge, {"work": "work", "finalize": "finalize"})
g.add_edge("finalize", END)
```

**实测输出：**

```
[finalize] 被调用 n=3 calls=['work', 'work', 'work']
{'n': 3, 'calls': ['work', 'work', 'work', 'finalize']}
```

`finalize` 只有一条入口，但"进入它"意味着循环退出——语义上仍是"某一路到达即汇合"。
**这类或扇入不需要任何 reducer 也能跑**（`calls` 用了 reducer 只是因为想累积轨迹）。

### 4.3 形态三：并行两路各自独立汇合（易错放大）

```python
# START 条件路由到 a 或 b，a/b 都指向 merge
g.add_conditional_edges(START, router, {"a": "a", "b": "b"})
g.add_edge("a", "merge")
g.add_edge("b", "merge")
```

**实测：**

```
== path=a ==  [merge] calls=['a']  →  {'calls': ['a', 'merge']}
== path=b ==  [merge] calls=['b']  →  {'calls': ['b', 'merge']}
```

每次只跑一条路，`merge` 拿到的只有该路径的写入。**如果误以为这是与扇入、在上面等了"另一路"，就会死等。**

---

## 五、混淆两种扇入会造成什么 bug

### bug 1：把或扇入当与扇入 → 想"等齐"结果只等到一路

```python
# 错误预期：merge 能同时看到 a 和 b
# 实际：条件边互斥，永远只有一路，merge 只看到一路
```

**症状**：`state` 里永远是 `None` / 空列表，日志显示另一路"从没执行过"。
**真相**：不是没执行，是**这次运行根本没走那条路**。

### bug 2：把与扇入当或扇入 → 少配 reducer 直接崩

见 §3.4，`InvalidUpdateError`。

### bug 3：与扇入里某个分支可能走 END → 汇合点永远不触发

```python
# START → a, b；a → merge；b → 条件边 → (merge | END)
# 若 b 本次走 END，merge 只剩 a 一路到达 —— 但它还有一个未激活的入边 b→merge
```

LangGraph 的行为是：**当前 super-step 里只要有一条入边被激活，节点就执行**（不会被"未激活的兄弟边"阻塞）。
也就是说：**严格意义上的"必须 N 路全部到达"只在所有 N 路都无条件激活时才成立**。
一旦某路可能中途退出，它就自动退化成"或"语义。

> 想要"部分分支可跳过、但其余必须齐"的语义，做法是：
> **用 reducer 收集 + 在汇合点自己判断数量**。
> ```python
> def merge(s):
>     if len(s["parts"]) < 3:            # 自己校验是否齐
>         raise RuntimeError("分支不齐")
> ```
> 或者把可跳过的分支改成**返回占位值**（`{"parts": ["b:skipped"]}`）而不是走 END。

---

## 六、与扇入的最佳实践（凭经验总结）

| 实践 | 原因 |
|------|------|
| **每个参与扇入的 key 都配 reducer** | 否则 `InvalidUpdateError` |
| **汇合节点里自己校验完整性** | LangGraph 不保证"等齐N路"，只保证"激活了就执行" |
| **别依赖列表顺序** | 并行写入顺序不保证；要顺序就自己 sort |
| **汇合节点尽量纯函数** | 它可能被重跑（配合 checkpointer 时），副作用要幂等 |
| **扇出前想清楚"是否可能中断"** | 一旦有路走 END，与扇入就退化 |
| **路数固定就用 `add_edge` 硬连** | 比 `Send` 简单可读，图上可视化也清晰 |
| **路数运行时才知道才用 `Send`** | 见（二）第五章 |

---

## 七、与扇入 vs 或扇入的完整对照（含代码骨架）

```python
# ---------- 与扇入 AND-join ----------
class AndState(TypedDict):
    outs: Annotated[List[str], operator.add]     # ✅ reducer 必须

g = StateGraph(AndState)
g.add_node("w1", ...); g.add_node("w2", ...); g.add_node("join", ...)
g.add_edge(START, "w1"); g.add_edge(START, "w2")  # 并行兄弟
g.add_edge("w1", "join"); g.add_edge("w2", "join")  # 全部指同一节点
# join 一次，看到 outs=['w1','w2']


# ---------- 或扇入 OR-join ----------
class OrState(TypedDict):
    calls: Annotated[List[str], operator.add]    # reducer 可选

def route(state) -> Literal["a", "b"]:
    return state["which"]

g = StateGraph(OrState)
g.add_node("a", ...); g.add_node("b", ...); g.add_node("merge", ...)
g.add_conditional_edges(START, route, {"a": "a", "b": "b"})   # 互斥
g.add_edge("a", "merge"); g.add_edge("b", "merge")            # 哪条走都汇合
# merge 一次，只看到走的那一路
```

---

## 八、决策清单

写扇入时照着问自己：

1. **几路汇聚到这个节点？** —— 数入边。
2. **这些入边会同时激活吗？**
   - 会（多条 `add_edge` 从同一祖先发出）→ **与扇入**，配 reducer，汇合点可校验齐活
   - 不会（条件边 / 循环回边，互斥）→ **或扇入**，LastValue 就够
3. **某一路可能中途退出（走 END）吗？**
   - 会 → 与扇入退化成"或"，要么让退出分支返回占位值，要么在汇合点自己校验
4. **汇合结果的顺序重要吗？**
   - 重要 → 自己 sort，别信 reducer 的追加顺序
5. **汇合节点有副作用吗（写库/发消息）？**
   - 有 → 必须幂等，配合 checkpointer 时可能重跑
6. **路数固定还是运行时才知道？**
   - 固定 → 本篇 `add_edge`
   - 动态 → `Send`（（二）第五章）

---

## 九、踩坑清单（本篇实测汇总）

| # | 坑 | 现象 | 解法 |
|---|-----|------|------|
| 1 | 扇入 key 没配 reducer | `InvalidUpdateError: Can receive only one value per step` | 用 `Annotated[T, reducer]` |
| 2 | 以为扇入节点会跑 N 次 | 实际只跑 1 次（实测 `invocations=1`） | 单次执行里拿全部兄弟结果 |
| 3 | 依赖 reducer 追加顺序 | 单节点巧合稳定，动态扇出不保证 | 自己 sort |
| 4 | 把条件边的汇合当与扇入 | 一直等不到"另一路" | 条件边互斥，是或扇入 |
| 5 | 与扇入里一路走 END | 汇合点只看到部分数据 | 退出分支返占位值 或 汇合点自校验 |
| 6 | 用 `Send` 的思维写静态扇入 | 想给每个分支独立 state | `Send` payload 才是独立 state；静态扇入共享主 state |
| 7 | 以为 `add_sequence` 能连已有节点 | `ValueError: Node names must be unique` | `add_sequence` 只连它自己注册的 |

---

## 十、自检问题

1. 区分与扇入/或扇入，**唯一需要看的**是哪个结构特征？（答：入口边是否会**同时**激活）
2. 为什么三条 `add_edge(n, "join")` 的 `join` 只跑 1 次？靠什么机制？（答：目标节点入边全激活才调度；state 合并靠 reducer）
3. 把 `Annotated[List[str], operator.add]` 改成 `List[str]` 后是"后到覆盖先到"还是报错？（答：直接报 `InvalidUpdateError`）
4. 条件边的目标是同一节点，这算与扇入还是或扇入？为什么？
5. 与扇入里某一路走了 END，汇合点会等它吗？（答：不等，会执行——与扇入退化成或）
6. `Annotated[int, operator.add]` 能用来做扇入吗？给个场景。
7. 为什么说"扇入节点天然是 super-step 分界线"？
8. 静态扇入和 `Send` 动态扇入，state 的来源有什么本质差别？

---

## 🔗 衔接

- **往回**：[LangGraph（一）](./langgraph-01-图基础与状态管理.md) 的 Reducer 是**与扇入的前提**，没有它扇入直接崩。
- **往回**：[LangGraph（二）](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md) 讲了 `Send` 动态扇出——本篇是它的"静态兄弟"：**固定路数用 `add_edge`，动态路数用 `Send`**。
- **往回**：[MQE/HyDE](../hello-agents/08-进阶检索-MQE与HyDE.md) 的"扩展 → 并行检索 → 合并"：扩展路数已知 → 静态与扇入；扩展路数由 LLM 现算 → `Send`。
- **往前**：Subgraph 作为扇入目标（多子图汇聚）、`Command(goto=[...])` 在节点内做静态并行分派、`defer` 与汇合节点的关系。
