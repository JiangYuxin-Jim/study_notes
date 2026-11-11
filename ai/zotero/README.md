# 研究 / 写作工具

> 服务于学习和科研的辅助工具，不是学习主线，但能让后面的路好走很多。

---

## 📖 目录

| 工具 | 主题 | 笔记 | 日期 |
|---|---|---|---|
| Zotero | 文献管理·基础使用 | [zotero-基础使用](./zotero-基础使用.md) | 2026-08-29 |

---

## 🔍 Zotero 学到的要点

- **核心概念**：Library / Collection / Item Type / Tag / 附件 / 笔记
- **入库三招**：浏览器插件一键抓取、DOI 直接导入、批量导入
- **组织方式**：分类集（层级）+ 标签（多维）+ 智能搜索（动态），三者互补
- **阅读**：PDF 高亮批注直接沉淀为笔记
- **写作**：Word 插件自动引用、一键生成参考文献、随时切换引文格式
- **同步**：官方云（300MB 免费）或 WebDAV（坚果云）

---

## 🔗 和 AI 主线的连接点

Zotero 不只是"存文献"，它其实是一个**高质量语料库**：

```
Zotero 文献库  →  PDF 正文 / 元数据  →  Loader 加载  →  切分  →  向量化  →  RAG 知识库
                                                                    ↓
                                                          个人文献问答助手
```

对照 [LangChain（六）RAG 与文档加载](../langchain/langchain-06-rag与文档加载.md)：Zotero 的 `metadata`（作者/年份/期刊）正好对应 `Document.metadata`，可以在检索时做**年份、来源过滤**；文献全文就是高质量的 `page_content`。

> 这条线以后做下去，就是"能引用真实文献的写作助手"。

---

_相关板块：[LangChain](../langchain/) · [LangGraph](../langgraph/) · [hello-agents](../hello-agents/)_
