# LangGraph · 持久化：内存 vs PostgreSQL

> 学习日期：2026-11-02
> 环境：本机 `langgraph 1.2.16` + `langgraph-checkpoint 4.3.0` + `langgraph-checkpoint-postgres 3.2.0`（psycopg 3.3.6 / psycopg_pool 3.3.3）+ 本机 PostgreSQL 15.19，**所有结论逐条实跑，输出贴在对应位置**
> 承接：[LangGraph（一）· 图基础与状态管理](./langgraph-01-图基础与状态管理.md)（checkpointer 在那里只是"知道有这么个东西"）→ [（二）进阶建图](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md)（`interrupt` 三铁律第一条：必须 checkpointer）→ [（四）控制流](./langgraph-04-控制流-输出-跳转-缓存-重试.md)（文末留的伏笔："`durability` 模式与持久化 cache（Redis/Postgres）"）
> 一句话：**本篇把"状态存在哪"这件事从"一个参数"讲成"一条选型决策"。**

---

## 〇、先说结论

| | **InMemorySaver** | **PostgresSaver** |
|---|---|---|
| 存在哪 | 进程内的 `defaultdict`（Python 对象） | PostgreSQL 的四张表 |
| 进程重启 | ❌ 全丢 | ✅ 全在 |
| 多 worker / 多副本共享 | ❌ 各存各的 | ✅ 共享同一份 |
| 跨进程 resume 中断 | ❌ 做不到 | ✅ 实测可行（本篇核心证据） |
| 时间旅行（history） | ✅ | ✅ |
| 额外依赖 | 无 | 一个 PG 实例 + `psycopg` |
| 适用 | 单元测试、本地调试、notebook、单次 Demo | **生产、HITL 审批、崩溃恢复、多轮会话** |

**一句话选型：只要这个 agent 会"活过"一次 HTTP 请求，就不能用 InMemorySaver。**

还有一个容易被忽略的第三档：**SqliteSaver**（单文件、零服务），适合"要跨进程但不想运维数据库"的单机场景，本篇也顺手实测了。

---

## 一、持久化到底在存什么

先把"存什么"说清楚，后面所有行为都能推出来。

LangGraph 的执行是 **super-step** 模型（[（三）篇](./langgraph-03-静态扇入-与扇入与或扇入.md)讲过 `langgraph_step` 就是 super-step 编号）。checkpointer 干的事是：

> **每跑完一个 super-step，就把"这一刻的完整 State + 待执行的下一步 + 元数据"打一个快照存下来，并用 `thread_id` 做索引。**

所以一条完整的"持久化链"是：

```
thread_id ──┬─→ checkpoint[step=-1]  (input：本次 invoke 的入参)
            ├─→ checkpoint[step=0]   (loop：节点 a 跑完)
            ├─→ checkpoint[step=1]   (loop：节点 b 跑完)
            ├─→ checkpoint[step=2]   (input：第二次 invoke 的入参)
            └─→ ...
```

每个 checkpoint 带一个 `parent_checkpoint_id` 指向上一个 —— **这就成了一条链，链就是历史，链尾就是当前状态。**

这解释了三个现象（后面都会实测到）：
1. 为什么能"接着上次跑"——先按 `thread_id` 找链尾，把 State 恢复出来
2. 为什么能"时间旅行"——拿到链上任意一节的 `checkpoint_id` 就能从那里分叉
3. 为什么 `interrupt` 能恢复——"停在哪"这件事本身就是 State 的一部分，被存下来了

---

## 二、内存持久化：InMemorySaver

### 2.1 最小用法

```python
from langgraph.checkpoint.memory import InMemorySaver

saver = InMemorySaver()
app = graph.compile(checkpointer=saver)

cfg = {"configurable": {"thread_id": "t1"}}
app.invoke({"n": 0, "log": []}, cfg)
app.invoke({"n": 0, "log": []}, cfg)   # 会接着上次的 state
```

### 2.2 实测：多轮累积 + 线程隔离

```python
class S(TypedDict):
    n: Annotated[int, operator.add]
    log: Annotated[list, operator.add]

def inc(s: S):
    return {"n": 1, "log": [f"inc->{s['n'] + 1}"]}
```

