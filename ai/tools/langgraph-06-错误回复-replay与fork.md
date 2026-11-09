# LangGraph（六）· 错误回复、运行、Fork 与 Replay

> 学习日期：2026-11-09
> 环境：本机 `langgraph 1.2.16` + `langgraph-checkpoint 4.3.0`，**下述三段实验全部实跑，输出原样贴出**
> 承接：[（五）· 持久化](./langgraph-05-持久化-内存与PostgreSQL.md)（那里只把 `get_state_history` 当"能看历史"用了，本篇把它变成**能做的事**）
> 一句话：**（五）讲的是"状态存下来了"，本篇讲的是"存下来之后能拿来干什么" —— 三条分支：继续跑（resume）、重跑一遍（replay）、另开一条路（fork）。**

---

## 〇、先把三个词定死

| 动作 | 一句话 | 入口 | 产生新线程吗 |
|---|---|---|---|
| **resume** | 从「暂停/出错」的那一帧**接着往下**跑 | `invoke(Command(resume=...), cfg)` | 否，同线程 |
| **replay** | 从某个**历史帧**原样重跑一遍 | `invoke(None, 历史cfg)` | 否，同线程（会追加到链上） |
| **fork** | 从某个历史帧**改状态后另起一条线** | `update_state(历史cfg, 新值)` 或 `update_state(新线程cfg, 值, as_node=...)` | 可选，看 config |

三者共用同一块地基：**checkpoint 链**。`thread_id` 决定"哪条链"，`checkpoint_id` 决定"链上哪一节"。

```
thread ── ckpt[-1] ── ckpt[0] ── ckpt[1] ── ckpt[2]
             ↑            ↑          ↑          ↑
          replay 可从任意一节起   fork 也从任意一节起（改写后再分叉）
```

> 💡 记牢这一个写法：**`invoke(None, config)` 的第一个参数传 `None` = "不给新输入，就着这个 checkpoint 往下走"**。所有 replay / 续跑都走这个入口；（五）篇里已经出现过，本篇给它正名。

---

## 一、错误回复：失败也是一种"状态"

### 1.1 关键认知：异常不会抹掉现场

节点抛异常时，LangGraph **把异常向上抛给调用方**，但 checkpointer 里那一帧已经写好了：

```
=== 失败线程：异常被 checkpointer 留在链上 ===
捕获异常: explode 模拟节点异常
失败后 values: {'log': ['boom', 'inc->2']}
失败后 next: ('work',)   <- 非空 = 卡在 work 节点
tasks: [('work', '"RuntimeError(\'explode 模拟节点异常\')"')]
失败后历史快照数: 3
```

三个可直接用于"错误回复"的信号：

1. **`get_state(cfg).next` 非空** → 还有没跑完的节点，不是正常结束
2. **`state.tasks[*].error`** → 失败节点名 + 异常对象本身
3. **`thread_id` 仍然有效** → 状态还在，不用从头再来

也就是说：**持久化让"出错"从一次事故变成了一次可回滚的快照。** 这是 Agent 能长时间跑的前提 —— LLM 调用不稳定，没有 checkpointer 的话一次 429 就得把整个任务从头烧一遍 token。

### 1.2 两种"错误"要分开处理

| 类型 | 表现 | 恢复方式 |
|---|---|---|
| **异常型**（节点抛错、API 失败、超时） | `invoke` 抛出、`tasks[].error` 有值 | 修好后从该帧 replay / 用 `RetryPolicy` 自动重试 |
| **中断型**（HITL 审批、等用户输入） | `invoke` **正常返回**，带 `__interrupt__` 字段 | `invoke(Command(resume=值))` |

中断不是异常，这点很多教程讲错。实测：

```
=== 1. 跑到 interrupt 处 ===
invoke 返回值: {'log': ['start', 'A, B'], '__interrupt__': [Interrupt(value={'question': '选 C 还是 D？',
              '已做': ['start', 'A, B']}, id='2ed30a5d...', response_schema=None)]}
next: ('pick_c',) | 暂停时 values: {'log': ['start', 'A, B']}
```

**`invoke` 返回了，`next` 指向暂停节点，`interrupts` 里有待答问题。** 状态已落盘，进程可以退出，明天再来答都行 —— 这就是（五）篇验过的"跨进程 resume"。

