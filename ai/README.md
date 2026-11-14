# AI 智能体与 RAG（主线板块）

> 📚 本板块为学习主线的第四个板块，基于 **Datawhale 社区**两个开源项目系统学习 **RAG（检索增强生成）** 与 **AI 智能体（Agent）**。
> 内容使用 AI 辅助生成和润色。

---

## 🌟 为什么学这个板块

- 当前市场最大风口是 **AI 应用 / 智能体**（AI 应用开发岗需求暴涨、供需比约 1:5）。
- 本板块补齐知识体系中缺失的 **AI 应用两大核心：RAG + Agent**。
- 与天机学堂课程（Spring AI、RAG、多智能体）互补：一个学**通用原理（Python）**，一个做 **Java 落地**。
- 语言路线：**Python + Java 双修**，用 Python 学透原理，用 Java/Spring AI 落地工程。

---

## 📚 两个项目

| 项目 | 仓库（GitHub） | 内容 | 章节 |
|------|----------------|------|------|
| **all-in-rag** | datawhalechina/all-in-rag | RAG 技术全栈指南（检索增强生成全链路） | 9 章 |
| **hello-agents** | chendaming525/hello-agents | 系统性智能体学习教程（AI 原生 Agent） | 16 章 |

学习顺序：**先 hello-agents（Agent 地基）→ 再 all-in-rag（RAG 进阶）**

### 项目本地路径
- `/home/admin/ai_projects/all-in-rag`
- `/home/admin/ai_projects/hello-agents`

---

## 📂 笔记目录

### RAG（all-in-rag）9 章 → 笔记 `ai/` 下

| 章 | 主题 | 笔记 |
|----|------|------|
| ch1 | RAG 介绍 / 环境准备 / 快速上手 | |
| ch2 | 数据加载与文本分块 | |
| ch3 | 向量化（embedding）/ 向量数据库（Milvus）/ 索引优化 | |
| ch4 | 混合检索 / 查询构造 / Text2SQL / 高级检索 | |
| ch5 | 格式化生成 | |
| ch6 | 系统评测 / 常用工具 | |
| ch7 | 知识图谱 RAG（KG-RAG） | |
| ch8 | 综合项目：环境架构 / 数据 / 索引检索 / 生成系统 | |
| ch9 | GraphRAG：图架构 / 建模 / 索引 / 智能路由 | |

### Agent（hello-agents）16 章 → 笔记 `ai/hello-agents/` 下

| 篇 | 主题 | 笔记 | 完成时间 |
|----|------|------|----------|
| 1 | 初识智能体（理论基础） | [01-初识智能体(理论基础)](./hello-agents/01-初识智能体(理论基础).md) | 2026-08-07 |
| 1 | 动手实现第一个智能体 + 协作模式 | [02-动手实现第一个智能体与协作模式](./hello-agents/02-动手实现第一个智能体与协作模式.md) | 2026-08-07 |
| 2 | 智能体发展史 | [02-智能体发展史](./hello-agents/02-智能体发展史.md) | 2026-10-18 |
| 3 | 大语言模型基础 | [03-大语言模型基础](./hello-agents/03-大语言模型基础.md) | 2026-08-11 |
| 4 | 智能体经典范式构建 | | |
| 5 | 基于低代码平台的智能体搭建 | | |
| 6 | 框架开发实践 | [06-框架开发实践](./hello-agents/06-框架开发实践.md) | 2026-08-13 |
| 7 | 构建自己的 Agent 框架 | [07-构建你的Agent框架](./hello-agents/07-构建你的Agent框架.md) | 2026-08-14 |
| 8 | 记忆与检索 | [08-记忆与检索](./hello-agents/08-记忆与检索.md) | 2026-08-18 |
| 8 | 8.3.5 高级检索：MQE 与 HyDE | [08-进阶检索-MQE与HyDE](./hello-agents/08-进阶检索-MQE与HyDE.md) | 2026-10-25 |
| 9 | 上下文工程 | [09-上下文工程](./hello-agents/09-上下文工程.md) | 2026-10-19 |
| 9 | 上下文工程（补充）· JIT 上下文与 GSSC 流水线 | [09-补充-JIT上下文与GSSC流水线](./hello-agents/09-补充-JIT上下文与GSSC流水线.md) | 2026-10-26 |
| 9–16 | 后续章节 | | |

