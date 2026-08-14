# 第七章 构建你的 Agent 框架

> 学习日期：2026-08-14
> 课程：hello-agents / 第七章「构建你的智能体框架」
> 核心主题：从「用框架的人」升级为「造框架的人」——手写一个轻量、教学友好的 Agent 框架（HelloAgents），把前六章学过的概念（Agent 范式、LLM 封装、工具调用）用抽象基类 + 统一接口的方式落地成一个可扩展的代码骨架。

---

## 7.1 框架整体架构设计

### 7.1.1 为何需要自建 Agent 框架

市面框架（LangChain 等）存在 4 大痛点：

1. **过度抽象的复杂性**：为了通用性引入大量抽象层和配置项，学一个简单任务要理解 Chain / Agent / Tool / Memory / Retriever 等十几个概念，学习曲线陡峭。
2. **快速迭代的不稳定性**：商业框架 API 变更频繁，版本升级后代码经常跑不起来，维护成本高。
3. **黑盒化的实现逻辑**：核心逻辑封装过严，开发者难以理解内部机制，缺乏深度定制能力；社区不活跃时问题反馈极慢。
4. **依赖关系复杂**：成熟框架携带大量依赖包，体积大，和其他项目配合易产生依赖冲突。

**自建框架的价值（从使用者 → 构建者的跃迁）：**

- **深度理解 Agent 工作原理**：亲手实现每个组件，才能真正懂思考过程、工具调用机制、各种设计模式的好坏。
- **获得完全控制权**：对每行代码可控，可按需精确调优，不受第三方设计理念束缚。
- **培养系统设计能力**：涉及模块化设计、接口抽象、错误处理等软件工程核心技能。
- **满足定制化**：金融/医疗/教育等垂直领域需要专属提示词、特殊工具集成、定制化安全策略；生产环境对性能/资源精确控制。

### 7.1.2 HelloAgents 框架的设计理念（核心）

围绕核心问题：**如何让学习者既能快速上手，又能深入理解 Agent 工作原理？** 四大设计理念：

1. **轻量级与教学友好的平衡**：核心代码按章节区分，保证有基础的人能完全读懂；依赖极简，除 OpenAI 官方 SDK 和几个必要库外不引入重型依赖，出问题能直接定位到框架本身。
2. **基于标准 API 的务实选择**：OpenAI API 已是行业标准，几乎所有 LLM 提供商都兼容。在此之上构建而非另起炉灶 → 兼容性好（迁移/集成逻辑一致）+ 学习成本低（不用学新概念模型）。
3. **渐进式学习路径**：每章代码存为可 pip 下载的历史版本，每个核心功能都是自己写的，按照自己的节奏前进，不产生概念跳跃。
4. **统一的"工具"抽象：万物皆为工具** 🔑 这是最关键的简化：**除核心 Agent 类外，一切皆为 Tools**。Memory（记忆）、RAG（检索增强）、RL（强化学习）、MCP（协议）等在别的框架中需要独立学习的模块，在 HelloAgents 里被统一抽象为一种"工具"。消除不必要的抽象层，回归"智能体调用工具"这一最直观的核心逻辑。

### 7.1.3 本章学习目标
- 掌握多提供商 LLM 封装（HelloAgentsLLM）
- 掌握框架核心接口：Message / Config / Agent 抽象基类
- 用框架化方式实现五种 Agent 范式：SimpleAgent / ReActAgent / ReflectionAgent / PlanAndSolveAgent / FunctionCallAgent
- 掌握统一工具系统：工具基类、注册机制、自定义工具、多源搜索工具、工具链与异步执行

---

## 7.2 HelloAgentsLLM 扩展

### 7.2.1 支持多提供商

核心思想：LLM 提供商虽多，但接口大同小异。封装一个 `HelloAgentsLLM`，自动识别 provider（openai / modelscope / ollama / vllm 等）。

```python
# my_llm.py —— 重写客户端，父类继承 think 等方法
class MyLLM(HelloAgentsLLM):
    def __init__(self, provider="openai"):
        super().__init__(provider=provider)
    def chat(self, messages):
        # 调用对应 provider 的 SDK
        ...
```

支持 provider 的方式：
- 直接实例化并指定：`llm = HelloAgentsLLM(provider="modelscope")`
- 从 `.env` 读取 API key / base_url
- 提供自动检测机制（见 7.2.3）

