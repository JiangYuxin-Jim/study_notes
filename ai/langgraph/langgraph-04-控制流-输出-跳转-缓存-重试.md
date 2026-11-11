# LangGraph · 控制流：输出 · 跳转 · 缓存 · 重试

> 学习日期：2026-10-31
> 环境：本机 `langgraph 1.2.16` + `langgraph-checkpoint 4.3.0`，全部结论**逐条实跑验证**（实验脚本附在文末）
> 承接：[LangGraph（三）· 静态扇入](langgraph-03-静态扇入-与扇入与或扇入.md)（"什么时候算齐"）
> 本篇主题：图"怎么连"（边）之外的四件控制权——**输出什么给外面看、能不能中途改道、算过的能不能不重算、算挂了能不能再算**

---

## 〇、一句话总览

| 控制维度 | 机制 | 解决什么问题 | 挂在哪 |
|---|---|---|---|
| **输出** | `stream_mode` + `get_stream_writer()` | 外面怎么"看"和"拿"运行过程 | 调用方 `stream()` / 节点内部 |
| **跳转** | `Command(goto=..., update=...)` | 节点运行时**自己**决定下一步去哪，覆盖静态边 | 节点**返回值** |
| **缓存** | `CachePolicy` + `compile(cache=...)` | 同输入不重复算（省钱、省时间） | `add_node(..., cache_policy=...)` |
| **重试** | `RetryPolicy` | 瞬时故障自动重来 | `add_node(..., retry_policy=...)` |

四者互不冲突，可以同一个节点上叠加（`cache_policy` + `retry_policy` 同时挂，实测没问题）。

一条心智模型：

> **边是"建图时"说好的路，`Command` 是"运行时"改道的方向盘，`RetryPolicy` 是油门打了滑怎么再来一次，`CachePolicy` 是这条路修好了就别再修，`stream_mode` 是路边的监控摄像头。**

---

## 一、输出控制：外面到底能看到什么

### 1.1 六种 stream_mode 速查（本篇实测前四种）

| mode | 每次吐什么 | 适合谁 |
|---|---|---|
| `updates` | `{节点名: 该节点返回的增量}` | **调试首选**：一眼看出哪个节点改了什么 |
| `values` | **完整 state 快照**（含初始态） | 要整体状态、UI 渲染整页 |
| `messages` | `(token_chunk, metadata)` | 打字机效果（LLM token 流） |
| `custom` | 节点内 `get_stream_writer()` 写出的任意对象 | **业务进度条 / 中间事件** |
| `debug` | 极详细事件（task 起止、checkpoint…） | 排查执行细节 |
| `checkpoints` | checkpoint 事件 | 时间旅行 / 审计 |

**实测（updates）**：

```
[run] a
 {'a': {'log': ['a'], 'answer': 'quick answer'}}
[run] b
 {'b': {'log': ['b'], 'answer': 'deep answer'}}
```

**实测（values）**——注意**第一条是初始 state 本身**（节点还没跑）：

```
 {'log': [], 'question': 'a very long question indeed'}     ← 初始快照
[run] a
 {'log': ['a'], 'question': '...', 'answer': 'quick answer'}
[run] c
 {'log': ['c'], 'question': '...', 'answer': 'quick answer'}
```

`updates` 里 `'log': ['a']` 是**增量**（reducer 之前的值），`values` 里是**已经合并完**的结果。这是两者最容易混淆的一点。

### 1.2 多模式同时开

```python
for chunk in app.stream(inputs, config, stream_mode=["updates", "values"]):
```
每个 chunk 变成 `(mode_name, payload)` 元组，实测：

```
('values',  {'log': [], 'question': 'hi'})
[run] a
('updates', {'a': {'log': ['a'], 'answer': 'quick answer'}})
('values',  {'log': ['a'], 'question': 'hi', 'answer': 'quick answer'})
```