### 深度学习实战 → 笔记 `ai/transformer/` 下

| 项目 | 主题 | 笔记 | 完成时间 |
|------|------|------|----------|
| Transformer-pytorch | 从零手搓 Transformer 做英译中（PyTorch 亲手实现 Encoder-Decoder·约 1500 行·BLEU 26.30） | [01-从零手搓Transformer英译中实战](./transformer/01-从零手搓Transformer英译中实战.md) | 2026-10-28 |

---

### LangGraph 框架 → 笔记 `ai/langgraph/` 下（9 篇）

| 序号 | 主题 | 笔记 | 完成时间 |
|------|------|------|----------|
| 一 | 图基础与状态管理（建图五步 / Reducer / 条件边循环 / checkpointer） | [langgraph-01-图基础与状态管理](./langgraph/langgraph-01-图基础与状态管理.md) | 2026-10-24 |
| 二 | 进阶建图（`add_sequence` / `path_map` / Router / `Send` / `defer`） | [langgraph-02-进阶建图](./langgraph/langgraph-02-进阶建图-defer-条件边-sequence-router-send.md) | 2026-10-25 |
| 三 | 静态扇入（**或扇入执行 2 次 vs 与扇入执行 1 次且等齐**） | [langgraph-03-静态扇入](./langgraph/langgraph-03-静态扇入-与扇入与或扇入.md) | 2026-10-30 |
| 四 | 控制流（`stream_mode` / `Command(goto)` / `CachePolicy` / `RetryPolicy`） | [langgraph-04-控制流](./langgraph/langgraph-04-控制流-输出-跳转-缓存-重试.md) | 2026-10-31 |
| 五 | 持久化（InMemorySaver vs PostgresSaver / **跨进程 resume 中断** / durability 三档） | [langgraph-05-持久化](./langgraph/langgraph-05-持久化-内存与PostgreSQL.md) | 2026-11-02 |
| 六 | 错误回复 · Replay · Fork（checkpoint 链三分支 / 异常 vs 中断） | [langgraph-06-错误回复-replay与fork](./langgraph/langgraph-06-错误回复-replay与fork.md) | 2026-11-09 |
| 七 | 记忆系统（**短期=checkpointer / 长期=Store** / 语义检索 / 读写时机） | [langgraph-07-记忆](./langgraph/langgraph-07-记忆-短期上下文与长期Store.md) | 2026-11-10 |
| 八 | 中断 · 工具节点 · 流式执行（**HITL 三件套** / `interrupt()` / `ToolNode` / `stream_mode`） | [langgraph-08-中断-工具节点-流式执行](./langgraph/langgraph-08-中断-工具节点-流式执行.md) | 2026-11-11 |
| 九 | Subgraph 子图与静态发现（**两种接入方式** / `xray=True` / **推翻「链式导致解析失败」的误判**·三组控制变量实验） | [langgraph-09-Subgraph子图与静态发现](./langgraph/langgraph-09-Subgraph子图与静态发现.md) | 2026-11-11 |

### Learn Claude Code → 笔记 `ai/learn-claude-code/` 下（6 篇）

| 序号 | 主题 | 笔记 | 完成时间 |
|------|------|------|----------|
| 前三章 | Agent Loop / 工具调用 / 三层权限隔离 | [learn-claude-code-前三章](./learn-claude-code/learn-claude-code-前三章.md) | 2026-09-17 |
| 四 | 钩子函数（Hooks / 生命周期事件 / 权限接管） | [learn-claude-code-04-钩子函数](./learn-claude-code/learn-claude-code-04-钩子函数.md) | 2026-09-18 |
| 五 | TodoWrite（任务清单 / 四态生命周期 / 提醒机制 / 模型可用性） | [learn-claude-code-05-todowrite](./learn-claude-code/learn-claude-code-05-todowrite.md) | 2026-09-20 |
| 六 | Subagent 与 Skill 加载（上下文隔离 / 按需加载 / 成本模型） | [learn-claude-code-06-subagent与skill加载](./learn-claude-code/learn-claude-code-06-subagent与skill加载.md) | 2026-09-21 |
| 七 | 上下文压缩（四级降级 / 首尾保留 / 引用化 / LLM 摘要兜底） | [learn-claude-code-07-上下文压缩](./learn-claude-code/learn-claude-code-07-上下文压缩.md) | 2026-09-22 |
| 八 | 记忆系统（LLM 无状态 / 分层记忆 / CLAUDE.md / 与压缩配合） | [learn-claude-code-08-记忆系统](./learn-claude-code/learn-claude-code-08-记忆系统.md) | 2026-10-04 |

