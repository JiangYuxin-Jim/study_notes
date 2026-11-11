# LangGraph（八）中断、工具节点与流式执行

> 学习日期：2026-11-11
> 环境：本机 `langgraph 1.2.16` + `langgraph-checkpoint 4.3.1` + `langchain-core 1.7.0`，**下述实验全部实跑，输出原样贴出**
> 承接：[（五）持久化](langgraph-05-持久化-内存与PostgreSQL.md)（checkpointer 是中断的地基）、[（六）replay/fork](langgraph-06-错误回复-replay与fork.md)（resume 的另一半）、[（七）记忆](langgraph-07-记忆-短期上下文与长期Store.md)
> 一句话：**中断（interrupt）让图可以"停下来等人"；工具节点（ToolNode）让"调工具"变成图上的一格；流式（stream_mode）让外面能"边跑边看"。这三件事凑在一起，才是能干活的 Agent。**

---

## 〇、先建立一张全局图

```
       ┌──────────── interrupt 让图停在这里等人 ────────────┐
       │                                                    │
   START → model ──(有 tool_calls)──→ tools ──→ model ──→ END
             │                          │
             └──(无 tool_calls)──→ END   └── 工具内部也可能 interrupt
                                                         │
   外面通过 stream_mode 实时看到：updates / values / messages / custom
```

三者的关系：

| 机制 | 解决什么问题 | 挂在哪 |
|---|---|---|
| **interrupt()** | 图跑到一半需要**人的决定**（审批 / 补充信息 / 纠偏） | 节点**内部**任意位置，抛异常式暂停 |
| **ToolNode** | 模型说"要调工具"，谁去执行、怎么把结果塞回 messages | 图中一个**普通节点** |
| **stream_mode** | 外部（CLI / Web UI）怎么实时看到过程 | 调用方 `graph.stream(...)` |

**关键认知：interrupt 不是"返回一个值让你下次从这儿继续"，而是"整个节点从开头重跑一遍"。** 这条搞错了，所有副作用都会重复执行。后面第 2 节全是围绕这句话的坑。

---

## 一、中断：`interrupt()` + `Command(resume=...)`

### 1.1 最小可用例子（实跑）

核心三点：**`interrupt()` 抛异常 → 图暂停并把"停在哪"存进 checkpoint → 用 `Command(resume=值)` 从那儿接着跑。**

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

class S1(TypedDict):
    action: str
    amount: int
    log: Annotated[list, operator.add]

def plan_node(state: S1):
    return {"action": "退款", "amount": 1280, "log": ["plan: 生成退款单"]}

def approve_node(state: S1):
    # 关键：interrupt() 抛异常 → 图暂停 → checkpoint 保存 → 返回 __interrupt__
    decision = interrupt({
        "question": f"确认要{state['action']} {state['amount']} 元吗?",
        "amount": state["amount"],
    })
    return {"log": [f"approve: 用户答复={decision}"]}

def exec_node(state: S1):
    return {"log": [f"exec: 执行{state['action']} {state['amount']}"]}

b1 = StateGraph(S1)
b1.add_node("plan", plan_node); b1.add_node("approve", approve_node); b1.add_node("exec", exec_node)
b1.add_edge(START, "plan"); b1.add_edge("plan", "approve"); b1.add_edge("approve", "exec"); b1.add_edge("exec", END)
g1 = b1.compile(checkpointer=InMemorySaver())

cfg = {"configurable": {"thread_id": "t1"}}
r = g1.invoke({"log": []}, cfg)
print(r)
print(g1.get_state(cfg).tasks)
```

实测输出：

```
--- 第一次 invoke：图在 approve 处暂停 ---
返回值: {'action': '退款', 'amount': 1280, 'log': ['plan: 生成退款单'],
        '__interrupt__': [Interrupt(value={'question': '确认要退款 1280 元吗?', 'amount': 1280},
                                    id='7413310cfdc5338e3bb2fe1569b49063', response_schema=None)]}