```
t1 #1: {'n': 1, 'log': ['inc->1']}
t1 #2: {'n': 2, 'log': ['inc->1', 'inc->2']}
t1 #3: {'n': 3, 'log': ['inc->1', 'inc->2', 'inc->3']}
t2 #1: {'n': 1, 'log': ['inc->1']}
```

两个关键点：

- **`n` 累积到 2、3 不是"覆盖"，是 reducer 在叠加**。节点永远只返回 `{"n": 1}`，但 `Annotated[int, operator.add]` 让它把 1 加到**上一快照的值**上。这是 [（一）篇](./langgraph-01-图基础与状态管理.md) Reducer 语义在持久化下的自然结果 —— **reducer 的输入是"恢复出来的旧值"，不是空值。**
- **`t2` 从 1 开始** —— `thread_id` 是硬隔离边界，两条链互不可见。

> ⚠️ 对照实验：**不传 checkpointer 时传 `thread_id` 不报错，但状态完全不存**（第二次 invoke 还是 `{'n': 1, ...}`）。这是个静默失效 —— 你以为有记忆，其实没有。

### 2.3 实测：`get_state` / `get_state_history` / 时间旅行 / `update_state`

```
get_state: {'n': 3, ...} | next: () | checkpoint_id: 1f1d6bf6
历史快照数: 9
 [0] step=7 source=loop  values={'n': 3, ...}
 [1] step=6 source=loop  values={'n': 2, ...}
 [2] step=5 source=input values={'n': 2, ...}
 [3] step=4 source=loop  values={'n': 2, ...}
 [4] step=3 source=loop  values={'n': 1, ...}
 ...
 [8] step=-1 source=input values={'n': 0, 'log': []}
```

**9 个快照 = 3 次 invoke × 3 个 checkpoint**（每次 invoke 产生 `input` + 两个 `loop`，因为图里只有一个节点但框架仍记 input 帧与终止帧）。注意 `source` 有两种：

- `input`：这是一次 `invoke` 的入口快照（记的是"用户递进来的东西"）
- `loop`：节点执行完产生的快照

时间旅行就是从任意一节继续：

```python
out = app.invoke(None, hist[-1].config)   # 传 None = 不改输入，从该 checkpoint 恢复续跑
```

```
first.values: {'n': 0, 'log': []}
从 first 恢复后: {'n': 1, 'log': ['inc->1']}
```

> 💡 `invoke(None, config)` 这个写法要记牢：**第一个参数传 `None` 表示"不提供新输入，就着 checkpoint 往下走"**。这是所有"恢复/重放/续跑"场景的统一入口，也是后面 resume 中断的思路来源。

`update_state` 手动改状态（HITL 的底层机制之一）：

```
改后 get_state: {'n': 101, 'log': ['inc->1', '人肉写入']}
```

注意 `n` 变成 101 不是 100 —— 因为 `n` 是 reducer channel，`update_state({"n": 100})` 是**往 channel 里追写 100**，跟原来的 1 叠加。**reducer 语义无处不在，改值前要想清楚这个 channel 是不是累加的。**

### 2.4 内存版的内存长什么样

```
saver 内存占用类型: <class 'collections.defaultdict'>
已存线程: ['t1', 't2', 't3']
delete t2 后: ['t1', 't3']
```

**就是一个 `defaultdict[thread_id → 该线程的 checkpoint 链]`。** 看懂了这一行，就看懂了内存版的天花板：**对象活在 Python 堆里。**

### 2.5 天花板实测：换进程就没了

```
# 进程 A
内存 #: {'n': 1}
内存 #: {'n': 2}
内存 #: {'n': 3}

# 进程 B（另起一个 python，同代码）
新进程内存 get_state: {}          ← 全空
新进程内存再跑: {'n': 1}          ← 从零开始
```

对比 Postgres 版同样两段进程：

```
# 进程 A
pg-t1 #1: {'n': 1, ...}
pg-t1 #2: {'n': 2, ...}
pg-t1 #3: {'n': 3, ...}

# 进程 B
新进程 get_state: {'n': 3, 'log': ['inc->1', 'inc->2', 'inc->3']}
新进程再跑一轮: {'n': 4, 'log': [..., 'inc->4']}     ← 接着 3 往下
```

