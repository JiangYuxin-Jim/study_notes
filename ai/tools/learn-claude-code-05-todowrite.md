# Learn Claude Code · 第五章：TodoWrite（任务清单）

> 学习日期：2026-09-20（笔记整理 2026-09-21）
> 内容类型：AI 编程智能体（Coding Agent）工程实现原理
> 前置：前四章（Agent Loop / 工具调用 / 三层权限隔离 / 钩子函数）
> 一句话：**TodoWrite 是一个"给模型自己用的工具"——它不改代码、不跑命令，只维护一份外部化的任务清单，让 Agent 在多步任务中"知道自己走到哪了"，也让用户看得见进度。**

---

## 一、一句话理解 TodoWrite

前四章我们学了：Loop 怎么转、工具怎么调、权限怎么拦、Hook 怎么接。

到这一章出现了一个新问题：

> **Agent 干一个"要跑 8 步"的活，怎么保证它不跑偏、不重复、不半路忘事？**

人做复杂任务靠什么？靠一张**写下来的清单**——写完一项打个勾，剩下的还看得见。

TodoWrite 就是把这件事搬进 Agent：**给模型一个写入/更新"待办清单"的工具**。

它跟其它工具本质不同：

| 维度 | 普通工具（Read / Bash / Edit） | TodoWrite |
|------|-------------------------------|-----------|
| **作用对象** | 外部世界（文件、命令、网络） | **Agent 自己的执行状态** |
| **产出** | 真实结果（文件内容、命令输出） | 一份清单（结构化的 tool_use / tool_result） |
| **谁受益** | 用户拿到结果 | **模型自己**（规划+追踪）**和用户**（可见进度） |
| **是否副作用** | 有（改了文件/环境） | 无（只改自己的任务状态） |

> 💡 关键认知：**TodoWrite 是"元工具"**。前四章讲的是"模型如何改变世界"，这一章讲的是"**模型如何管理自己**"——这是 Agent 从"能干活"走向"能可靠地干长活"的分水岭。

---

## 二、它在 Agent Loop 里的位置

```
UserPromptSubmit
   ↓
【Agent Loop】
   ├─ ① 理解任务 → 🆕 TodoWrite（写出清单，planning）
   ├─ ② 取第一项 → status: in_progress
   ├─ ③ 调工具干活（Read / Edit / Bash …）
   ├─ ④ 干完 → 该项 status: completed
   ├─ ⑤ 回到 ② 取下一项（循环）
   └─ ⑥ 全部完成 → 输出最终答复
   ↓
Stop
```

对比前几章的定位：

| 章节 | 类比 | 作用 |
|------|------|------|
| 第三章/第四章主线 | **Loop 是骨架** | 让模型能转圈干活 |
| 工具调用 | **Tools 是手脚** | 让模型能改变世界 |
| 三层权限 + Hooks | **Permissions 是刹车 / Hooks 是接线端子** | 让工程层面可控 |
| **第五 章 TodoWrite** | **是"导航仪 / 检查表"** | **让长任务不迷路、进度可见** |

> ⚠️ 注意：TodoWrite **不参与权限决策，也不阻断任何流程**——官方文档标注它的 "Permission required" 是 **No**。它只写自己的状态，不碰外部世界，所以不需要过三道闸。

---

## 三、⭐ 模型可用性：一个反直觉的现状

这是我们这次学习里最值得记的一条工程事实（**与很多旧教程讲的完全不同**）：

> **TodoWrite 在较新的模型上已经不默认提供了。**

官方文档（Tools reference · Task tool availability）原文大意：

- 任务追踪工具（`TodoWrite` / `TaskCreate` / `TaskGet` / `TaskUpdate` / `TaskList`）**默认只在 Claude 3.x、Opus 4~4.7、Sonnet 4~4.6、Haiku 4.5 上可用**
- **其它模型（包括 Claude Code 不认识的模型 ID，比如通过 LLM 网关接入的自定义模型）默认不给这些工具**
- 有这些工具时，默认给的是**四个 Task 工具**（Create/Get/Update/List）；设 `CLAUDE_CODE_ENABLE_TASKS=0` 才回退成 `TodoWrite`
- 该默认集从 **Claude Code v2.1.268** 起生效（TS Agent SDK 从 v0.3.268 打包）

**官方给的理由（很关键）**：

