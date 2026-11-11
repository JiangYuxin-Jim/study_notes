# Learn Claude Code · 前三章（Agent Loop / 工具调用 / 三层权限隔离）

> 学习日期：2026-09-17
> 内容类型：AI 编程智能体（Coding Agent）工程实现原理
> 定位：AI 主线下的「工程实现」板块。与 hello-agents 学到的 Agent 范式一一对应——**理论在 hello-agents，工程化落地看 Claude Code**。

---

## 一、为什么学这个

hello-agents 讲的是 Agent 的**理论范式**（ReAct、Reflection、Plan-and-Solve、Function Calling），而 Claude Code 是目前最成熟的**生产级 Coding Agent**，前三章把「一个真正能跑、能用的 Agent」的三个必备件拆得最清楚：

| 必备件 | 作用 | 一句话 |
|--------|------|--------|
| **Agent Loop** | 让模型能「多轮自主干活」 | 大脑的思考循环 |
| **工具调用（Tool Use）** | 让模型能「动手改变世界」 | 大脑的手脚 |
| **三层权限隔离** | 让「动手」这件事可控可审 | 手脚的安全带 |

> 三者缺一不可：只有 Loop 没有工具 = 只会聊天的空想家；有工具没有权限控制 = 危险。**工程化的 Agent = 循环 + 工具 + 权限。**

---

## 二、Agent Loop（智能体循环）

### 1. 本质
Agent Loop 就是 hello-agents 里学过的 **TAO 循环（Thought → Action → Observation）** 的工程实现版本 —— 一个 **while 循环**，不断把「模型的输出」变成「给模型的新输入」，直到任务完成。

### 2. 循环体（核心流程）

```
用户输入 (prompt)
      ↓
┌─────────────────────────────────────┐
│  while (任务未结束) {               │
│    ① 把当前全部上下文发给 LLM        │
│    ② LLM 返回：                     │
│         - 纯文本 → 任务完成，退出     │
│         - 工具调用请求 → 继续         │
│    ③ 执行工具，拿到结果              │
│    ④ 把「工具结果」追加进上下文       │
│    ⑤ 回到 ①，再问一次 LLM           │
│  }                                  │
└─────────────────────────────────────┘
      ↓
  最终答复
```

### 3. 关键理解点

- **循环的驱动力不是"预设流程"，而是模型的自主决策**：模型自己决定「还要不要继续、下一步调什么工具」——这正是 Agent 与 Workflow 的本质区别（Workflow 是写死的 if-else 编排）。
- **上下文是累加的（conversation state）**：每一轮都把历史消息 + 工具结果一起发回去，模型才有"记忆"，才能基于上一步的观察做下一步决策。→ 这就是为什么**上下文长度是 Agent 的核心瓶颈**（直接对应 hello-agents 第九章「上下文工程」GSSC：Gather→Select→Structure→Compress）。
- **循环必须有终止条件**，通常有三类：
  1. 模型不再请求工具（自然结束）
  2. 达到最大轮数上限（max turns / max iterations，防止死循环烧 token）
  3. 用户中断 / 出错
- **循环的每一步都要"可观测"**：把每轮的思考、工具名、参数、结果打印/记录出来，才便于调试。这就是我们在 hello-agents 第一章手工实现的 `while True` + 打印 Observation 的升级版。

### 4. 与 hello-agents 的对应
| Claude Code | hello-agents |
|-------------|--------------|
| Agent Loop | 第一章的 TAO 主循环 / 第二章旅行助手的 `while` 循环 |
| 每一轮 = 一次 LLM 调用 | ReAct 的 Thought→Action→Observation |
| 终止条件 | `if not response.tool_calls: break` |

---

## 三、工具调用（Tool Use / Function Calling）

### 1. 本质
让 LLM 从「只能输出文本」变成「能输出结构化的动作指令」。模型不直接执行任何东西，它只是**输出一个"我要调 XX 工具，参数是 YY"的 JSON**，由外层程序（Harness）解析并真正执行。