**这就是两种持久化唯一真正重要的差别。** 其余能力（多轮记忆、线程隔离、时间旅行、`update_state`、`interrupt` 恢复）**内存版全都有**，只是有效期只有"进程活着"这段时间。

---

## 三、PostgreSQL 持久化

### 3.1 最小用法

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB = "postgresql://user:pass@host:5432/dbname"

with PostgresSaver.from_conn_string(DB) as saver:
    saver.setup()                                   # ← 必须手动调一次！
    app = graph.compile(checkpointer=saver)
    app.invoke({"n": 0, "log": []}, {"configurable": {"thread_id": "t1"}})
```

### 3.2 坑一：不调 `setup()` 直接报错

`from_conn_string` **不会**自动建表。直接跑：

```
报错: UndefinedTable -> relation "checkpoints" does not exist
```

`setup()` 做的事是：建表 + 跑迁移（`checkpoint_migrations` 表记录版本号），幂等 —— 每次启动都调一次是安全的，且**多副本并发启动也安全**（迁移按版本号串行推进）。

### 3.3 四张表长什么样（实测 `setup()` 后）

```
自动建的表: ['checkpoint_blobs', 'checkpoint_migrations', 'checkpoint_writes', 'checkpoints']
```

| 表 | 干什么 | 关键列 |
|---|---|---|
| `checkpoints` | **快照主表**，一条 = 一个 super-step 的存档 | `thread_id` `checkpoint_ns` `checkpoint_id` `parent_checkpoint_id` `metadata`(jsonb) `checkpoint`(jsonb) |
| `checkpoint_blobs` | 各 channel 的**二进制值**（msgpack 序列化的大块数据） | `thread_id` `checkpoint_ns` `channel` `version` `type` `blob` |
| `checkpoint_writes` | 一次 super-step 内**每个任务的写入**（`Send` 并行时一个 step 有多条） | `task_id` `idx` `channel` `blob` `task_path` |
| `checkpoint_migrations` | 迁移版本号，保证 `setup()` 幂等 | `v` |

**为什么拆成 checkpoints + blobs？** 这是典型的"元数据窄表 + 大字段宽表"分离：
- `checkpoints` 很小，只存指针和元数据 → 按 `thread_id` 列表查询快
- 真正的值（消息列表、长文档）进 `blobs`，按 `(thread_id, ns, channel, version)` 版本化 → **同一个 channel 的不同版本不重复存**，改一次只多一行

实测：一个只有 `__start__` channel 的空图，blob 一共 4 字节（msgpack 空值）。同一个 channel 塞 5000 字符的字符串：

```
before blobs: [('__start__', 'msgpack', 5011)]
```

5011 字节 ≈ 5000 + msgpack 头 —— 符合预期，没有额外膨胀。

老版本的 Node.js 生态里 `checkpoints` 和 `writes` 是合并的，新版拆开后才支持 `Send` 并行 fan-out 下的"一个 step 多任务写入"。

### 3.4 实测：链式结构

```
checkpoints 总行数: 12
  1f1d6bff-a1e7 parent=None          step=-1 src=input
  1f1d6bff-a1ef parent=...-a1e7      step=0  src=loop
  1f1d6bff-a1fa parent=...-a1ef      step=1  src=loop
  1f1d6bff-a21b parent=...-a1fa      step=2  src=input
  1f1d6bff-a222 parent=...-a21b      step=3  src=loop
  1f1d6bff-a229 parent=...-a222      step=4  src=loop
  1f1d6bff-a245 parent=...-a229      step=5  src=input
  1f1d6bff-a24b parent=...-a245      step=6  src=loop
  1f1d6bff-a24f parent=...-a24b      step=7  src=loop
