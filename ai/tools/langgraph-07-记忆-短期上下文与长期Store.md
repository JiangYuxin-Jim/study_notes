# LangGraph（七）记忆系统：短期（环境上下文）vs 长期（Store）

> 环境：本机 `langgraph 1.2.16` + `langgraph-checkpoint 4.3.0`，以下代码全部实测通过。
> 承接（五）持久化 checkpointer 与（六）replay/fork：本篇讲**「记忆」到底该怎么分层**——不是所有东西都塞进 state。

---

## 一、一句话结论

| | 短期记忆（Short-term） | 长期记忆（Long-term） |
|---|---|---|
| 存什么 | **当前这次会话/任务的上下文**（消息、草稿、中间结果） | **跨会话沉淀的事实与经验**（用户画像、偏好、领域知识） |
| 怎么存 | `checkpointer` → 挂在 `thread_id` 上 | `Store` → 按 **namespace** 组织，与线程无关 |
| 谁说它是"记忆" | 是「**环境上下文**」——本质是 state 的历史快照 | 是真正的**记忆**——显式读写、可检索、可遗忘 |
| 生命周期 | 线程内（可跨进程，但**跨线程不通**） | 进程/线程无关，**用户级/租户级**共享 |
| 检索方式 | 按 `thread_id` 直取，全量喂回 | `search(namespace, query=/filter=, limit=)`，按需取片段 |
| 典型失败 | 聊到第 100 轮上下文爆了 | 用户换个会话，AI 又"第一次见你" |

> **核心心智模型：checkpointer 是录音带，Store 是笔记本。**
> 录音带忠实记录这次对话说了什么；笔记本记下「这个人是谁、他喜欢什么」，下次开新会话直接翻笔记本。

**为什么必须分两层**：把长期事实塞进 state，等于让每轮对话都拖着全部历史走——上下文越来越长（对照 hello-agents 第九章：n² 注意力稀释 = 上下文腐蚀），还会因为 `thread_id` 隔离导致换会话即失忆。反过来把会话流水全塞进 Store，又变成把笔记本当录音带用，检索噪声爆炸。**分层不是可选优化，是结构上的必需。**

---

## 二、短期记忆 = checkpointer（环境上下文）

### 2.1 本质：state 的版本化快照

（五）已实测：每个 super-step 存一帧 State，`parent_checkpoint_id` 串成链，`thread_id` 做索引。所以「短期记忆」在 LangGraph 里的实现**就是**靠 `thread_id` 反复 `invoke` 同一条链，让 state（尤其是 messages）累积。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class S(TypedDict):
    messages: Annotated[list, add_messages]

def chat(state: S):
    return {"messages": [f"(echo) {state['messages'][-1]}"]}

g = StateGraph(S); g.add_node("chat", chat)
g.add_edge(START, "chat"); g.add_edge("chat", END)
app = g.compile(checkpointer=InMemorySaver())

cfg = {"configurable": {"thread_id": "t1"}}
for text in ["我叫小明", "我住在杭州", "我刚才说我叫什么？"]:
    out = app.invoke({"messages": [text]}, cfg)
    print(out["messages"][-1])
# → 第 3 轮仍在同一 thread_id 上，state["messages"] 里前两轮的 4 条消息都还在
```

### 2.2 关键认知：`thread_id` 是新旧记忆的**唯一开关**

```python
app.invoke({"messages": ["我刚才说我叫什么？"]}, {"configurable": {"thread_id": "t2"}})
# → 全新线程，messages 里只有这一条，模型"完全不认识你"
```

这就是「换设备/换会话就失忆」的根源——**不是 bug，是 checkpointer 的设计边界**。

### 2.3 「环境上下文」这个词的准确含义

教程里把短期记忆叫 **environment context** / 运行时上下文，指的是：**当前执行环境里所有能让 LLM 做对判断的信息**。它由三块拼起来：

1. **state 里的会话数据**（messages、草稿字段）
2. **`Runtime.context`** —— `invoke(..., context=Ctx(...))` 传进来的静态业务上下文（用户 id、租户、权限、语言），**不进 state、不写 checkpoint**，每次调用现传
3. **`Runtime.store`** —— 长期记忆的入口（下一节）

```python
from dataclasses import dataclass
from langgraph.runtime import Runtime

@dataclass
class Ctx:
    user_id: str
    lang: str = "zh"

def node(state: S, runtime: Runtime[Ctx]):
    print(runtime.context.user_id, runtime.context.lang)   # → 可以拿到
    print(runtime.store)                                    # → Store 实例（compile 时传了才有）