__interrupt__: (PregelTask(id='bc3dc5e6-...', name='approve', path=('__pregel_pull', 'approve'),
                interrupts=(Interrupt(value={'question': '确认要退款 1280 元吗?', ...}),), ...),)
--- resume 后 ---
['plan: 生成退款单', 'approve: 用户答复=同意', 'exec: 执行退款 1280']
```

### 1.2 三个返回值的区别（容易混）

| 从哪看 | 拿到什么 |
|---|---|
| `invoke()` 返回值里的 `__interrupt__` | `[Interrupt(value=..., id=...)]`，**下次 resume 要用 id** |
| `graph.get_state(cfg).tasks` | pending 的 `PregelTask` 列表 —— `name` 告诉你卡在哪个节点 |
| `graph.get_state(cfg).next` | 下一步要跑谁，如 `('approve',)`；跑完变 `()` |

> `tasks` 才是"我在等什么"的权威来源；`__interrupt__` 只是同一信息的便捷副本。

### 1.3 resume 的三种写法

```python
# ① 单中断：直接给值
g.invoke(Command(resume="同意"), cfg)

# ② 多中断：必须按 interrupt id 给 dict（否则报错，见 1.5）
g.invoke(Command(resume={id_a: "A同意", id_b: "B同意"}), cfg)

# ③ 顺着流：stream 也能 resume，事件继续往外吐
for chunk in g.stream(Command(resume="同意"), cfg, stream_mode="custom"): ...
```

---

## 二、最重要的一个坑：resume 会**整个节点重跑**

### 2.1 实测：副作用执行了两次

```python
calls = {"n": 0}

def counting_node(state):
    calls["n"] += 1                    # 副作用！
    ans = interrupt({"ask": "paused", "try": calls["n"]})
    return {"x": ans, "note": [f"节点第 {calls['n']} 次执行, 收到 {ans}"]}
```

实测输出：

```
node 执行次数 = 2 (中断前1次 + resume后整节点重跑1次)
最终: {'x': 42, 'note': ['节点第 2 次执行, 收到 42']}
```

**机制**：`interrupt()` 恢复时，LangGraph 并不是"从 interrupt 那一行往下执行"，而是**重新进入整个节点函数**，这次 `interrupt()` 不再抛异常，直接返回你给的 resume 值。

**所以铁律：**

1. `interrupt()` **之前**的代码必须**幂等 / 无副作用**（不能发邮件、不能扣款、不能写库、不能 `print` 到业务日志）
2. **副作用一律放在 `interrupt()` 之后**
3. 需要"记录到第几轮"这类状态，**写在 state 里**让它随 checkpoint 恢复，而不是靠 Python 变量

对比写法：

```python
# ❌ 错：先发短信再中断 → 重跑会发两条
def bad(s):
    send_sms(s["phone"], "已受理")
    ok = interrupt({"q": "确认发送?"})
    return {"log": [ok]}

# ✅ 对：中断后再做副作用
def good(s):
    ok = interrupt({"q": "确认发送?"})
    if ok == "OK":
        send_sms(s["phone"], "已受理")
    return {"log": [ok]}
```

### 2.2 多次中断的幂等写法（循环里 interrupt）

如果节点在一个循环里反复被中断，"第几次"必须来自 **state**，不能来自闭包变量：

```python
def review_loop(s):
    i = len(s.get("approved", []))          # ← 从 state 推，天然可恢复
    d = interrupt({"round": i, "item": s["items"][i]})
    return {"approved": [d]}