```

`parent_checkpoint_id` 串起来就是一条链，**`step` 是全局递增的**（跨多次 invoke 不重置），每次 `invoke` 插一次 `input` 帧。

> ⚠️ 注意 step 从 `-1` 开始，且**每次 invoke 的第一帧是 `input` 而不是 `loop`**。所以"一次 invoke 产生了几个 checkpoint"= `2 × 节点数 + 1`（线性图），这个数字直接决定了存储增长速度和后面要不要 prune。

### 3.5 实测：跨运行累积 + 历史 + 中断恢复

跨运行累积与内存版完全一致：

```
pg-t1 #1: {'n': 1, 'log': ['inc->1']}
pg-t1 #2: {'n': 2, ...}
pg-t1 #3: {'n': 3, ...}
pg-t2 #1: {'n': 1, ...}
```

时间旅行：

```
快照数: 9
hist[2].values: {'n': 2, 'log': ['inc->1', 'inc->2']}
从 hist[2] 重跑: {'n': 3, 'log': [..., 'inc->3']}
```

中断-恢复：

```
第一次返回 __interrupt__: [Interrupt(value={'问题': '批准吗？'}, id='8e3428dd...')]
next: ('ask',)
resume 后: {'draft': 'AI草稿', 'approved': True}
```

### 3.6 ★核心证据：中断状态跨进程存活

这是**内存版绝对做不到、也是上生产唯一理由**的实验。场景：一个需要人工审批的 agent，进程 A 停在审批点，进程 B 起来接手续跑。

```python
# 进程 A
r = app.invoke({"messages": [HumanMessage("帮我删除所有数据")], "pending_action": ""}, cfg)
# → 停在 interrupt，进程 A 退出
```

```
进程1 返回 __interrupt__: [Interrupt(value={'待审批操作': 'delete_all'}, ...)]
进程1 结束时: 消息数=2 next=('act',)
   [H] 帮我删除所有数据
   [A] 准备执行删除操作
```

```python
# 进程 B（全新进程，同一个 thread_id）
r = app.invoke(Command(resume=True), cfg)
```

```
进程2 启动时读到: 消息数=2 next=('act',)       ← 完整还原了挂起现场
resume 后: 消息数=3 next=()
   [H] 帮我删除所有数据
   [A] 准备执行删除操作
   [A] ✅ 已删除
```

**进程 2 什么都没重建，直接 `Command(resume=True)` 就接上了。** 消息历史、`pending_action`、`next=('act',)` 全部从 PG 里读回来。

这就是为什么 [（二）篇](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md) 说 `interrupt` 必须配 checkpointer —— 更准确地说：**在生产环境必须配"能活过进程"的 checkpointer**。用 InMemorySaver 做 HITL，在多进程/多副本部署下等于随机 500（请求打到没有那份内存的实例上）。

### 3.7 清理 API

```python
saver.delete_thread("pg-t2")     # 按线程整条删
saver.prune([tid], strategy="keep_latest")   # 只留最新（3.2+，新 API）
saver.prune([tid], strategy="delete")        # 整条删（同 delete_thread）
```

```
delete_thread('pg-t2') 后剩余: ['pg-hitl', 'pg-t1']
```

实测 prune 的效果（5 次 invoke 后）：

```
prune 前 (checkpoints, blobs, writes): (15, 5, 15)
keep_latest 后:                        (1, 0, 0)
  历史快照: 1
  最新 state 还在吗: {'n': 5}          ← 状态完整保留
delete 后:                             (0, 0, 0)
```

**反直觉的点：`keep_latest` 把 `checkpoint_blobs` 清到 0，但状态一点没丢。** 我一开始以为是 bug，专门做了个 5000 字符的压力验证：

```
before blobs: [('__start__', 'msgpack', 5011)]
after prune blobs: []
after prune len(big): 5000 | n= 1          ← 值还在
跨进程 after prune → n= 1 len(big)= 5000   ← 换进程也还在
```

原因：**最新的那个 checkpoint 行里已经内联了各 channel 的当前值**（`checkpoint` 是个 jsonb 大字段），`blobs` 主要给"回放旧版本"用。砍掉历史后，只需保留链尾即可还原当前状态。

> 📌 生产含义：`keep_latest` 是**"只要当前状态、放弃时间旅行"**的省空间方案。如果你要做审计/回放/HITL 多轮审批，就不能用 `keep_latest`，得配定时 `prune` 保留最近 N 天。

---

## 四、第三档：SqliteSaver（轻量跨进程）

单文件、零服务，适合单机部署、CLI 工具、桌面应用。

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

conn = sqlite3.connect("/tmp/ckpt.db", check_same_thread=False)
saver = SqliteSaver(conn)
saver.setup()
app = graph.compile(checkpointer=saver)
```