> **关键认知：模型永远只是"提议"，执行权在宿主程序手里。** 这条认知是理解下一节权限控制的前提。

### 2. 一个工具的定义包含什么

| 部分 | 说明 |
|------|------|
| **name** | 工具名（唯一标识、模型调用时用它） |
| **description** | 自然语言描述——**最重要**，模型全靠它判断「什么时候该用这个工具」 |
| **input_schema** | JSON Schema 定义参数的结构/类型/是否必填，模型据此生成合法参数 |
| **执行逻辑（handler）** | 真正干活的代码，运行在宿主程序里 |

```jsonc
// 工具定义（给模型看的"说明书"）
{
  "name": "read_file",
  "description": "读取指定路径的文件内容，用于查看代码或文本",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": { "type": "string", "description": "文件的绝对或相对路径" }
    },
    "required": ["path"]
  }
}
```

### 3. 一次工具调用的完整链路

```
① 把「工具清单」随上下文一起发给 LLM
        ↓
② LLM 判断需要动手 → 返回 tool_use 块：
   { "type": "tool_use", "name": "read_file", "input": {"path": "a.py"} }
        ↓
③ 宿主程序解析这个结构 → 找到对应 handler
        ↓
④ ★ 权限检查（见第四节）→ 允许 / 询问 / 拒绝
        ↓
⑤ 真正执行 → 拿到结果
        ↓
⑥ 把结果包成 tool_result 塞回上下文
        ↓
⑦ 回到 Agent Loop，把上下文再发给 LLM
```

### 4. 几个容易踩的点

- **description 写得差 = 模型不会用或乱用**：工具描述的清晰度直接决定 Agent 的成功率。
- **参数校验不能省**：模型可能生成不合法 JSON / 缺必填字段 / 路径穿越（`../../etc/passwd`），宿主必须校验。
- **工具结果要可读**：报错信息也要回给模型（"文件不存在"比直接崩掉更有用，模型能自我纠正重试）。
- **工具粒度**：太粗（一个"万能工具"）模型难用；太细（几十个工具）模型选择困难。→ 对应 hello-agents 第七章的**统一工具系统**（工具基类 + 注册表 + 工具链）。
- **并行工具调用**：一轮里模型可能同时请求多个工具，宿主可并发执行以提速。

### 5. 与 hello-agents 的对应
- hello-agents 第七章「万物皆为工具」+ 统一工具系统 = 这里的工具定义/注册/执行。
- hello-agents 第六章 LangGraph/CAMEL 的 Function Calling 范式 = 这里 tool_use 的前置理论。

---

## 四、三层权限隔离（Permission / Safety）

### 1. 为什么需要
Agent Loop + 工具调用 = 模型能**真实地读写文件、执行命令、发网络请求**。一旦模型判断失误（或被恶意输入诱导 = prompt injection），后果是真实的：删库、泄密、rm -rf。

> **原则：模型不可信（untrusted），一切动作在执行前都要过闸。** 这也是本 skill 安全观的直接体现。

### 2. 三层结构（本课核心）

| 层 | 名称 | 作用 | 举例 |
|----|------|------|------|
| **第一层** | **工具白名单**（能力边界） | 决定 Agent **有哪些工具可用**，不给的工具模型压根调不到 | 只暴露 read_file / grep / edit，不暴露 shell_exec |
| **第二层** | **参数级校验**（范围约束） | 同一个工具，限制**参数取值**，把危险调用拦在门外 | edit 只允许改 workspace 目录内；路径规范化后校验不逃逸 |
| **第三层** | **人工确认**（Human-in-the-loop） | 对高风险动作，**执行前弹给用户确认**，批准才跑 | 首次执行某命令 → 弹窗 "是否允许执行 rm xxx？" 允许一次 / 永久允许 / 拒绝 |

### 3. 三层各自的分工（理解要点）