```

实测三轮全过：

```
第1次暂停，待审: [{'round': 0, 'item': '条目A'}]
第2次暂停，待审: [{'round': 1, 'item': '条目B'}]
第3次暂停，待审: [{'round': 2, 'item': '条目C'}]
全部完成: ['通过A', '通过B', '通过C']
```

---

## 三、checkpointer：中断的**物理前提**

### 3.1 没有 checkpointer 时到底发生什么（实测纠正了一个常见误解）

很多人以为"没 checkpointer 就报错"。**实测：`invoke` 不报错，照样返回 `__interrupt__`，但 `resume` 时报错。**

```
invoke ok, interrupt: True
RESUME RAISED RuntimeError : Cannot use Command(resume=...) without checkpointer
```

结论：**interrupt 只要被调用就一定"停"；但"停下来之后能不能接上"，取决于有没有 checkpointer。** 没有的话图就永远停在那一帧，谁也接不回去。

### 3.2 真正的中断语义要求：状态必须活过进程

用 sqlite 模拟"进程退出再重启"：

```python
# 第一次：跑到中断，返回 __interrupt__
r = g.invoke({"log": []}, cfg)
conn.close()          # ← 模拟进程 A 退出

# 「新进程」重新打开同一个 sqlite 文件
conn2 = sqlite3.connect(DB, check_same_thread=False)
g2 = b.compile(checkpointer=SqliteSaver(conn2))
r2 = g2.invoke(Command(resume="驳回"), cfg)   # ← 照样能接上
```

实测输出：

```
A) 第一次： ['plan'] | 中断: [{'q': '确认退款 1280元?'}]
   快照里 pending 节点: ['approve']
   下一步: ('approve',)
B) 重新打开数据库后 next = ('approve',) | 中断还在: [{'q': '确认退款 1280元?'}]
C) 跨进程序列 resume → ['plan', 'approve:驳回', 'exec']
D) 终态 next = ()
```

**这才是 HITL（Human-In-The-Loop）能落地的真正原因**：人的审批可能隔几小时才回来，进程早重启了八百遍。`InMemorySaver` 只适合本地调试，**生产必须 Postgres / Redis / SQLite 这类持久 saver**（详见（五）篇）。

### 3.3 同一 super-step 多个中断：必须按 id resume

用 `Send` 并行扇出两个都要审批的节点：

```
中断列表: [{'node': 'a', 'q': 'A批准?'}, {'node': 'b', 'q': 'B批准?'}]
pending tasks: [('fan_a', [{...}]), ('fan_b', [{...}])]
```

此时直接 `Command(resume="同意")` 会炸：

```
RuntimeError: When there are multiple pending interrupts, you must specify
the interrupt id when resuming.
```

正确做法是按 id 逐个喂，**可以分多次 resume**：

```python
ints = {i.value["node"]: i.id for i in r["__interrupt__"]}
r = g.invoke(Command(resume={ints["a"]: "A同意"}), cfg)
# → log = ['a:A同意'] | 剩余中断: [{'node': 'b', 'q': 'B批准?'}]
r = g.invoke(Command(resume={ints["b"]: "B同意"}), cfg)
# → log = ['a:A同意', 'b:B同意'] | 还有中断? False
```

> 这其实就是"**分批审批**"的实现方式：UI 上先批 A，B 留着，批完再续。

### 3.4 `@entrypoint` 函数式里也能用

```python
@entrypoint(checkpointer=InMemorySaver())
def wf(x: int):
    y = double(x).result()
    ok = interrupt({"q": f"{x} 翻倍为 {y}，接受吗?"})
    return {"result": y if ok == "接受" else None}
```

```
第一次: {'__interrupt__': [Interrupt(value={'q': '3 翻倍为 6，接受吗?'}, ...)]}
resume: {'result': 6}
```

**图式 / 函数式只是外壳，中断的语义完全一致**——因为底层都是同一个 Pregel 循环。

---

## 四、工具节点：`ToolNode`

### 4.1 它在干什么

模型返回的 `AIMessage` 里带着 `tool_calls`（一个 `id/name/args` 列表）。`ToolNode` 干四件事：

1. 读最后一条消息的 `tool_calls`
2. **逐个（并行）执行**对应工具
3. 把每个结果包成 `ToolMessage(content=..., tool_call_id=..., name=...)`
4. 返回 `{"messages": [...]}`，靠 `add_messages` reducer 追加进 state

```python
from langgraph.prebuilt import ToolNode