```

> **`Runtime.context` 实测要点**：它是 `context_schema=Ctx` 声明的强类型对象，`StateGraph(S, context_schema=Ctx)` 注册后节点第二参自动注入。**别把 user_id / tenant 塞进 state** —— 它们不是"状态"，是被环境携带的常量，塞进 state 会被 checkpoint 冗余存 N 份。

### 2.4 短期记忆的容量治理

聊天久了 messages 会撑爆窗口，三条常规手段（都在 LangGraph 里现成）：

| 手段 | 做法 | 代价 |
|---|---|---|
| **裁剪** | 只保留最近 N 条 / 按 token 数截断 | 丢早期信息，且可能截断 tool_call 与 ToolMessage 的配对 → 报错 |
| **摘要** | 用 LLM 把老消息压成一段 summary 存 state 单独字段 | 多一次 LLM 调用；细节丢失 |
| **卸载到长期** | 把值得记的事实写进 Store，state 里只留指针 | 需要设计"什么值得记"，见第三节 |

实战推荐组合：**state 里 `messages` 保留近 K 轮 + `summary` 字段累积摘要 + 关键事实写 Store**。这就是 hello-agents 第九章 GSSC 流水线里 Gather/Select/Compress 三段的工程版。

---

## 三、长期记忆 = `BaseStore`

### 3.1 数据模型：namespace 是目录，key 是文件

```python
store.put(namespace: tuple[str, ...], key: str, value: dict)
store.get(namespace, key) -> Item | None
store.search(namespace, query=None, filter=None, limit=10) -> list[SearchItem]
store.delete(namespace, key)
store.list_namespaces(prefix=("memories",))
```

- **namespace 是元组**，用 `("/".join)` 的层级思维理解：`("memories", "u1")` = `/memories/u1/`
- **key 是字符串**，同一 namespace 下唯一，`put` 同 key = 覆盖
- **value 是 dict**，会被 JSON 序列化（生产环境慎放不可序列化对象）
- **`SearchItem`** 有 `.key` / `.value` / `.score` / `.namespace` / `.created_at` / `.updated_at`

实测输出：

```python
store.put(("memories","u1"), "profile", {"text":"用户是后端工程师，喜欢 Python，讨厌啰嗦"})
store.search(("memories","u1"))
# → [Item(namespace=('memories','u1'), key='profile', value={...})]
store.search(("memories","u2"))   # → []   天然多租户隔离
store.list_namespaces(prefix=("memories",))
# → [('memories','u1')]
```

> **坑 1**：`list_namespaces()` 的唯一参数是**关键字参数** `prefix=`，位置传参会 `TypeError`。
> **实签名**：`list_namespaces(*, prefix=None, suffix=None, max_depth=None, limit=100, offset=0)`

### 3.2 节点里怎么拿到 store

三种写法，实测只有后两种在节点内可靠：

```python
# ✅ 写法 A：Runtime 注入（推荐，类型安全）
def node(state: S, runtime: Runtime[Ctx]):
    store = runtime.store

# ✅ 写法 B：contextvar 取
from langgraph.config import get_store
def node(state: S):
    store = get_store()

# ⚠️ 写法 C：闭包捕获 compile 之前的外部变量
```
无论哪种，**`compile(store=...)` 必须传**，否则 `runtime.store` 为 `None`。

```python
app = g.compile(checkpointer=InMemorySaver(), store=store)
```

### 3.3 实现选型

| 实现 | 包路径 | 特点 |
|---|---|---|
| `InMemoryStore` | `langgraph.store.memory` | 字典实现，进程内，测试用 |
| `PostgresStore` | `langgraph.store.postgres` | 生产首选，**要 `setup()`**，与 `PostgresSaver` 同一连接池 |
| `SqliteStore` | `langgraph.store.sqlite` | 单机持久化，轻量 |

> **坑 2（实测）**：`InMemoryStore` **不支持 TTL**。`store.put(ns, key, value, ttl=0.1)` 直接
> `NotImplementedError: TTL is not supported by InMemoryStore`。
> `supports_ttl` 属性可以查；TTL 只在 Postgres/Sqlite Store 上可用（清理"我这周的兴趣"这类易腐记忆）。

---

## 四、语义检索：Store 的杀手锏

不给 `query` 时 `search` 只是**按 namespace 罗列**；给了 `query` 才会做**向量相似度排序**——这才是"长期记忆"真正有用的地方（不然每次都得把整个 namespace 全读出来塞 prompt）。

### 4.1 索引要在 put 时声明

```python
from langgraph.store.memory import InMemoryStore
from langchain_core.embeddings import Embeddings