⚠️ **顺序**：初始 `values` 先来，然后每个节点先 `updates` 后 `values`。

### 1.3 custom 流：把节点内部进度吐给外面

```python
from langgraph.config import get_stream_writer

def progress(state):
    writer = get_stream_writer()
    writer({"progress": 0}); writer({"progress": 50}); writer({"progress": 100})
    return {"log": ["progress"]}
```
```
for chunk in app.stream(..., stream_mode="custom"):
   {'progress': 0}
   {'progress': 50}
   {'progress': 100}
```

**关键点**：writer 写的东西**不进 state**。切回 `stream_mode="updates"` 只看得到 `{'progress': {'log': ['progress']}}`，那三条进度消失。
→ 进度/心跳/中间事件用 custom，**需要留在历史里的必须 return**。

> 实战对应：智能搜索助手（hello-agents 6.5 的 `Dialogue_System.py`）就是把 `astream()` 的每个节点输出拿来当 UI 字幕——`understand`/`search`/`answer` 三阶段提示。换成 custom writer 会更清爽，因为不用把提示语塞进 `messages` 污染对话历史。

---

## 二、跳转：`Command`

### 2.1 三种粒度

```python
from langgraph.types import Command, Send

# ① 跳到一个节点（或 END）
return Command(update={"log": ["x"]}, goto="y")

# ② 静态并行：同时跳到多个节点
return Command(update={"out": ["p1"]}, goto=["p2", "p3"])

# ③ 动态扇出：goto 里放 Send 列表（数量运行时才知道）
return Command(goto=[Send("worker", {"item": i}) for i in state["items"]])
```

`update` 的作用和普通节点返回 dict **完全一样**（走 reducer）。所以 `Command` = **"返回值 + 下一跳"二合一**。

### 2.2 实测：`goto` 覆盖静态边

```python
g.add_edge(START, "x"); g.add_edge("x", "z"); g.add_edge("y", END)
def x(s): return Command(update={"log": ["x"]}, goto="y")
```
只保留 `goto="y"` 时 → `{'log': ['x', 'y']}`（`z` 没跑）。

**⚠️ 我踩的坑：静态边和 `goto` 是"并存"不是"覆盖"**

如果 `g.add_edge("x","z")` 和 `goto="y"` **都写**，实测结果是：

```
{'log': ['x', 'y', 'z']}
```

`z` **照跑**。原因：`goto` 只是额外"追加"一条出边，**静态边并不会因此失效**。所以：
- 想让 `Command` 独占路由 → **节点不要注册静态出边**；
- 想"条件性加跑一个节点" → 这个并存特性反而正好用得上。

### 2.3 实测：`goto=[...]` 静态并行

```
{'out': ['p1', 'p2', 'p3', 'p4']}
```
`p1` 同时派发 `p2`/`p3`，之后用与扇入 `add_edge(["p2","p3"], "p4")` 收齐。
**和（三）篇的 `add_edge` 分支对比**：`add_edge("p1","p2") + add_edge("p1","p3")` 也能并行，但**"去哪"是建图时写死的**；`Command(goto=[...])` 是**运行时**决定的（比如按 state 里列表长度决定派几个）。

### 2.4 实测：`goto=[Send...]` 动态扇出

```
[run] fan_out
[run] worker {'item': 1} / {'item': 2} / {'item': 3}
{'items': [1,2,3], 'results': [2,4,6]}
```
这就是（二）篇 `add_conditional_edges` 里返回 `[Send...]` 的**节点内写法**。区别：
- `add_conditional_edges("a", router)` → 路由函数**只看 state**、**返回** Send 列表，**不能改 state**；
- `Command(goto=[Send...], update={...})` → **能同时改 state**（"派活的时候顺手记一笔"）。

### 2.5 实测：`Command(goto=END)` 提前终止