@tool
def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b

@tool
def get_weather(city: str) -> str:
    """查询城市天气"""
    return f"{city}: 晴 22℃"

tool_node = ToolNode([add, get_weather])
```

实测（一条 AIMessage 里两个 tool_calls）：

```
--- ToolNode 并行执行两个 tool_call ---
  call_1 add -> 7
  call_2 get_weather -> 杭州: 晴 22℃
```

> **并行**执行，但消息顺序按 `tool_calls` 列表顺序落进 messages。

### 4.2 `tools_condition`：要不要去工具节点

```python
from langgraph.prebuilt import tools_condition

b.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
```

它就是"读最后一条消息有没有 `tool_calls`"，有 → `"tools"`，无 → `END`。

实测：

```
--- tools_condition 判定 ---
有 tool_calls -> 去 tools 节点, 结果: ['7', '杭州: 晴 22℃']
无 tool_calls -> 去 END, 消息数: 1
```

### 4.3 完整 Agent 骨架 = 三行边

```python
b = StateGraph(S)
b.add_node("model", model_node)
b.add_node("tools", tool_node)
b.add_edge(START, "model")
b.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
b.add_edge("tools", "model")          # ← 这一条就是"循环"
```

这五句，就是 `create_agent` 内部那张图的全部结构（对照 [LangChain（四）](../langchain/langchain-04-agents.md)）。

---

## 五、工具里中断 = 工具审批（HITL 的生产形态）

### 5.1 在 `@tool` 函数体里直接调 `interrupt()`

```python
@tool
def send_money(to: str, amount: int) -> str:
    """给某人转账（危险操作，需要人工审批）"""
    ok = interrupt({"tool": "send_money", "to": to, "amount": amount, "q": "允许这笔转账吗?"})
    if ok == "允许":
        return f"已向 {to} 转账 {amount} 元 ✅"
    return f"用户拒绝，转账取消 ❌"
```

实测：

```
--- 工具内 interrupt：图暂停 ---
  中断内容: [{'tool': 'send_money', 'to': '张三', 'amount': 500, 'q': '允许这笔转账吗?'}]
  pending 节点: ['tools']
  resume('允许') 后:
    send_money -> 已向 张三 转账 500 元 ✅
  resume('拒绝') -> 用户拒绝，转账取消 ❌
```

**注意 pending 是 `tools` 而不是工具名** —— 因为 ToolNode 是一个节点，它内部卡住了。

### 5.2 混合调用：一个危险一个安全

```
--- 混合调用：calc 先跑完，send_money 卡住 ---
  已产生的 ToolMessage: []
  中断: [{'tool': 'send_money', 'to': '李四', 'amount': 99, 'q': '允许这笔转账吗?'}]
  批准后: [('calc', '3'), ('send_money', '已向 李四 转账 99 元 ✅')]
```

⚠️ **第一轮里 `calc` 明明算完了，但 `已产生的 ToolMessage: []` —— 工具节点的返回值没写进 state。** 这是 ToolNode 的**原子性**：节点内任何一个工具中断，整个节点这一轮作废，全部结果都不落盘。

---

## 六、⚠️ 最隐蔽的坑：ToolNode 中断后**所有工具都会重跑一遍**

这是本篇最重要的实测结论。用带副作用的工具记录执行轨迹：

```python
calls = []

@tool
def slow_first(x: int) -> int:
    """第一个工具（会中断）"""
    calls.append("slow_first:enter")
    ok = interrupt({"q": "允许 slow_first 吗?"})
    calls.append(f"slow_first:resumed({ok})")
    return x * 10