> 在更新的模型上，Claude **不写清单也能自己跟踪多步工作**，而这些工具的定义 + 提醒消息还会**占用上下文**。

→ 所以这是一次**"能力内化"后的减法**：模型自己长出这个能力了，就把外挂工具撤掉，省 context。

**想在一个本来没有的会话里打开它，有三种方式：**

| 方式 | 做法 |
|------|------|
| 权限白名单 | 在 `allowedTools` / `allowed_tools` 里**点名**该工具 |
| 工具名单 | 在 `tools` 选项里列出它（注意：`tools` 会**限制**会话内置工具，只保留你列的，要连带列上其它要用的） |
| 环境变量 | `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`（TypeScript 的 `env` 会**替换**子进程环境，记得 `...process.env` 展开继承；Python 的 `env` 是叠加） |

> 🧠 **认知升级**：工具集不是"越多越强"。当模型能力提升，**工具的边际价值 = 能力增益 − 上下文成本**，一旦为负就该砍。这跟第四章"Hook 用确定性补模型的不确定"是同一枚硬币的两面：**确定性交给宿主，能内化的能力就交还模型。**

---

## 四、Todo 的生命周期（四态）

官方文档给得很清楚，每一项 todo 走四个状态：

| 阶段 | 状态 | 触发 |
|------|------|------|
| **Created** | `pending` | 模型识别出一个任务，加进清单 |
| **Activated** | `in_progress` | 开始做这件事 |
| **Completed** | `completed` | 成功做完 |
| **Removed** | `deleted` | 不再需要（用 `TaskUpdate` 传 `status: "deleted"`，不是"删除接口"） |

> 注意第 4 条的设计：**没有独立的 delete 工具，删除也是"一次状态更新"**——所有变更都走同一个 `TaskUpdate` 通道，模型的心智负担更低（只需要记住"改状态"这一件事）。

**模型什么时候会建清单？** 官方列了四类场景：

1. **复杂多步任务**：需要 3 个以上独立动作的
2. **用户给的任务列表**：用户一口气提了好几件事
3. **较长的操作**：需要进度追踪才不慌的
4. **用户明确要求**：直接说"用 todo 组织一下"

反向：**很短或单步的请求，Claude 会跳过 todo**（避免为了用工具而用工具）。

---

## 五、输入输出长什么样（SDK 视角）

在消息流里，todo 活动就是普通的 `tool_use` 块——**没有特殊协议，就是工具调用**，这是它最优雅的地方：

```jsonc
// 新建
{ "name": "TaskCreate", "input": { "subject": "搭建首页", "activeForm": "正在搭建首页" } }

// 更新状态
{ "name": "TaskUpdate", "input": { "taskId": "3", "status": "in_progress" } }

// 结果里带回真实 ID（TaskCreate 的 tool_use_result）
{ "task": { "id": "3", "subject": "搭建首页" } }
```

**几个工程细节（踩坑点 ⚠️）：**

| 细节 | 说明 |
|------|------|
| **create 的 ID 不在输入里** | 新建时模型不知道 ID，真实 ID 在**结果**里返回 → 想要"创建↔更新"关联，必须**等 tool_result**（`tool_use_result.task.id`） |
| **字段名会漂** | 模型可能吐 `id` / `task_id` / `active_form`；Claude Code 执行前会**纠正**成 `taskId` / `activeForm`，但**流式输出里看不到这次纠正** → 解析要**防御式**取：`input.taskId ?? input.id ?? input.task_id` |
| **`activeForm` vs `subject`** | `subject` 是"要做什么"（名词式），`activeForm` 是"正在做什么"（进行时）。**进行中的项显示 activeForm**，未开始/已完成显示 subject → 用户体验上的小设计 |
| **任务系统消息 ≠ todo** | `SDKTaskNotificationMessage` 那些报的是**后台任务**（后台命令、子智能体）；todo 只看 `tool_use` 块。**两套东西别混** |

**在应用里渲染进度**（伪代码，来自官方 Python 示例的思想）：

```python
class TaskTracker:
    def display_progress(self):
        completed = len([t for t in self.tasks.values() if t["status"] == "completed"])
        print(f"\nProgress: {completed}/{len(self.tasks)} completed")
        for task_id, task in self.tasks.items():
            icon = "✅" if task["status"] == "completed" else "🔧" if task["status"] == "in_progress" else "❌"
            text = task["activeForm"] if task["status"] == "in_progress" and task.get("activeForm") else task["subject"]
            print(f"{task_id}. {icon} {text}")
```