store = InMemoryStore(index={"embed": my_embeddings, "dims": 64})

store.put(ns, "1", {"text": "用户喜欢 Python 编程 脚本"}, index=["text"])   # ← index 指定哪些字段进向量
store.search(ns, query="Python 脚本怎么写", limit=2)
```

实测（用 64 维 hash embedding 做可控验证，dims 必须与 embed 输出维度一致）：

```
query='Python 脚本怎么写'
    key=1  '用户喜欢 Python 编程 脚本'  score=0.667
    key=3  '用户周末喜欢爬山 徒步'      score=0.24
query='宠物 猫'
    key=2  '用户养了一只叫豆豆的猫'      score=0.231
```

**要点**：
- `index=[...]` 是 **put 阶段的声明**，不声明就不会被检索到（静默，不报错）
- `index=False` 可显式关闭某条记录的索引
- **`dims` 必须与 embedding 输出维度严格一致**，否则报错或检索全 0
- `score` 越高越相关；跨模型不可比，**别拿来当绝对阈值用**——生产里通常取 top-k + 一次性注入

### 4.2 query（语义）vs filter（精确）—— 两者可叠加

```python
# 语义模糊找
store.search(("memories","u1"), query="写代码", limit=5)

# 精确条件找（等值匹配）
store.search(("memories","u1"), filter={"text": "用户在做 LangGraph 学习笔记"}, limit=1)
# → [{'text': '用户在做 LangGraph 学习笔记'}]
```

**选型**：事实型（"用户等级=VIP"、"tenant=acme"）用 `filter`；模糊回忆（"他之前提过什么宠物"）用 `query`。生产最常见是 `namespace` 做用户隔离 + `filter` 做硬条件 + `query` 做软排序。

---

## 五、把长期记忆接进图的两个时机

### 5.1 读：进模型之前注入系统提示（实测）

```python
def call_model(state: S, runtime: Runtime[Ctx]):
    st = runtime.store
    hits = st.search(("memories", runtime.context.user_id), limit=5)
    mem_text = "\n".join(f"- {i.value['text']}" for i in hits)
    system = f"你了解用户以下背景：\n{mem_text}" if mem_text else "暂无用户背景"
    # → system + state["messages"] 一起发给模型
```

实测输出：

```
== 用户 u1 ==
  系统提示注入的记忆:
- 用户是后端工程师，喜欢 Python，讨厌啰嗦
  当前消息: ['帮我写个脚本']
== 用户 u2（无记忆）==
  系统提示注入的记忆:          ← 空
  当前消息: ['帮我写个脚本']
```

**同一张图、同一个代码路径，仅因 `user_id` 不同，注入的记忆不同** —— 这就是长期记忆的价值，且它和 `thread_id` 完全解耦。

### 5.2 写：异步/后台写入，别堵主链路

三个写入时机，各有取舍：

| 时机 | 做法 | 权衡 |
|---|---|---|
| **主图内同步写** | `store.put()` 直接在节点里 | 简单、一致性强；但每次对话都多一次写，且写失败会拖垮回复 |
| **后置节点写** | 图尾加 `save_memory` 节点 | 与主流程解耦，可加条件（只写"值得记"的） |
| **后台独立写** | 用 `update`/cron/队列另跑一个图 | 不拖慢响应，最贴近生产；但需要并发与去重设计 |

```python
from datetime import datetime
store.put(("memories","u1"), f"mem-{datetime.now().timestamp():.0f}",
          {"text":"用户在做 LangGraph 学习笔记"})