```
sqlite #1: {'n': 1}
sqlite #2: {'n': 2}
sqlite #3: {'n': 3}
历史快照: 9
表: ['checkpoints', 'writes']            ← 只有两张，比 PG 少
checkpoints 行数: 9
文件大小: 4096 bytes
```

跨进程验证（关连接、重新打开）：

```
关闭连接后再用： -> 报错: ProgrammingError Cannot operate on a closed database.
新连接读到: {'n': 3}
新连接再跑: {'n': 4}
```

**两点注意：**
1. `check_same_thread=False` 必加，否则 FastAPI/多线程下直接炸
2. **连接关了 saver 就废了** —— checkpointer 是**绑定连接**的，不是自带连接池。这个坑在 PG 版同样存在（见下节）

三档全景对比：

| | InMemorySaver | SqliteSaver | PostgresSaver |
|---|---|---|---|
| 跨进程 | ❌ | ✅ | ✅ |
| 跨机器/多副本 | ❌ | ❌ | ✅ |
| 需要服务 | 否 | 否 | 是 |
| 并发写 | GIL 下勉强 | 文件锁，**多写者差** | ✅ 强 |
| 生产推荐 | 测试用 | 单机工具 | ✅ 正式 |

---

## 五、生产写法：连接池 + Async

### 5.1 单连接的问题

`PostgresSaver.from_conn_string()` 给的是**一条连接**，且 `with` 块退出就关。实测：

```python
pool.close()
# -> 报错: PoolClosed the pool 'pool-1' is already closed
```

我踩到的那个诡异报错（`psycopg.OperationalError: the connection is closed`）原因也是同类：**脚本缩进写错导致 `with` 块提前结束、连接被关，但 saver 对象还在被用**。所以第二类坑是：

> ⚠️ **checkpointer 的生命周期必须 ≥ 图的整个使用期。** 生产上绝不能"每次请求开一个 saver"（连接爆炸），也不能"启动时 with 一下注册完就退出"（连接已关）。

### 5.2 正确姿势：连接池

```python
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

pool = ConnectionPool(
    DB, max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
)
pool.wait()
saver = PostgresSaver(pool)
saver.setup()

app = graph.compile(checkpointer=saver)   # 全局单例，跟着应用生命周期
```

```
pool #1: {'n': 1}
pool #2: {'n': 2}
pool #3: {'n': 3}
pool 类型: ConnectionPool | closed? False
历史快照: 9
```

三个 kwargs 都是必需的（官方文档默认值，漏了会出各种怪问题）：
- `autocommit=True`：`PostgresSaver` 自己管事务，外面不能再套
- `prepare_threshold=0`：关掉 psycopg 的 prepared statement 缓存（连接池复用连接时，prepared statement 会跨连接失效）
- `row_factory=dict_row`：saver 内部按列名取值，不给就 `KeyError`

### 5.3 Async 版

FastAPI 这类异步服务要用 `AsyncPostgresSaver`：

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

async with AsyncConnectionPool(DB, max_size=5, open=False, kwargs={...}) as pool:
    saver = AsyncPostgresSaver(pool)
    await saver.setup()
    app = graph.compile(checkpointer=saver)
    await app.ainvoke({"n": 0}, cfg)