```python
def guard(s):
    if s.get("block"): return Command(goto=END, update={"log": ["blocked"]})
    ...
```
```
block=True : {'log': ['blocked']}
block=False: {'log': ['passed', 'work']}
```
**这是"防火墙式"节点的标准写法**：输入校验不过就原地结束，不往下走。

### 2.6 什么时候用 `Command` 而不是条件边

| 场景 | 选谁 |
|---|---|
| 纯按 state 分支，不需要改 state | `add_conditional_edges`（更声明式、图能画出来） |
| 分支时要**顺手改 state** | `Command` |
| 一个节点**可能跳到多个下游**（并行） | `Command(goto=[...])` |
| 要**提前终止**整张图 | `Command(goto=END)` |
| 想让子图**跳回父图**某个节点 | `Command(goto=..., graph=Command.PARENT)` |

---

## 三、缓存：`CachePolicy`

### 3.1 怎么开

```python
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy

g.add_node("slow", slow_fn, cache_policy=CachePolicy(ttl=2))   # ttl 秒；None = 永不过期
app = g.compile(cache=InMemoryCache())                        # ← 必须给 cache 实例
```

**两个都要**：节点上声明策略 + `compile(cache=...)` 提供存储。只写一个不生效。

### 3.2 实测：命中条件

节点 `slow` 有 `time.sleep(0.3)`，用耗时当"是否重算"的信号：

| 调用 | 输入 | 耗时 | 是否执行 |
|---|---|---|---|
| `thread_id=t1` 第一次 | hello | 0.309s | ✅ 跑 |
| `thread_id=t1` 第二次 | hello | **0.005s** | ❌ 命中 |
| `thread_id=t2`（不同线程） | hello | **0.004s** | ❌ **命中** |
| `thread_id=t3` | world | 0.306s | ✅ 跑（输入不同） |
| 等 2.5s 后（ttl=2 过期） | hello | 0.306s | ✅ 跑（TTL 过期） |

**三个结论**：

1. **缓存 key = 节点名 + 该节点收到的输入（+ 配置）**，与 `thread_id` **无关** → 缓存是**跨会话共享**的。这是"省钱"的关键：不同用户问同一个问题，LLM 只算一次。
2. **TTL 按写入时间算**，与本篇的 checkpointer 完全是两套东西（checkpointer 管"线程历史"，cache 管"计算结果"）。
3. `ttl=None`（默认）＝永不过期 —— **对 LLM 节点要小心**：模型升级、prompt 改了，老答案会一直命中。要么给 TTL，要么自己管缓存版本号。

### 3.3 缓存 key 怎么自定义

```python
CachePolicy(key_func=lambda state: state["query"].strip().lower())
```
默认 key 是整个输入 state 的哈希——**state 里有个无关字段变了（比如时间戳）就会 miss**。所以实践中常自己指定 `key_func` 只取真正决定输出的字段。

### 3.4 什么该缓存、什么绝不能缓存

| 该缓存 | 绝不能缓存 |
|---|---|
| LLM 调用（同 prompt 同模型） | 有副作用的外部写操作（发消息、下单、扣库存） |
| 昂贵检索 / Embedding | 依赖当前时间的节点（"现在几点"） |
| 确定性计算 | 需要走人工审批的节点 |

> 记住这条：**缓存 = 假装这次节点执行从未发生过**。任何"执行本身有价值"的节点都不要缓存。

---

## 四、重试：`RetryPolicy`

### 4.1 怎么配

```python
from langgraph.types import RetryPolicy

g.add_node("search", search_fn,
           retry_policy=RetryPolicy(max_attempts=3, initial_interval=0.1, jitter=False))
```

| 字段 | 含义 |
|---|---|
| `max_attempts` | **总尝试次数**（含第一次）。`3` = 首次 + 重试 2 次 |
| `initial_interval` | 首次退避间隔（秒），之后指数增长 |
| `backoff_factor` | 退避倍数（默认 2） |
| `max_interval` | 单次退避上限 |
| `jitter` | 是否加随机抖动（多副本打同一 API 时**要开**，防雪崩同步） |
| `retry_on` | 哪些异常重试：异常类 / 元组 / 可调用对象 |