len(store.search(("memories","u1")))   # → 2  累积式，不覆盖
```

**key 设计是最容易踩坑的地方**：

- **累积型**（事件、日志）：key 用时间戳/UUID → 只增不改，需要定期合并
- **覆盖型**（用户画像、偏好）：key 固定如 `"profile"` → 每次 `put` 全量覆盖，永远只有一条

> **坑 3**：覆盖型用时间戳 key 会越堆越多、语义检索时同一件事被检索出 10 条；累积型用固定 key 会只剩最后一条。**先想清楚这条记忆是"事实快照"还是"事件流水"。**

### 5.3 遗忘：长期记忆必须能删

```python
store.delete(("memories","u1"), "k1")             # 精确删
# 生产：定期按 list_namespaces + search 清过期；或 Postgres/Sqlite Store 用 ttl
```
对照 hello-agents 第八章三种遗忘策略（时间衰减 / 重要性 / 容量淘汰）：Store 只提供原语，**策略得自己写**。

---

## 六、两层记忆的对照总表

| 维度 | checkpointer（短期） | Store（长期） |
|---|---|---|
| 索引键 | `thread_id` | `namespace` + `key` |
| 内容 | 完整 state 每步快照 | 人工设计的 value dict |
| 写入方式 | 自动（框架每 super-step 写） | 手动（节点内 `put`） |
| 读取方式 | 自动回灌整个 state | 手动 `search` 取片段 |
| 隔离粒度 | 线程 | 用户 / 租户 / 业务域（自己定） |
| 相似度检索 | ❌ | ✅（配 embeddings） |
| 适合放 | messages、流程中间态、待审批草稿 | 用户画像、偏好、历史决策、领域知识 |
| 常见误用 | 塞用户 id、租户、常量配置 | 塞整轮对话原文 |
| 生产落地 | PostgresSaver + 连接池 | PostgresStore（同一数据库） |

**一句话判决：state 装"这一趟的行李"，Store 装"这个人是谁"。**

---

## 七、实战骨架：两层记忆一起用

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

DB = "postgresql://user:pwd@localhost:5432/agent"

with PostgresStore.from_conn_string(DB) as store:
    store.setup()
    with PostgresSaver.from_conn_string(DB) as saver:
        saver.setup()
        app = g.compile(checkpointer=saver, store=store)

        # 短期：同 thread_id 累积会话
        cfg = {"configurable": {"thread_id": "conv-2026-11-10-001"}}
        # 长期：同 namespace 跨会话共享
        ctx = Ctx(user_id="u1")

        app.invoke({"messages": ["帮我看看上次那个方案"]}, cfg, context=ctx)
```

**要点**：
- 两个 `setup()` 都得调（Store 也有一张自己的表）
- 两者可以共用同一个 Postgres 库，`thread_id` 与 `namespace` 各管一摊
- 生产用 `ConnectionPool` + `Async*` 版本，理由同（五）

---

## 八、踩坑清单（全部本机实测）

1. `InMemoryStore.put(..., ttl=...)` → `NotImplementedError`，TTL 只在持久化 Store 上支持
2. `store.list_namespaces(("memories",))` → `TypeError`，必须 `prefix=(...)` 关键字传
3. `store.search` 不传 `query` 只是罗列，**不会做相似度排序**；传了 query 但 put 时没 `index=[...]` → 查不到（静默返回空）
4. `index={"dims": N}` 必须与 embedding 实际维度一致
5. `compile` 不传 `store=` → `runtime.store is None`，节点里一取就炸
6. `runtime.context` 要在 `StateGraph(..., context_schema=Ctx)` 注册后才有；没注册拿不到自定义字段
7. 用 dataclass 做 State 时访问是 `state.msgs`，**不是 `state["msgs"]`** → 写成 dict 下标直接 `TypeError: 'S' object is not subscriptable`
8. 覆盖型记忆用时间戳 key → 重复堆积；累积型用固定 key → 只剩最后一条
9. 短期记忆裁剪 messages 时，别把 `tool_call` 与对应 `ToolMessage` 拆开（LangChain 会因 id 配对失败报错）

---

## 九、和前面章节的连线

- **（五）持久化**：checkpointer 解决了"活过进程"，本篇解决"活过会话"——**两个不同维度**
- **（六）replay/fork**：fork 改的是短期 state；如果要让"修正后的事实"永远生效，得同时 `put` 进 Store
- **LangChain（四）Agent `checkpointer + thread_id`**：那是短期记忆的封装版
- **hello-agents 第八章**：四种记忆类型（工作/情景/语义/感知）→ 这里的工作记忆 = state，情景/语义 = Store
- **hello-agents 第九章 GSSC**：Gather 五源里"记忆"那一路，生产实现就是 `store.search(...)` 取 top-k
- **learn Claude Code 第八章记忆系统**：CLAUDE.md 那种"项目级长期记忆"≈ Store 的一个固定 namespace

---

## 十、下一步

- **Subgraph 子图** + `interrupt()` 真 HITL（长期记忆在审批场景里能记住"上次用户批了什么"）
- **手搓 ReAct 图**对照 `create_agent`，把记忆层加进去
- LangChain RAG 线：Embeddings → VectorStore → Retriever（Store 的向量检索只有一层，专业 RAG 要更强）