> 👉 这一套就是你在 Claude Code 界面里看到的**"Claude 正在做什么"的进度条**的真身：它**不是模型在说话，而是在渲染 tool_use 流**。

---

## 六、终端里的任务清单（用户视角）

| 操作 | 说明 |
|------|------|
| `Ctrl+T` | 展开/收起任务清单视图（一次最多显示 5 项；没建过任务时按了没反应） |
| 保持展开 | 下次 `--resume` / `--continue` 恢复到展开态；清单为空时默认收起 |
| 查看/清空 | 直接对 Claude 说 "show me all tasks" / "clear all tasks" |
| **跨压缩存活** | ✅ **任务清单能跨上下文压缩保留**，帮模型在大项目上保持组织性 |
| 跨会话共享 | 设 `CLAUDE_CODE_TASK_LIST_ID=my-project` → 用 `~/.claude/tasks/` 下的具名目录，多会话共享一份清单 |

> 💡 **`CLAUDE_CODE_TASK_LIST_ID` 是个被低估的功能**：等于把"待办清单"从**会话内变量**升级成**项目级持久状态**，多开几个 agent 干活可以看同一份清单。

⚠️ 别混淆：**任务清单（todo）** ≠ **`/tasks` 的后台任务视图**（那个看的是运行中的 shell 和子智能体）。

---

## 七、与前四章的串联

| 学过的概念 | TodoWrite 里的体现 |
|-----------|-------------------|
| **Agent Loop（TAO 循环）** | 清单在 **Thought/Action 之间**起到"外部化的思考锚点"：把"我打算怎么做"从隐式的推理变成显式的结构化状态 |
| **工具调用（提议→权限→执行→回灌）** | TodoWrite **完整走了这条链路**，但因为是纯自状态写入，Permission 一栏是 No——**它是"工具调用范式"的最干净样本** |
| **上下文工程** | 清单是**给模型看的上下文**：每轮重新读一遍，"还差哪几项"不用靠记忆推断 |
| **第三章 hello-agents 的 Reflection / PlanAndSolve 范式** | TodoWrite 就是 **Plan-and-Solve 的工程化落地**：先 Plan（建清单），再 Solve（逐项执行），边做边更新 |
| **第四章 Hooks** | Hook = **确定性地给模型加规矩**；TodoWrite = **模型自己给自己加结构**。一个外部约束，一个自我约束 |

### 💡 最大认知升级

**"外部化的状态"是长任务可靠性的来源。**

- 模型的上下文窗口是**有限的、会丢的（压缩、截断）**
- 但一份写在**结构化工具状态里**的清单，可以跨轮次、跨压缩存活
- 于是"这个任务做到哪了"不再依赖模型的记忆，而依赖一份**可读、可渲染、可持久化的数据**

一句话：**Loop 是骨架，Tools 是手脚，Permissions 是刹车，Hooks 是接线端子，TodoWrite 是挂在仪表盘上的任务清单——它不改变车怎么跑，但让司机（和乘客）始终知道开到哪了。**

而更值得记住的是那条**工程趋势**：**当模型把这个能力内化后，工具就被撤掉了。** 这提示我们判断一个 Agent 工具该不该存在，标准不是"能不能做"，而是"**模型自己做得好不好 + 占不占上下文**"。

---

## 八、待补 / 后续

- [ ] 动手实践：用 Agent SDK 跑一个多步任务（如"建静态网站：首页+关于页+样式表"），观察 `TaskCreate` / `TaskUpdate` 的 tool_use 流
- [ ] 试 `CLAUDE_CODE_TASK_LIST_ID` 跨会话共享清单，验证 `~/.claude/tasks/` 目录结构
- [ ] 对比 `TodoWrite` 与四个 Task 工具（Create/Get/Update/List）的差异，理解为什么官方默认迁到后者
- [ ] 后续章节：记忆/上下文管理、多 Agent 协作、MCP 集成

---

> 📎 参考：Claude Code 官方文档 —— Tools reference（Task tool availability）、Track todos（Agent SDK）、Interactive mode（Task list）