实测成功恢复：
```
[run] flaky #1 -> raise
[run] flaky #2 -> raise
[run] flaky #3 -> ok
{'out': ['ok@3']}
```

实测耗尽：`max_attempts=2` 跑两次后 `raised: RuntimeError never works` —— **异常最终抛给调用方**，不是静默返回。
未配 `retry_policy` 的节点报错 → `raised: ValueError no retry`，**一次都不重试**。

### 4.2 ⚠️ 最大的坑：`ValueError` 默认**不重试**

我第一版实验用 `raise ValueError("boom")` 配 `RetryPolicy(max_attempts=3)`，结果**只跑了 1 次**：

```
[run] value -> raise
raised: ValueError default skip （只跑了 1 次，没重试）
```

翻了 `langgraph/_internal/_retry.py` 的 `default_retry_on`，**默认白名单是黑名单制**——以下内置异常**直接放弃重试**：

```
ValueError, TypeError, ArithmeticError, ImportError, LookupError,
NameError, SyntaxError, RuntimeError, ReferenceError,
StopIteration, StopAsyncIteration, OSError
```

（其余异常以及 `Exception` 默认重试。）

**设计意图很合理**：这些异常基本都是「代码写错了」，重试一万次也是同样的错，白烧钱。真正该重试的是网络/超时/限流。

**踩到的连带效应**：`TimeoutError` 是 `OSError` 的子类 → **默认不重试**！所以"API 超时自动重试"这种最常见的需求，**恰恰需要显式写**：

```python
RetryPolicy(max_attempts=3, retry_on=(TimeoutError, ConnectionError, Exception))
```

反过来，如果你确实想让 `ValueError` 重试（比如某些 SDK 用 ValueError 表示限流），就显式写 `retry_on=ValueError`——上面 flaky 实验正是这么修好的。

### 4.3 重试作用在哪一层

重试的是**整个节点的执行**，不是节点内部某一行。所以：
- 节点要**幂等**：重试会重跑整段，写数据库要 `upsert` 不要 `insert`；
- 节点里如果已经对外发了一条消息，重试会**再发一次** → 副作用外置到别的节点，或者自己加去重键。

### 4.4 三层容错别搞混

| 层 | 工具 | 粒度 |
|---|---|---|
| 单次调用 | LLM SDK 自己的 retry / `max_retries` | HTTP 请求 |
| **单个节点** | **`RetryPolicy`** | **节点执行** |
| 整条业务链 | 条件边 + 重试计数 state（见实验四 `verify`） | 图 |

---

## 五、四者合体：实战图

实验四把四件事全用上（脚本见文末）：

```
              ┌── Command(goto) 决定 ──┐
START ──► understand ──┬──► search ──┐
   │                   └──► answer ◄─┐│
   │ goto=END(非法输入)              ││
   └────────────────────────────────┘│
                                     ▼
                                  verify ── Command(goto="answer") 不合格重写
                                     │
                                     ▼
                                   hitl ── Command(goto=END / "answer")
```

| 节点 | 挂的控制 |
|---|---|
| `understand` | `Command`（路由 + 非法输入 `goto=END`）、`CachePolicy(ttl=3600)` |
| `search` | **`RetryPolicy`**（首次 `ConnectionError` 自动重试）+ `CachePolicy(ttl=300)` |
| `answer` | `CachePolicy()` |
| `verify` | `Command` 回跳 `answer`（带 `attempts` 上限防死循环） |
| `hitl` | `Command(goto=END/"answer")` + `get_stream_writer()` 吐审批事件 |

**实跑日志（节选）**：