### 7.2.2 本地模型调用

本地部署 / 私有化场景（vLLM / Ollama 等）：
- **vLLM 方式**：启动 vLLM 服务加载开源模型（如 Qwen1.5-0.5B-Chat），首次自动下载模型，之后直接启动服务；通过 OpenAI 兼容接口调用（vLLM 提供 `/v1` 兼容端点），`.env` 配置 `base_url` 指向本地服务地址。
- **Ollama 方式**：安装 Ollama 后拉取模型，通过本地 API 调用。

两者的共同点：**都兼容 OpenAI API 协议**，所以只需在 `.env` / 构造时指定 base_url 和 provider，其余代码完全复用。

### 7.2.3 自动检测机制

根据 `.env` 中的配置（如存在 `OPENAI_API_KEY`、`MODELSCOPE_API_KEY`、或 `BASE_URL` 指向本地 ollama/vllm）自动判断 provider，**无需显式传 provider**，框架内部日志会打印检测到的 provider（如 `provider='ollama'`），后续调用方式完全一致。好处：一套代码，多环境无缝切换。

---

## 7.3 框架接口实现（三大核心文件）

### 7.3.1 Message 类（消息系统）

设计要点：
- 用 `typing.Literal` 把 `role` 严格限制为 `"user" / "assistant" / "system" / "tool"` 四种，**对齐 OpenAI API 规范，保证类型安全**。
- 核心字段：`content`、`role`；扩展字段：`timestamp`（日志）、`metadata`（预留扩展）。
- `to_dict()`：把内部 Message 对象转换为 OpenAI API 兼容的字典格式 → 体现 **"对内丰富，对外兼容"** 的设计原则。

### 7.3.2 Config 类（配置管理）

职责：把代码中硬编码的配置参数集中管理，支持从环境变量读取。
- 默认值：default_model、default_provider、temperature、max_tokens、debug、log_level、max_history_length 等。
- `from_env()` 类方法：从环境变量创建配置（DEBUG、LOG_LEVEL、TEMPERATURE、MAX_TOKENS）。
- `to_dict()`：转为字典方便传递。

### 7.3.3 Agent 抽象基类（框架顶层抽象）

用 `abc`（Abstract Base Classes，抽象基类）实现，强制所有具体 Agent 遵循同一"接口"：

```python
class Agent(ABC):
    def __init__(self, name, llm, system_prompt=None, config=None):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self._history = []

    @abstractmethod
    def run(self, input_text, **kwargs) -> str:
        """运行 Agent —— 所有子类必须实现"""
        pass

    def add_message(self, message): ...   # 添加消息到历史
    def clear_history(self): ...          # 清空历史
    def get_history(self): ...            # 获取历史副本
```

设计体现：
- 继承 `ABC` → 不能直接实例化（抽象类）。
- `@abstractmethod` 装饰的 `run()` → 强制所有子类实现，**保证所有智能体有统一执行入口**。
- 基类提供通用历史管理方法，与 Message 类协同 → 体现组件间联系、单一职责。

---

## 7.4 Agent 范式的框架化实现（五种范式）

本章把前几章学过的各种交互范式用"继承抽象基类 + 覆写 run()"的方式统一实现，形成框架的 Agent 家族。

### 7.4.1 SimpleAgent（最简单的基础 Agent）
- 最基础的对话 Agent：接收输入 → 拼 system_prompt + 历史 → 调用 LLM → 返回。
- 支持**动态添加工具**（`agent.add_tool(...)`）和**流式响应**。
- 测试项：基础对话（无工具）→ 带工具 → 流式 → 动态加工具 → 查看历史。

### 7.4.2 ReActAgent（思考-行动-观察循环）
沿用第一章的 Thought-Action-Observation 主循环，框架化后内置在 run() 中：
- 工作流程：**Thought（思考）→ Action（选工具+参数）→ Observation（工具结果）→ 循环直到 Final Answer**。
- 系统提示词包含：可用工具列表、工作流程、执行历史格式约束，引导 LLM 输出结构化推理链。

### 7.4.3 ReflectionAgent（反思型 Agent）
- 思路：**先生成回答 → 自我反思 → 根据反馈迭代改进**。
- 两阶段提示词：
  - 生成器：根据任务产出初版回答。
  - 反思器：对回答给出反馈意见（错误、改进点）。
  - 迭代：把"原始任务 + 上一轮回答 + 反馈意见"拼给生成器，产出改进版，循环若干轮。