```
=== 3. 人工回传 ===
resume 结果: {'log': ['start', 'A, B', '选了 C']}
```

> ⚠️ 一个隐藏语义：`interrupt` 恢复时 **`pick_c` 这个节点会从头再跑一遍**，`interrupt(...)` 那行之前的所有副作用（写库、发请求）都会重放。所以铁律是：**`interrupt` 之前不能放有副作用的操作**，或者副作用必须做成幂等的。

---

## 二、Replay：原样重跑一遍

### 2.1 用法

```python
hist = list(app.get_state_history(cfg))     # 新 → 旧
h = hist[1]                                 # 挑一帧
out = app.invoke(None, h.config)            # 从这一帧重跑
```

实测（干净线程，`inc -> work`）：

```
=== 1. 干净线程 ===
结果: {'log': ['inc->1', 'ok']}
快照数: 4
  [0] step=2 source=loop  values={'log': ['inc->1', 'ok']}  next=()
  [1] step=1 source=loop  values={'log': ['inc->1']}        next=('work',)
  [2] step=0 source=loop  values={'log': []}                next=('inc',)
  [3] step=-1 source=input values={'log': []}               next=('__start__',)
```

### 2.2 Replay 的两个真实用途

**① 调试**：Agent 出错时，最痛的不是"错了"，是"复现不出来"（LLM 有随机性、工具返回会变）。有了 checkpoint，可以**回到出错前那一帧重放**，反复观察同一个节点的行为，甚至逐帧 `next` 看路由决策。

**② 归因**：从第 N 帧重跑，对比"同样的输入为什么这次走了另一条路" → 一眼看出是 prompt 问题还是工具返回变了。

### 2.3 ⚠️ Replay 不是"只读"——它会把结果写回同一条链

```
replay 后该线程快照数: 6      # 原来是 4
```

从 `hist[1]`（step=1）重跑后，链上多了 `inc->1, ok` 之后的新帧，**原线程的 head 被这次重跑的结果顶掉了**。

> **结论：想保留原始轨迹，就别在原线程上 replay。** 要对照实验就 fork 到新线程（下一节）。

还有一个语义细节：replay 从 `step=1` 那一帧起跑时，`inc` **不会重跑** —— 因为那一帧的 `next=('work',)` 已经写明"下一个该跑 work"，State 里 `inc->1` 也已经写好了。**replay 的起点是"该帧的 next"，不是"该帧的 values 再往前一步"。**

---

## 三、Fork：另开一条路

### 3.1 机制：`update_state` = 在链上"打补丁生新帧"

`update_state` 的本质是：**拿一个 config（指向某帧），把 values 怼进去，产出一个新 checkpoint，其 `parent` 指向那一帧。** 于是链就分叉了。

实测（同线程分叉）：

```
=== A. 同线程 fork：update_state(历史config, 新值) ===
新 id: 1f1dc41e | parent == 目标帧: True
快照数: 4 -> 5
线程 t 的 head 已被新分支占据: {'log': ['inc->1', 'A: 同线程改写']}
```

**分叉点在原线程内**，`head` 就变成了新分支的末帧。原轨迹还在（历史里能查到），但"当前状态"已经是新分支了。

### 3.2 想要独立分支 → 换 `thread_id`

```python
fork = {"configurable": {"thread_id": "t-fork2"}}
app.update_state(fork, dict(target.values), as_node="inc")   # as_node 定位"这是 inc 跑完之后的样子"
```

实测：

```
=== B. 独立分支 ===
新线程 t-fork2 values: {'log': ['inc->1']} next: ('work',)
主干 t head: {'log': ['inc->1', 'A: 同线程改写']}
主干快照数: 5 | 分支快照数: 1

=== C. 分支独立续跑，主干不受影响 ===
分支续跑结果: {'log': ['inc->1', 'ok']}
主干 t: {'log': ['inc->1', 'A: 同线程改写']}
分支 t-fork2: {'log': ['inc->1', 'ok']}
```

**主干纹丝不动，分支独立推进。** 这才是"A/B 对照"的正确姿势。

### 3.3 `as_node` 是必填的思路

`update_state(config, values, as_node=...)` 第三个参数决定"这帧算哪一步产生的"。不给的话：