- **第一层是"有没有这个能力"** —— 静态、粗粒度，在工具注册阶段就定死。最小权限原则：用不到的能力绝不放出来。
- **第二层是"这个参数合不合法"** —— 动态、细粒度，在执行前做 schema + 业务校验（路径穿越、越界、超长、注入）。
- **第三层是"要不要人拍板"** —— 兜底，针对不可逆/高风险操作（删除、外发、支付、git push --force）。人确认后这次放行，可记成"允许一次"或"本会话允许"。

```
模型提议动作
   ↓
[第一层] 工具在白名单里吗？ ── 否 → 拒绝，返回错误给模型
   ↓ 是
[第二层] 参数合法 & 在允许范围内吗？ ── 否 → 拒绝，返回错误给模型
   ↓ 是
[第三层] 是高风险动作吗？ ── 是 → 暂停，问人（允许一次/总是允许/拒绝）
   ↓ 批准
  执行
```

### 4. 设计思想
- **纵深防御（Defense in Depth）**：三层不是三选一，而是层层叠加，任一层都能兜住。
- **默认拒绝（deny by default）**：没明确允许的就不做。
- **可审计**：每次工具调用都留日志（谁、什么工具、什么参数、批没批）。
- **最小权限**：给 Agent 的权限 = 完成任务的最小集合，能读就别给写，能单目录就别给全盘。

### 5. 与我们自己 OpenClaw 的对应
本机 OpenClaw 的机制就是这套思想的实例：
- 工具集由 policy 过滤（**第一层**：可用工具清单）
- `tools.exec` 的 security / 白名单 / 路径限制（**第二层**）
- exec 高危命令触发 approval 卡片，需 `/approve`（**第三层**：人工确认 + allow-once 语义）

---

## 五、三章串起来：一个 Agent 的最小骨架

```python
# 伪代码：Claude Code 前三章的浓缩
TOOLS = load_tools()                    # 工具清单（含 name/desc/schema）
WHITELIST = ["read_file", "edit" ]      # ← 第一层：能力边界

def agent_loop(user_input, max_turns=20):
    messages = [{"role": "user", "content": user_input}]
    for _ in range(max_turns):                   # ← 终止条件②
        resp = llm(messages, tools=TOOLS)        # ① 请求模型
        messages.append(resp)

        if not resp.tool_calls:                  # ← 终止条件①：不再动手
            return resp.text

        for call in resp.tool_calls:
            if call.name not in WHITELIST:       # ← 第一层
                result = "权限拒绝：工具不可用"
            elif not validate(call.input):       # ← 第二层
                result = "权限拒绝：参数非法"
            elif is_risky(call) and not ask_user(call):  # ← 第三层
                result = "用户拒绝执行"
            else:
                result = execute(call)           # ⑤ 执行
            messages.append(tool_result(result)) # ⑥ 结果回灌上下文
    return "达到最大轮数，任务未完成"
```

**一句话总结：Agent = 一个带终止条件的循环（Loop） + 一套能动手的工具（Tools） + 一层让人类放心的刹车（Permissions）。**

---

## 六、本课收获（对照 hello-agents）

| 之前（hello-agents 理论） | 现在（Learn Claude Code 工程） |
|---------------------------|-------------------------------|
| ReAct/TAO 循环、Agent vs Workflow | 懂了循环的真实工程结构（终止条件、上下文累加、可观测） |
| Function Calling 范式、统一工具系统 | 懂了工具的真实定义方式（description 决定成败、schema 校验） |
| "Agent 要安全"（抽象） | 懂了安全怎么落成三层（白名单 → 参数校验 → 人工确认） |

👉 **最大认知升级**：模型输出的永远是「提议」，真正的执行权与刹车始终在宿主程序手里。工程化 Agent 的难点不在"让模型聪明"，而在"让模型的每次动手都可控"。

---

## 七、待补 / 后续

- [ ] 前三章后的章节：记忆/上下文管理、多 Agent 协作、MCP 集成等（后续补充）
- [ ] 可动手实践：用 Python 手写一个 mini agent loop（read/write 两个工具 + 三层权限），复现本课骨架