```
=== invoke query='LangGraph 的缓存怎么做' thread=s1
  [node] search #1
  [node] search #2          ← RetryPolicy 自动重试
  [node] verify #1 score=None attempts=0
  [node] answer #1
  [node] verify #2 score=60 attempts=1
  [node] hitl #1
  最终: {'plan': 'web', 'score': 60, 'attempts': 2} 耗时 0.06s

=== invoke query='LangGraph 的缓存怎么做' thread=s2     ← 同输入不同线程
  [node] verify #3 ...      ← understand/search/answer 全部命中缓存，跳过了！
  耗时 0.01s
```

第二行是最有说服力的一行：**换了线程、同一个问题，understand / search / answer 三个节点一次都没执行**，只有不缓存的路由判断节点跑了。

**另一个坑（实测暴露）**：`verify` 里写 `s['score']` 直接 `KeyError: 'score'` —— 上游节点没写入这个 key 时，TypedDict 声明过也**不会有默认值**。要么 `s.get("score")`，要么在初始 state 里给全默认值。

**缓存 + 条件边的相互作用**（实测，比想象中微妙）：

`s3`（短 query，走 `answer → verify → 打回 answer`）里 `answer` **连跑 3 次都没命中缓存**，原因：
- `verify` 回跳时 `Command(update={"score": ...})` → **输入状态变了** → key 变 → 必然 miss；
- 就算状态不变，**`answer` 自己的输出没变**（占位实现），重算结果一样 —— 这是个"缓存该命中却没命中"的假象，实战里 `verify` 打回时通常还会带上反馈文本，输入本就应该变。

> **结论：缓存不是"结果 idempotent"，而是"输入相同才不重算"。循环里回跳几乎必 miss，别指望它省算力。**

---

## 六、组合与优先级

1. **节点挂了先重试、重试成功再写缓存**（缓存只存成功结果；失败不会被缓存住反复命中）。
2. `retry_policy` 与 `cache_policy` 同一节点实测共存正常（实验四 `both` 节点：第一次跑、第二次命中）。
3. `Command` 与 `cache_policy` 并存：**缓存的是节点返回值（含 `Command`）** → 命中时**连跳转方向一起复用**。这很强大也很危险：路由逻辑依赖的东西如果没进缓存 key（比如某个全局开关），改了会一直走老路线。**这种情况请关掉缓存或自定义 `key_func`。**
4. `interrupt()`（HITL）节点**不要挂缓存**——人工输入不可能相同。

---

## 七、踩坑清单

| # | 坑 | 现象 | 解法 |
|---|---|---|---|
| 1 | `ValueError`/`RuntimeError`/`TimeoutError` 配 RetryPolicy 不重试 | 只跑一次就抛 | 明白默认黑名单，显式 `retry_on=(...)` |
| 2 | 只在节点写了 `cache_policy`，`compile()` 没给 `cache=` | 静默不生效，每次都重算 | 两处都要写 |
| 3 | 以为缓存是按 `thread_id` 隔离的 | 换线程仍然命中，跨用户串答案 | 这是特性；要隔离就自定义 `key_func` 带上 thread |
| 4 | 给有副作用的节点加缓存 | 发消息/下单被"跳过" | 只缓存纯计算节点 |
| 5 | `Command(goto)` 和静态边并存 | 两条路都跑 | 想独占路由就别注册静态出边 |
| 6 | `stream_mode="values"` 第一条是初始态 | 误以为节点多跑了一次 | 正常现象，先过滤首帧 |
| 7 | custom writer 的内容想去 state 里拿 | 拿不到 | 要留痕就 return，writer 只是旁路 |
| 8 | 重试节点里已发过外部消息 | 重复发送 | 副作用外置 / 幂等 / 去重键 |
| 9 | TypedDict 声明了字段但初始 state 没给 | 上游没写就是 `KeyError` | `s.get(k)` 或初始值补全 |
| 10 | 循环里期待缓存命中 | 回跳后输入变了，必然 miss | 接受；循环靠缩短轮次省钱，不靠缓存 |