- 支持自定义提示词（如专门用于代码生成的反思提示词）。

### 7.4.4 PlanAndSolveAgent（规划-执行 Agent）
把复杂问题拆解为"计划 + 逐步执行"：
- **规划器（Planner）提示词**：把原始问题拆成完整计划（步骤列表）。
- **执行器（Solver）提示词**：根据计划 + 历史步骤结果，执行当前步骤，得到中间结果。
- 循环：直到所有步骤完成。
- 支持自定义提示词（例如专门为数学问题定制规划/执行提示词，提升准确率）。

### 7.4.5 FunctionCallAgent（函数调用 Agent）
- 依赖模型的**原生函数调用（Function Calling / Tool Calling）能力**（OpenAI 系模型的 tools 参数）。
- LLM 输出结构化的函数名 + 参数 → 框架解析 → 调用对应工具 → 把结果回传给模型继续推理。
- 与 ReAct 的区别：工具选择由模型原生机制完成（结构化 JSON），而非靠提示词让模型输出文本格式，更稳定、更省 token。

**五种范式小结**（统一 run() 入口，差异在于 run 内部的组织逻辑）：
| 范式 | 核心机制 | 适用场景 |
|------|---------|---------|
| Simple | 直接对话 | 简单问答 |
| ReAct | 思考-行动-观察循环 | 需推理+多工具 |
| Reflection | 生成→反思→迭代 | 代码/写作质量提升 |
| PlanAndSolve | 先规划后执行 | 复杂多步任务 |
| FunctionCall | 模型原生函数调用 | 结构化工具调用 |

---

## 7.5 工具系统

### 7.5.1 工具基类与注册机制设计
- **万物皆为工具**：所有扩展能力（记忆、RAG、搜索引擎等）统一走工具接口。
- 工具基类定义统一结构：`name`（工具名）、`description`（描述，供 LLM 选择）、`run()/call()`（执行逻辑）、参数 schema。
- **注册机制**：Agent 维护一个工具表（dict：name → tool），`add_tool()` 注册，运行时按名字查表调用，未注册则报"未知工具"。

### 7.5.2 自定义工具开发
写一个计算器工具示例：定义工具类（含 name/description/run），`agent.add_tool(calculator)` 注册后即可被 Agent 调用。

### 7.5.3 多源搜索工具
封装多个搜索源（如 wttr.in 天气 / Tavily 网页搜索等），统一成一个高级搜索工具，Agent 只需调用一个工具即可获得多源结果。

### 7.5.4 工具系统的高级特性
- **工具链管理（Tool Chain Manager）**：把多个工具编排成链式流水线，前一个工具输出作为后一个工具输入。
- **异步工具执行（Async Tool Executor）**：支持异步调用，多个工具可并行执行，提升吞吐。

---

## 7.6 本章小结

- 自建框架的动机：摆脱黑盒、掌控一切、理解本质、深度定制。
- 核心设计理念：**轻量 + 教学友好 + 基于 OpenAI 标准 API + 万物皆为工具**——把记忆/RAG/RL/MCP 等复杂概念统一收敛到"工具"这一个最简单的心智模型。
- 三大接口：`Message`（统一消息格式）、`Config`（集中配置）、`Agent`（抽象基类 + 强制 run() 入口）。
- 五种范式框架化：Simple / ReAct / Reflection / PlanAndSolve / FunctionCall，统一 run() 入口，差异在内核组织逻辑。
- 统一工具系统：工具基类 + 注册机制 + 自定义工具 + 多源工具 + 工具链 + 异步执行。
- **承上启下**：本章基于前六章内容完善，也为后续高级知识（上下文工程 / 记忆 / 检索等）打下框架基础——后续章节会在本框架基础上扩展记忆、检索等能力（因为在本框架里它们都只是"工具"）。

---

## 习题自测（建议）
1. 为什么 HelloAgents 强调"万物皆为工具"？这解决了市面框架的哪些痛点？
2. Agent 抽象基类用 @abstractmethod 强制 run() 的实现，带来什么好处？
3. ReAct、Reflection、PlanAndSolve 三种范式在 run() 内部的组织逻辑有何区别？
4. FunctionCallAgent 相比 ReActAgent 在工具选择上有什么优势？
5. 如果要把 RAG 能力接入本框架，按"万物皆为工具"思想应该怎么做？