@tool
def quick_second(y: int) -> int:
    """第二个工具（不中断）"""
    calls.append("quick_second:enter")
    return y + 1
```

**场景 A：第一个工具就中断**

```
【中断时】工具执行轨迹: ['slow_first:enter']
【resume 后】工具执行轨迹: ['slow_first:enter', 'slow_first:enter',
                          'slow_first:resumed(允许)', 'quick_second:enter']
```

→ `slow_first:enter` 出现了**两次**，但 `resumed` 只有一次（因为第一次在 interrupt 处抛异常就断了）。

**场景 B：先跑安全的、后跑危险的**

```
【中断时】轨迹: ['A', 'B:enter']        (A 已跑完但消息未落 state)
state 里的 ToolMessage: []
【resume 后】轨迹: ['A', 'B:enter', 'A', 'B:enter', 'B:resumed(允许)']
```

→ **`A` 执行了两次**。

**结论与应对：**

| 情况 | 后果 | 应对 |
|---|---|---|
| 工具是纯函数（查、算、读） | 重跑无害 | 不用管 |
| 工具有外部副作用（转账、发消息、写库） | **会重复执行一次** | 用**幂等键**（`request_id`）在外部去重 |
| 多个工具混合调用 | 前面跑完的也会重跑 | 把"需审批的工具"**单独一次调用**，别和别的混在一批 |

> 更稳的做法：**别在工具内部 interrupt**，而是把"审批"做成独立的 `approval` 节点，放在 model 和 tools 之间 —— 审批通过后再让 ToolNode 真正执行，ToolNode 内就没有中断，不会重跑。

---

## 七、流式执行：`stream_mode`

### 7.1 六种模式全景（本篇重点实测 4 种）

| mode | 每次吐什么 | 适合谁 |
|---|---|---|
| `updates` | `{节点名: 该节点返回的增量}` | **调试首选** |
| `values` | **完整 state 快照**（含初始态） | 要整体状态 / 渲染整页 |
| `messages` | `(token_chunk, metadata)` | 打字机效果 |
| `custom` | 节点内 `get_stream_writer()` 写出的任意对象 | **进度条 / 业务事件** |
| `debug` | 极详细事件 | 排查执行细节 |
| `checkpoints` | checkpoint 事件 | 时间旅行 / 审计 |

> （四）篇已测过 updates/values/custom，本篇补上 **messages** 与**中断场景下的流行为**。

### 7.2 `updates` 的一个反直觉点

```python
for chunk in g1.stream(Command(resume="同意"), cfg, stream_mode="updates"):
    print(chunk)
```

实测是**空的**（原文输出为空行）。

**为什么**：`resume` 是对"已存在的 super-step"的补充输入，这一轮不是"新节点执行"。真正有输出的是 `values`：

```
--- stream_mode='values' (完整快照) ---
  log = ['plan: 生成退款单']
  log = ['plan: 生成退款单', 'approve: 用户答复=同意']
  log = ['plan: 生成退款单', 'approve: 用户答复=同意', 'exec: 执行退款 1280']
```

> resume 场景想看进度，**用 `values` 或 `custom`，别用 `updates`**。

### 7.3 `custom`：最实用的业务事件流

`get_stream_writer()` 拿到的是**当前节点的**写入器，写出去的东西**不进 state**：

```python
from langgraph.config import get_stream_writer

def custom_node(state):
    w = get_stream_writer()
    for i in range(3):
        w({"progress": i, "msg": f"处理第 {i} 步"})
    return {"msgs": ["done"]}
```

```
--- stream_mode='custom' (节点内自定义进度) ---
  {'progress': 0, 'msg': '处理第 0 步'}
  {'progress': 1, 'msg': '处理第 1 步'}
  {'progress': 2, 'msg': '处理第 2 步'}