- 同一帧（历史 config）下：默认取"最后一个改状态的节点"，通常也够用
- **新线程 + 从历史帧搬状态**时：必须显式给 `as_node`，否则框架不知道 `next` 该指向谁

> ⚠️ 踩坑记录：我第一次写成 `app.update_state(target.config, values, fork_config)` —— 把"新线程 config"当第三个位置参数传了。它被当成 `as_node`（要的是字符串），直接报 `TypeError: unhashable type: 'dict'`。**签名是 `(config, values, as_node, task_id)`，没有"目标 config"这个位置。** 换线程的做法一定是**把 config 换掉，再手动给 `as_node`**。

### 3.4 三种 fork 场景对照

| 场景 | 写法 | 影响原线程吗 |
|---|---|---|
| 临时改一下接着跑（HITL 修正） | `update_state(原cfg, 补丁)` | 会，head 变成新分支 |
| 保留证据 + 另起对照实验 | `update_state(新线程cfg, values, as_node=...)` | 不会 |
| 循环回退重试（"第 3 步搞错了，退回第 1 步"） | `update_state(第1步cfg, 修正值)` | 会，这是想要的效果 |

---

## 四、三者如何组合：一个真实套路

"Agent 跑到第 5 步发现方向错了" 的标准处置流程：

```
1. get_state_history(cfg)                    # 找"还没走错"的那一帧（比如第 2 帧）
2. hist[k].values 看一眼，确认是对的现场
3. 开新线程 fork：
     update_state({"configurable": {"thread_id": "run2"}}, 修正后的值, as_node="第2步的节点名")
4. invoke(None, 新线程 cfg)                   # 从那里接着跑，不重放前 2 步
5. 原线程保留原轨迹 → 事后能对比"哪一步开始分岔"
```

成本上是划算的：**只用重跑分岔点之后的节点**，前面的 LLM 调用全部省掉。Agent 越长越值。

---

## 五、几个必须记住的边界

1. **`get_state_history` 顺序是新 → 旧**。`hist[-1]` 是最早的 `source=input` 那一帧，`hist[0]` 是 head。
2. **`next == ()` 才是正常结束**。非空 = 暂停或失败。
3. **replay 会写回原链**，对照实验必须换 `thread_id`。
4. **`update_state` 对 reducer channel 是"追加"不是"覆盖"**（（五）篇实测 `n: 1 → update_state({"n":100}) → 101`）。想真正改值，得挑覆盖型 channel，或者写入前想清楚累加语义。
5. **`interrupt` 恢复会重跑整个节点**，副作用要么挪到 `interrupt` 之后，要么幂等。
6. **这三件事全部依赖 checkpointer**。`InMemorySaver` 下进程一退全没了 —— 生产要用 Postgres/SQLite。

---

## 六、自测题

1. `invoke(None, cfg)` 里的 `None` 表示什么？和 `invoke({}, cfg)` 有什么区别？
2. 节点抛异常后，为什么 `get_state().values` 里还能看到出错前的数据？异常存到哪个字段了？
3. `interrupt` 为什么不算"错误"？它和异常在 `invoke` 的返回/抛出上有什么不同？
4. 想让 replay 不污染原线程，最省事的做法是什么？
5. `update_state` 的第三个位置参数是什么？为什么不能传一个 config 进去？
6. fork 之后 `parent_checkpoint_id` 指向哪里？这条指针构成了什么结构？
7. 从第 K 帧 replay，前 K 个节点会重跑吗？为什么？
8. Agent 第 5 步走错，怎么只重跑第 2 步之后的部分？给出完整调用序列。

---

## 附：本篇实验脚本

均在 `/tmp` 下实跑（`InMemorySaver`，结论与持久化后端无关）：

- `fork_replay_demo.py` —— 异常现场留痕 / `tasks[].error` / replay 追加写回 / 同线程 fork
- `fork_demo2.py` —— 同线程 fork vs 换 `thread_id` 独立分支 / `as_node` 用法 / 分支独立续跑
- `err_resume_demo.py` —— `interrupt` 返回 `__interrupt__` 而非抛异常 / `Command(resume=)` 恢复 / 从 interrupt 之前 fork 走另一条路
