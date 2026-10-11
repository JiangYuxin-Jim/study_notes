# LangChain（六）RAG 与文档加载

> 学习日期：2026-10-11
> 课程：LangChain 1.x 入门（RAG 板块开篇）
> 核心主题：RAG 是什么、为什么需要它、RAG 的两大阶段（索引 / 检索生成）、文档加载（Document 对象 / Loader 家族 / 各种格式 / 切分策略）、与前面 Agent 章节的串联关系。
> 定位：前五章把「模型 → 工具 → 结构化输出 → Agent → Middleware」这条 **Agent 主线**走完，从这一章开始进入 **RAG 主线**——让模型接上「外部知识」。

---

## 6.1 为什么要 RAG

大模型有三个天生的短板：

1. **知识过时**：训练数据有截止时间（cutoff），今天发生的事它不知道。
2. **幻觉（Hallucination）**：不知道就硬编，编得还特别自信（第三章讲缩放法则时提过，RAG 是缓解手段之一）。
3. **私有数据缺失**：公司内部文档、个人笔记、产品手册，模型训练时根本没见过。

有两条路可以补：

| 方案 | 做法 | 问题 |
|------|------|------|
| **微调（Fine-tuning）** | 拿私有数据继续训练模型，把知识「焊」进参数 | 贵（算力+标注）、慢、知识更新要重训、易遗忘、无法溯源 |
| **RAG** | 检索出相关文档片段，塞进 prompt 让模型「看着材料回答」 | 依赖检索质量，但**便宜、快、易更新、可溯源** |

> 💡 一句话：**微调改变「模型怎么说话」，RAG 改变「模型说话时手边有什么材料」。**

RAG = **R**etrieval-**A**ugmented **G**eneration，检索增强生成。核心思想朴素到不行：

> 别指望模型记住一切，回答前先帮它把相关资料查出来，连同问题一起喂给它。

---

## 6.2 RAG 的两大阶段：索引 + 检索生成

RAG 系统在架构上分两条流水线。**离线建索引**（做一次）+ **在线检索生成**（每次问答都跑）：

```
【离线·索引阶段】只做一次（或数据更新时重做）
  原始文档（PDF/Word/HTML/DB…）
      │  ① 加载 Load
      ▼
  Document 对象（page_content + metadata）
      │  ② 切分 Split
      ▼
  文档块 Chunks
      │  ③ 向量化 Embed
      ▼
  向量 Vector（[0.12, -0.53, …]）
      │  ④ 入库 Store
      ▼
  向量数据库（Milvus / Chroma / FAISS…）

【在线·检索生成阶段】每次问答都跑
  用户提问
      │  ⑤ 向量化同一个 Embedding 模型
      ▼
  查询向量 ──相似度检索──► 向量库
      │
      ▼
  Top-K 相关文档块（+ metadata 过滤/重排）
      │  ⑥ 拼装 Prompt：系统提示 + 检索内容 + 用户问题
      ▼
  LLM 生成
      │  ⑦ 带引用来源的回答
      ▼
  答案
```

这套「**五层七步**」的思路在 hello-agents 第八章「记忆与检索」里出现过；这里用 LangChain 的组件把它真正落地。

> ⚠️ 关键细节：**索引阶段和查询阶段必须用同一个 embedding 模型**，否则向量空间对不上，检索就是瞎检索。

---

## 6.3 文档加载：一切的起点

RAG 的第一颗扣子就是 **Load（加载）**——把五花八门的原始资料，统一变成 LangChain 能处理的 **`Document` 对象**。

### Document 对象长什么样

LangChain 的 `Document` 只有两个字段，但设计极简极关键：

```python
from langchain_core.documents import Document

doc = Document(
    page_content="LangChain 是一个用于构建 LLM 应用的框架……",   # 正文（检索/喂模型的就是它）
    metadata={                                                  # 元数据（描述性信息，不参与向量化）
        "source": "docs/intro.md",
        "page": 3,
        "author": "张三",
        "date": "2026-10-01",
    },
)
```

- **`page_content`**：文本正文，后续切分、向量化、进 prompt 的都是它。
- **`metadata`**：任意 dict，用来存来源、页码、标题、时间、权限标签等。

> 💡 metadata 的价值经常被低估：它让检索支持**过滤**（只查某部门/某时间段的文档）、让回答支持**引用溯源**（告诉用户「这句话出自 XX 文档第 3 页」）、让后续能**增量更新**（按 source 删掉旧版本）。设计索引时 metadata 一定要一次想清楚。

### Loader 家族：一个统一接口，对接一切格式