---

## 八、自检问题

1. `stream_mode="updates"` 和 `"values"` 拿到的同一个节点的值，差在哪里？
2. 为什么 `values` 模式的第一条 chunk 是"没有节点名"的初始 state？
3. `get_stream_writer()` 写出去的内容会进 state 吗？如果业务要求"进度要能在历史里回放"，该怎么写？
4. `Command(goto="y")` 与 `add_conditional_edges` 相比，多出来的能力是什么？（两个）
5. `Command(goto=[Send(...)])` 比在路由函数里返回 `[Send(...)]` 好在哪？
6. 缓存的 key 由什么构成？`thread_id` 参与吗？为什么这样设计是合理的？
7. 为什么 LangGraph 默认**不**重试 `ValueError`？又为什么 `TimeoutError` 也被"误伤"？上生产要怎么写？
8. 重试作用在哪一层？为什么这决定了节点必须幂等？
9. 一个节点同时挂 `cache_policy` 和 `Command` 会有什么诡异后果？
10. `RetryPolicy` / `CachePolicy` / 条件边重试计数（state 里的 `attempts`）三者分别在解决什么层次的问题？

---

## 附：实验脚本

四个脚本均在本机 `langgraph 1.2.16` 实跑通过：

- **exp1_output.py** —— `stream_mode` 各模式对照 + `Command(goto)` 覆盖静态边（含并存坑）+ `goto=[...]` 并行 + `goto=[Send...]` 动态扇出
- **exp2_cache_retry.py** —— `CachePolicy` 命中/跨线程/不同输入/TTL 过期 + `RetryPolicy` 成功恢复/耗尽/未配置/`ValueError` 默认不重试/缓存重试同挂
- **exp3_stream.py** —— `get_stream_writer` custom 流不从 state 漏出 + `Command(goto=END)` 提前终止
- **exp4_workflow.py** —— 五节点实战图：understand/Command 路由 + search 自动重试 + 三节点缓存 + verify 回跳上限 + hitl 审批

<details>
<summary>exp2 关键实测输出</summary>

```
[run] slow #1
[run] llm #1
invoke(t1) -> {'text': 'HELLO!'} 耗时 0.309s
invoke(t1) -> {'text': 'HELLO!'} 耗时 0.005s
invoke(t2 不同 thread) -> {'text': 'HELLO!'} 耗时 0.004s
[run] slow #2
invoke(不同输入) -> {'text': 'WORLD!'} 耗时 0.306s
等待 2.5s 让 ttl=2 的缓存过期 ...
[run] slow #3
invoke(TTL 过期后) -> {'text': 'HELLO!'} 耗时 0.306s
CALLS = {'slow': 3, 'llm': 2}
```
</details>

---

## 🔗 衔接

- **往回**：[LangGraph（一）图基础与状态管理](langgraph-01-图基础与状态管理.md)——`stream_mode` 与 checkpointer 都在那里起头；本篇把"输出"讲透。
- **往回**：[LangGraph（二）进阶建图](langgraph-02-进阶建图-defer-条件边-sequence-router-send.md)——`Send` 动态扇出；本篇给了它的 `Command` 版本。
- **往回**：[LangGraph（三）静态扇入](langgraph-03-静态扇入-与扇入与或扇入.md)——`Command(goto=[...])` 并行派发后，收齐仍靠与扇入。
- **横向**：[LangChain（五）Middleware](../tools/langchain-05-middleware.md)——Middleware 的 `ToolRetryMiddleware` / `ModelRetryMiddleware` 是**模型与工具层**的重试，本篇 `RetryPolicy` 是**节点层**的重试，别混。
- **往前**：`interrupt()` + `Command(resume=...)` 做真正的 HITL（本篇 `hitl` 节点只是规则模拟）；Subgraph 与 `Command(graph=PARENT)` 跨图跳转；`durability` 模式与持久化 cache（Redis/Postgres）。
