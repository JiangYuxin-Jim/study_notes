# LangGraph 学习笔记

> LangGraph 是 LangChain 官方的**有向图 / 状态机**编排框架，Agent 的循环、分支、并行、中断、持久化都靠它落地。
> 本目录共 8 篇，全部基于本机 `langgraph 1.2.16` 实测，代码均可复现。

---

## 📖 目录

| 序号 | 主题 | 一句话 | 日期 |
|---|---|---|---|
| 01 | [图基础与状态管理](./langgraph-01-图基础与状态管理.md) | **LangGraph = 有向图 + 共享 State**；建图五步、Reducer 合并语义、条件边循环、checkpointer | 2026-10-24 |
| 02 | [进阶建图：defer·条件边·sequence·Router·Send](./langgraph-02-进阶建图-defer-条件边-sequence-router-send.md) | `add_sequence` / `path_map` 分层 / Router 纯函数决策层 / `Send` 动态扇出 / `defer` 真相 | 2026-10-25 |
| 03 | [静态扇入：与扇入 vs 或扇入](./langgraph-03-静态扇入-与扇入与或扇入.md) | 同一张图两种汇合写法结果完全不同，**图长得一样必须看代码** | 2026-10-30 |
| 04 | [控制流：输出·跳转·缓存·重试](./langgraph-04-控制流-输出-跳转-缓存-重试.md) | `stream_mode` 六种 / `Command(goto)` / `CachePolicy` / `RetryPolicy` | 2026-10-31 |
| 05 | [持久化：内存 vs PostgreSQL](./langgraph-05-持久化-内存与PostgreSQL.md) | checkpointer 快照机制、四张表、**跨进程 resume 中断**、durability 三档 | 2026-11-02 |
| 06 | [错误回复 · Replay · Fork](./langgraph-06-错误回复-replay与fork.md) | checkpoint 链的三条分支用法；异常 vs 中断的本质区别 | 2026-11-09 |
| 07 | [记忆：短期上下文 vs 长期 Store](./langgraph-07-记忆-短期上下文与长期Store.md) | **checkpointer 是录音带，Store 是笔记本**；语义检索与读写时机 | 2026-11-10 |
| 08 | [中断 · 工具节点 · 流式执行](./langgraph-08-中断-工具节点-流式执行.md) | HITL 三件套；`interrupt()` 语义、`ToolNode`、`stream_mode` 实战 | 2026-11-11 |

---

## 🧭 学习路径建议

```
①  01 图基础     ← 先建立"图 + State"心智模型，其它全建立在这上面
②  02 进阶建图   ← 把"怎么连边"练熟
③  03 静态扇入   ← 并行汇合的坑，越早踩越好
④  04 控制流     ← 输出/跳转/缓存/重试，工程化的第一层
⑤  05 持久化     ← checkpointer 是后面全部能力的地基
⑥  06 错误与分叉 ← 出错不再是事故，而是可回滚快照
⑦  07 记忆       ← 短期 vs 长期，分层是结构必需不是优化
⑧  08 中断/工具  ← HITL 落地，Agent 真能干活
```

---

## ⭐ 贯穿全系列的几条硬结论

1. **节点只返回增量**，不要 `state["x"].append()` 后再 return 整份 state —— reducer 会重复累加
2. **`add_edge("a","c")` 写两次 = 或扇入**（c 跑两次）；**`add_edge(["a","b"],"c")` = 与扇入**（c 跑一次且等齐）
3. **有副作用的汇总节点一律用与扇入**
4. **`interrupt()` 恢复时会整个节点重跑** → interrupt 之前的代码必须幂等、副作用必须放之后
5. **没有 checkpointer 时 `invoke` 不报错，`resume` 才报** —— 真要求是「状态活过进程」
6. **ToolNode 一旦中断，整批工具全部重跑** → 有副作用必须幂等键，或把审批拆成独立节点
7. **`RetryPolicy` 默认不重试 ValueError/OSError 系**（含 TimeoutError），API 超时必须显式 `retry_on`
8. **`replay` 不是只读**，会写回原链 → 对照实验必须换 `thread_id`

---

_持续更新中，下一篇：Subgraph 子图 + 手搓 ReAct 图对照 `create_agent`_