```

实测：

```
aio #1: {'n': 1}
aio #2: {'n': 2}
aio 历史: 6
async pool invoke: {'n': 1}
```

**同步/异步是两套类，不能混用**（`PostgresSaver` 配 `AsyncConnectionPool` 会报类型错）。`ainvoke` / `aget_state` / `aget_state_history` 是对应前缀。

---

## 六、durability：控制"存多勤"

这是本篇最有意思的一节，也是 [（四）篇](./langgraph-04-控制流-输出-跳转-缓存-重试.md) 留的伏笔。`invoke(..., durability=...)` 三档，实测**对同一次运行产生的快照数影响巨大**：

```
durability=exit   -> 快照数 1
durability=async  -> 快照数 3
durability=sync   -> 快照数 3
```

| 档位 | 行为 | 效果 |
|---|---|---|
| `sync` | 每个 super-step **同步阻塞**写入后才继续 | 最强保证，最慢。崩溃/OOM 也能恢复到最后一个 step |
| `async` | 每个 super-step 写入，但**异步不阻塞**执行 | 默认档。快，但进程被 `kill -9` 时可能丢最后一两个 step |
| `exit` | **只在整个运行结束时写一次** | 最快、存储最少。但中途崩溃 = 从头再来，且**不能从中断恢复** |

**`exit` 快照数只有 1 —— 因为它把中间过程全省了。** 这个档位适合"跑一次就完事的批处理"，绝不适合 HITL 或长任务。

> 💡 顺带一个发现：这个版本里 `ShallowPostgresSaver` 已经**废弃**了（2.0.20 起），官方明确让你改用 `durability="exit"`：
>
> ```
> ShallowPostgresSaver is deprecated ... Use PostgresSaver instead,
> and invoke the graph with `graph.invoke(..., durability='exit')`.
> ```
>
> 也就是说 —— 以前为了省存储专门搞了个"只存最新"的类，现在发现"存不存历史"是**运行时的策略**，不该是**checkpointer 的类型**。这是典型的 API 设计演进：**把静态的类型差异，下沉为动态的参数。**

---

## 七、几个容易踩的坑

### 7.1 `checkpoint_ns` 不是给你做业务隔离的

我本来想用 `thread_id` + `checkpoint_ns` 做"一个用户下的多个子会话"，实测发现：

```
invoke(ns="sub:abc") -> {'n': 1}
get_state(ns="sub:abc") -> ValueError: Subgraph sub not found
DB 里的 ns 取值: ['']
```

**`checkpoint_ns` 是框架内部给子图用的命名空间**（格式形如 `subgraph_node:task_id`），会被编译进图结构做校验。手工塞一个不存在的 ns 进去：
- `invoke` 直接忽略（静默，落到 `''` 主命名空间）—— 比报错更危险
- `get_state` 直接 `ValueError`

**结论：业务层做多级隔离，用 `thread_id` 拼前缀**（如 `user:123:chat:1`）。`checkpoint_ns` 别碰。

### 7.2 `add_messages` 的去重会让"重复提交"静默无效

```python
dup = HumanMessage("你好", id="fixed-id-1")
app.invoke({"messages": [dup]}, c2)
app.invoke({"messages": [dup]}, c2)
# -> 消息数: 3（不是 4）
```

`add_messages` 按 `id` 去重 —— 同一个 id 第二次不会追加而是"更新"。这是**好事**（重试幂等），但如果你手动给消息固定 id 做重试逻辑，会以为"发了两遍"其实只有一条。

### 7.3 每次用户输入只需要传"新消息"

```
三轮后: 消息数=6
  [H] 你好
  [A] 收到：你好
  [H] 我叫小张
  [A] 收到：我叫小张
  [H] 我叫什么？
  [A] 收到：我叫什么？
```

**每次只传一条 HumanMessage，历史自动从 checkpoint 恢复 + `add_messages` 追加。** 千万别"把整段对话重新发一遍"—— 那会因为 id 不同而重复堆积。

### 7.4 `update_state` 遇 reducer channel 会叠加

前面实测：`n` 原本是 1，`update_state({"n": 100})` 之后变成 **101**，不是 100。要"设成 100"得用覆盖型 channel 或自己算差值。

### 7.5 坑汇总表

| 坑 | 症状 | 解法 |
|---|---|---|
| 没调 `setup()` | `UndefinedTable: relation "checkpoints" does not exist` | 启动时调一次，幂等 |
| saver 生命周期短于图 | `OperationalError: the connection is closed` | 全局单例 + 连接池，跟应用同生共死 |
| 每请求新建 saver | 连接数爆炸 | 用 `ConnectionPool` |
| 忘 `check_same_thread=False` | SQLite 多线程报错 | 必加 |
| durability 用 `exit` 又想 resumed | 中断恢复失败 | HITL 用 `sync` |
| 手塞 `checkpoint_ns` | `invoke` 静默忽略 / `get_state` 报 `Subgraph not found` | 用 `thread_id` 前缀做隔离 |
| `keep_latest` 后想回放 | history 只剩 1 条 | 要审计就别用 keep_latest |
| 同步/异步类混用 | 类型错误 / 无响应 | `PostgresSaver` ↔ `AsyncPostgresSaver` 成对 |
| 不传 checkpointer 传 thread_id | **不报错但无记忆** | 显式检查 `app.checkpointer is not None` |

---

## 八、一张选型决策图

```
要跨进程/重启后还活着吗？
├─ 不要 → InMemorySaver（测试 / notebook / 单次 Demo）
└─ 要
   ├─ 单机、不想运维数据库 → SqliteSaver（+ check_same_thread=False）
   └─ 多副本 / 高并发 / 要强一致
      └─ PostgresSaver + ConnectionPool（异步服务用 AsyncPostgresSaver + AsyncConnectionPool）
         └─ 再决定 durability：
            ├─ 长任务 / HITL / 崩溃要能续 → sync
            ├─ 一般 Web 服务 → async（默认）
            └─ 一次性批处理 → exit