```

### 7.4 结构化事件 + 中断同流（生产 UI 的正确姿势）

在节点里推带 `type` 的结构化事件，包括"我要中断了"：

```python
def ask_node(s):
    w = get_stream_writer()
    w({"type": "hitl", "msg": "等待人工确认"})
    d = interrupt({"q": "结果够用吗?"})
    return {"result": [f"人审:{d}"]}
```

```
--- custom 流：结构化事件 + 中断同流 ---
   {'type': 'start', 'msg': '开始检索'}
   {'type': 'progress', 'cur': 1, 'total': 3, 'msg': '翻到第 1 页'}
   ...
   {'type': 'hitl', 'msg': '等待人工确认'}      ← 前端收到这条就该弹审批框
```

**前端只需要认得 `type` 字段，不用判断图的结构。** 这是 SSE/WebSocket UI 最干净的接口设计。

### 7.5 多流并发：`stream_mode=["messages", "updates"]`

```python
for mode, chunk in g.stream(inp, cfg, stream_mode=["messages", "updates"]):
    if mode == "messages":
        c, meta = chunk          # ← 注意是二元组
        ...
    else:
        ...
```

实测（用 `GenericFakeChatModel` 造 token 流，不依赖真 API）：

```
--- stream_mode="messages"（token 级）---
  '中断是'
  ' '
  'LangGraph'
  ' '
  '里最难也最值钱的一块。'
  拼接: 中断是 LangGraph 里最难也最值钱的一块。

--- stream_mode=["messages","updates"] 同时多路 ---
  [messages] '中断是'
  ...
  [updates] keys=['llm']
```

> `messages` 模式下 chunk 是 `(AIMessageChunk, metadata)` 二元组，`metadata` 里有 `langgraph_node` 等定位信息。

### 7.6 ⚠️ resume 时会**重放**中断节点的 custom 事件

实测：

```
--- 第一轮 stream (custom) ---
   {'node': 'a', 'evt': '开始'}
   {'node': 'a', 'evt': '完成'}
   {'node': 'b', 'evt': '请求审批'}
--- resume 时 stream (custom) 会不会重放 a 的事件? ---
   {'node': 'b', 'evt': '请求审批'}       ← ⚠️ 又出现一次
   {'node': 'b', 'evt': '拿到答复:好'}
```

**原因**：resume 重跑中断节点，`interrupt()` 之前写的 custom 事件会再写一遍；而 `a` 节点因为已经有 checkpoint 结果，**不会**重跑，它的旧事件也不会重放（LangGraph 有"已完成节点不重放"的优化）。

**应对**：UI 端对 `hitl` 这类事件做**幂等**（按 interrupt id 去重），别指望"事件只来一次"。

---

## 八、把三者拼起来：一个带审批的 Agent

完整形态（model → tools → model 回环 + 工具内审批 + custom 事件）：

```python
b = StateGraph(S)
b.add_node("model", model_node)
b.add_node("tools", ToolNode([get_balance, transfer]))
b.add_edge(START, "model")
b.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
b.add_edge("tools", "model")
g = b.compile(checkpointer=InMemorySaver())
```

实测三个场景：

```
=== 场景1：查余额（无审批）===
  [custom] {'type': 'node', 'msg': '模型思考中'}
  [updates] model
  [updates] tools
  [custom] {'type': 'node', 'msg': '模型思考中'}
  [updates] model

=== 场景2：转账（触发审批中断）===
  中断: [{'type': 'tool_approval', 'tool': 'transfer', 'to': '王五', 'amount': 200, ...}]
  pending: ['tools']
  -- 拒绝 --
   ToolMessage: 用户拒绝转账
   AIMessage: 结果已拿到：用户拒绝转账

=== 场景3：批准 ===
   ToolMessage: 已转账 200 元给 王五
   AIMessage: 结果已拿到：已转账 200 元给 王五