---

### LangChain 框架 → 笔记 `ai/langchain/` 下（6 篇）

| 序号 | 主题 | 笔记 | 完成时间 |
|------|------|------|----------|
| 一 | 模型调用与消息体系（`init_chat_model` / 六种调用方式 / `model_kwargs`·`extra_body` / LangSmith / AIMessage·ToolMessage） | [langchain-01-模型调用与消息体系](./langchain/langchain-01-模型调用与消息体系.md) | 2026-10-06 |
| 二 | 工具调用 Tool Use（`@tool` 三要素 / `StructuredTool` / **模型只提议不执行**·`bind_tools` / 手动回路 / `create_agent` / MVTS） | [langchain-02-tool-use](./langchain/langchain-02-tool-use.md) | 2026-10-08 |
| 三 | 结构化输出（`with_structured_output` / Pydantic Schema 设计 / 底层 Function Calling / 校验与兜底） | [langchain-03-structured-output](./langchain/langchain-03-structured-output.md) | 2026-10-08 |
| 四 | Agent（`create_agent` / ReAct → 原生 Function Calling / 内部图结构 / Middleware / checkpointer 记忆 / HITL） | [langchain-04-agents](./langchain/langchain-04-agents.md) | 2026-10-08 |
| 五 | 中间件 Middleware（**Agent 的 AOP**·六大钩子 / 装饰器 vs 类 / 执行顺序与 `jump_to` / 内置 18 个 / 四个实战） | [langchain-05-middleware](./langchain/langchain-05-middleware.md) | 2026-10-10 |
| 六 | RAG 与文档加载（微调 vs RAG / 离线索引 + 在线检索两阶段 / `Document` / Loader 家族 / `DirectoryLoader` / 切分策略） | [langchain-06-rag与文档加载](./langchain/langchain-06-rag与文档加载.md) | 2026-10-11 |

### 论文精读 → 笔记 `ai/papers/` 下

| 序号 | 论文 | 主题 | 完成时间 |
|------|------|------|----------|
| 1 | [Mirror Illusion Art (CVPR 2026)](./papers/01-Mirror-Illusion-Art-AutoMIA.md) | **AutoMIA 双视图逆向设计**：两张目标图（镜前 A / 镜中 B）→ 同一个 3D 体素物体的几何+颜色联合优化；治四类缺陷的四个模块 **PAC**（投影对齐连通块筛选·治表面噪声）· **PWA**（位置加权自适应·治背景噪声）· **IVP**（内部体素密度下限·治内部断裂）· **SCD**（形状→联合→颜色三阶段调度·治形状颜色失衡）；128³ 体素 · PyTorch3D · 单卡 76s/2.6GB · SL 0.989/NL 0.049/SS 0.931 全面优于 SA/SAR 但**时间不是最优**（SA 50s）；观察角约束 `θ₁<Θ<θ₂`；局限（两图宽度需相近·分辨率不超体素分辨率）＋ 原文 4 处笔误/矛盾存疑 | 2026-11-14 |

---

### 研究/写作辅助工具 → 笔记 `ai/zotero/` 下

| 工具 | 主题 | 笔记 | 完成时间 |
|------|------|------|----------|
| Zotero | 文献管理·基础使用 | [zotero-基础使用](./zotero/zotero-基础使用.md) | 2026-08-29 |

---

### 📁 目录结构

```
ai/
├── hello-agents/        智能体教程（Datawhale，16 章）
├── langchain/           LangChain 框架（6 篇）
├── langgraph/           LangGraph 框架（9 篇）+ labs/ 实验脚本
├── learn-claude-code/   Claude Code 内部机制拆解（6 篇）
├── papers/              论文精读（CVPR 等）
├── transformer/         深度学习实战（手搓 Transformer）
├── zotero/              研究工具
└── README.md
```

---

> 🔄 学习进度见本目录各章笔记，完成时间记录在 README 时间线中。