```

---

## 九、本篇与前文的接口

- **`interrupt`**（[（二）篇](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md)）：本篇给了它"跨进程"的能力证明。三铁律里"必须 checkpointer"升级为"必须持久化 checkpointer"。
- **`checkpointer` 与时间旅行**（[（一）篇](./langgraph-01-图基础与状态管理.md)）：本篇把"它存在哪、怎么存的、存成什么形状"全部落到了四张表。
- **`durability`**（[（四）篇](./langgraph-04-控制流-输出-跳转-缓存-重试.md)）：那个伏笔在这里兑现 —— 并且发现 `ShallowPostgresSaver` 的废弃史正好解释了"为什么它变成了参数"。
- **Middleware 的 `Summarization` / HITL**（[LangChain（五）篇](./langchain-05-middleware.md)）：压缩和中断都依赖"能读回历史"，用内存版在线上等于没做。
- **往前**：`CachePolicy` 目前只有 `InMemoryCache`，生产要持久化 cache 同样是这类决策；Subgraph 的 `checkpointer=True` 会让子图状态独立落盘（`checkpoint_ns` 的真正来源）。

---

## 十、自测题

1. InMemorySaver 里"存"的到底是什么 Python 对象？为什么它必然不跨进程？
2. `parent_checkpoint_id` 构成了什么数据结构？`get_state_history` 是遍历它还是查表？
3. 一次线性图（N 个节点）的 `invoke` 会产生几个 checkpoint？为什么是 `2N+1`？
4. `setup()` 为什么能重复调用？迁移靠哪张表保证幂等？
5. `checkpoints` 与 `checkpoint_blobs` 为什么要拆开？拆开带来了什么能力？
6. `keep_latest` 把 blobs 清空但状态没丢，说明最新的状态存在哪里？
7. `durability="exit"` 为什么快照数只有 1？它为什么不适合 HITL？
8. `ShallowPostgresSaver` 被废弃这件事，说明了什么 API 设计思想？
9. 为什么 `checkpoint_ns` 不能当业务隔离用？它会带来哪种更危险的失败模式？
10. `update_state({"n": 100})` 后 `n` 变 101 —— 这个行为对"人工修正状态"这个需求意味着什么？

---

## 附：实验脚本清单

均在本机实跑（PostgreSQL 15.19 @ `127.0.0.1:55432`，`langgraph 1.2.16`）：

- `exp1_memory.py` —— 无 checkpointer 静默失效 / 多轮累积 / 历史 9 帧 / 时间旅行 / `update_state` / `delete_thread` / interrupt 恢复 / `defaultdict` 结构
- `exp2_pg.py`（`write` / `read` / `setup_only` / `drop` 四个子模式）—— 不 setup 报错 / 四张表结构 / 链式 parent / 历史 / interrupt / `delete_thread` / **跨进程读取**
- `exp3_cmp.py`（`mem_write` / `mem_read` / `pool` / `durability` / `async` / `async_pool`）—— 内存 vs PG 跨进程对照 / 连接池 / durability 三档快照数 / 同步异步两套
- `exp4_sqlite_ns.py` —— SQLite 两表结构 / 跨进程 / `checkpoint_ns` 实验 / prune 三档 / blob 体积
- `exp5_chat.py`（`p1` / `p2`）—— 真实多轮对话 + `add_messages` 去重 + **跨进程 resume 中断**