LangChain 的加载器全部继承 `BaseLoader`，实现 `load()`（返回 `List[Document]`）和 `lazy_load()`（生成器，适合大文件）两个方法。

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("docs/intro.md", encoding="utf-8")
docs: list[Document] = loader.load()      # 一次性加载
```

按资料类型，常用加载器大致分几类：

| 类别 | Loader | 说明 |
|------|--------|------|
| **纯文本 / Markdown** | `TextLoader`、`UnstructuredMarkdownLoader` | 最基础，Markdown 版会按标题层级保留结构 |
| **PDF** | `PyPDFLoader`、`PyMuPDFLoader`、`UnstructuredPDFLoader` | `PyPDFLoader` 最常用、按页切分并带 `page` 元数据；`PyMuPDFLoader` 更快、对排版保留更好 |
| **Word / PPT / Excel** | `Docx2txtLoader`、`UnstructuredWordDocumentLoader`、`UnstructuredPowerPointLoader` | 办公文档，`Unstructured` 系列格式覆盖最广 |
| **网页** | `WebBaseLoader`、`AsyncHtmlLoader`、`UnstructuredHTMLLoader` | 直接抓 URL 或本地 HTML，能拿到正文与标题 |
| **结构化数据** | `CSVLoader`、`JSONLoader`、`SQLDatabaseLoader` | 一行/一条记录转成一个 Document |
| **代码** | `LanguageParser` / `GenericLoader` | 按语法结构切分，对代码库 RAG 很有用 |
| **云盘 / 平台** | `NotionDBLoader`、`GoogleDriveLoader`、`S3Loader` | 对接第三方数据源 |

**目录批量加载**（实际项目最常见的姿势）：

```python
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

loader = DirectoryLoader(
    "data/pdfs",
    glob="**/*.pdf",            # 通配符匹配
    loader_cls=PyPDFLoader,     # 每个文件用哪个 loader
    show_progress=True,
    use_multithreading=True,    # 多线程加速
)
docs = loader.load()
print(len(docs), docs[0].metadata)
```

> 💡 实战提醒：
> - **编码**：中文文档务必显式 `encoding="utf-8"`，否则乱码。
> - **失败文件**：批量加载要有容错，坏文件别让整批任务挂掉。
> - **懒加载**：文档量大时用 `lazy_load()`，边加载边处理，避免一次性把内存吃爆。
> - **元数据补全**：批量加载出来的 `source` 是文件路径，最好再补上标题、更新时间、业务标签等——检索质量一半靠这个。

### 加载之后的下一步：切分（Split）

加载完的 Document 往往太长（一篇 50 页 PDF 塞不进上下文，语义也太散）。所以紧接着就是 **Split**：

- 常用 `RecursiveCharacterTextSplitter`，按 `["\n\n", "\n", " ", ""]` 递归降级切分，尽量保住段落边界；
- 两个关键参数：`chunk_size`（块大小，如 500~1000 字符）+ `chunk_overlap`（重叠，如 50~200，防止一句话被切在中间丢语义）；
- 切分后每个 chunk 仍保留原 `metadata`（可加 `chunk_index`），保证溯源不断链。

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],  # 中文补上句末标点
)
chunks = splitter.split_documents(docs)
```

> 分块策略是 RAG 里最"玄学"也最影响效果的一环，后面章节（all-in-rag 的 ch2）还会深入，这里先把链路打通。

---

## 6.4 与前面章节的关系

```
LangChain（一）模型     ← 负责「说」
LangChain（二）工具     ← 负责「做」
LangChain（三）结构化输出 ← 负责「说成格式」
LangChain（四）Agent    ← 负责「自己决定做什么」
LangChain（五）Middleware ← 负责「把上面这些管起来」
LangChain（六）RAG      ← 负责「给模型补上外部知识」★本章
```

**RAG 与 Agent 不是替代关系而是组合关系**：RAG 的「检索」本质上可以封装成 Agent 的一个**工具**——这正是 hello-agents 第七章「万物皆为工具」的思路。一个成熟的 Agent 通常是：**能调用检索工具（RAG）+ 能执行动作（Tool）+ 有记忆（Memory/checkpointer）**。

---

## 6.5 本章小结

| 要点 | 一句话记忆 |
|------|-----------|
| 为什么 RAG | 模型知识过时/幻觉/没有私有数据；微调改"说话方式"，RAG 改"手边材料" |
| RAG 两阶段 | **离线索引**（加载→切分→向量化→入库）+ **在线检索生成**（检索→拼 Prompt→生成） |
| 第一步 | **Load**：一切原始资料 → 统一 `Document(page_content, metadata)` |
| Document | `page_content` 进向量、`metadata` 管过滤/溯源/更新 |
| Loader | `BaseLoader` 统一接口：`load()` / `lazy_load()`；文本/PDF/Office/网页/结构化/云盘全覆盖；`DirectoryLoader` 批量加载 |
| 紧接一步 | **Split**：`RecursiveCharacterTextSplitter`，`chunk_size` + `chunk_overlap`，中文补句末分隔符 |
| 铁律 | 索引与查询必须用**同一个 embedding 模型** |
| 与 Agent 关系 | 检索可封装为工具 → 组合成「会说 + 会做 + 有知识 + 有记忆」的完整 Agent |

---

## 下一步

- 继续 LangChain RAG 线：**向量化（Embeddings）→ 向量库（VectorStore）→ 检索器（Retriever）→ 高级检索**；
- 与 all-in-rag 的 ch3（向量化/向量库/索引）对照学习，一个学 LangChain 组件用法，一个学底层原理。