```

注意场景 2/3：**拒绝之后 Agent 并没有崩**，它把 `ToolMessage("用户拒绝转账")` 喂回模型，模型正常总结 —— 这才是"人机协作"该有的样子，而不是一拒了之。

---

## 九、踩坑清单

| # | 坑 | 现象 | 解法 |
|---|---|---|---|
| 1 | 副作用写在 `interrupt()` 前 | 重跑时执行两次 | 副作用一律放 interrupt 之后 |
| 2 | 用闭包变量记录"第几轮" | resume 后数值错乱 | 从 state 推导 |
| 3 | 没 checkpointer | invoke 不报错、resume 报 `Cannot use Command(resume=...) without checkpointer` | 必配 saver，生产用持久版 |
| 4 | 多 pending 中断直接给标量 | `must specify the interrupt id` | `Command(resume={id: val})` |
| 5 | resume 时用 `stream_mode="updates"` | 收不到任何输出 | 改用 `values` / `custom` |
| 6 | 工具内 interrupt + 多工具混批 | 前面跑完的工具**重复执行** | 幂等键 / 审批拆成独立节点 |
| 7 | 以为 ToolNode 部分结果会落盘 | 中断那轮 `ToolMessage` 全空 | 节点是原子的，全成功或全不写 |
| 8 | UI 假设 custom 事件只来一次 | resume 时重复弹窗 | 按 interrupt id 去重 |
| 9 | `InMemorySaver` 上生产 | 重启即丢失，审批全废 | Postgres/Redis/SQLite saver |

---

## 十、和前面章节的连线

- **（二）`interrupt` 三铁律**：「必须 checkpointer」这条本篇实测修正为 —— **invoke 时不报错，resume 时才报**，且真正要求是"活过进程"
- **（五）持久化**：那里把 interrupt 当"能跨进程 resume"的能力，本篇展开成 **HITL 的完整语义**
- **（六）replay/fork**：`Command(resume=...)` 是 resume 分支；本篇的工具审批就是最典型的 resume 场景
- **（七）记忆**：审批可以读 Store 里的"上次用户批了什么"做**预判/自动放行** —— 长期记忆在 HITL 里的价值
- **LangChain（四）Agent**：本篇第 4.3 节的五行边，就是 `create_agent` 内部图
- **LangChain（五）Middleware**：`HumanInTheLoopMiddleware` 是工具审批的封装版，**底层用的正是本篇的 `interrupt()`**
- **learn Claude Code 第四章 Hook**：Claude Code 的 `PreToolUse` 权限弹窗 ≈ 工具节点审批；**本质是同一个设计，换框架不换思路**
- **hello-agents 第九章 JIT 上下文**：流式正是"渐进式披露"的传输层实现

---

## 十一、下一步

- **Subgraph 子图** + 父图/子图各自的中断如何处理（多层 resume 的 id 归属）
- **`Command(goto=[...])` 节点内静态并行分派**
- **手搓 ReAct 图**对照 `create_agent`，把中断与流式全接上
- **Postgres saver + FastAPI SSE** 做一个真能挂到网页上的审批 Agent
- LangChain RAG 线：Embeddings → VectorStore → Retriever

---

## 附：实验脚本

- `lg8_experiment.py` —— 基础中断 / 副作用重跑 / ToolNode 并行 / tools_condition / 四种 stream_mode
- `lg8_hitl2.py` —— sqlite 跨进程序列 resume / 循环多次 interrupt
- `lg8_tool_hitl.py` —— 工具内 interrupt（批准 / 拒绝 / 混合调用）
- `lg8_toolorder.py` —— ⭐ ToolNode 中断后**全工具重跑**的轨迹追踪
- `lg8_stream.py` —— custom 结构化事件 + 中断同流 + 多模式分派
- `lg8_replay.py` —— resume 时 custom 事件重放 / 无 checkpointer 行为
- `lg8_extra.py` —— 多 pending interrupt 按 id resume / `@entrypoint` 风格
- `lg8_agent.py` —— 完整带审批的 Agent 三场景
