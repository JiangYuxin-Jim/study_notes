# Learn Claude Code · 第四章：钩子函数（Hooks）

> 学习日期：2026-09-18
> 内容类型：AI 编程智能体（Coding Agent）工程实现原理
> 前置：前三章（Agent Loop / 工具调用 / 三层权限隔离）
> 一句话：**Hook = 在 Agent 生命周期的固定节点上自动执行的"钩子"，把权限检查、格式化、通知这类事从"靠模型自觉"变成"确定性的程序行为"。**

---

## 一、一句话理解 Hook

前三章我们学了：
- **Agent Loop** —— 模型自己转圈干活
- **工具调用** —— 模型提议动作，宿主程序执行
- **三层权限隔离** —— 执行前过三道闸（白名单 → 参数校验 → 人工确认）

但这里有个隐含问题：**权限检查、命令是否危险、要不要弹窗问用户——这些判断逻辑写在哪里？**

- 写死在 CLI 程序里 → 每个人要改都得改源码、发版，不可扩展
- 交给模型自己判断 → 不可靠（模型可能被 prompt injection 绕过）

**Hook 就是第三选择：把这类"检查 / 拦截 / 附加动作"抽成一个可配置的外部程序，在生命周期固定节点上被自动调用。**

> 用户原话总结得很准：**"把像命令许可检查的东西放到钩子函数那边"** —— 对，命令许可（permission）检查就是 Hook 最典型的应用（`PreToolUse` + `PermissionRequest`）。

### Hook 与普通工具调用的本质区别

| 维度 | 工具调用（Tool Use） | 钩子（Hook） |
|------|---------------------|-------------|
| **谁来触发** | 模型自己决定要不要调 | 宿主程序在固定节点**自动**触发 |
| **是否确定性** | 不确定（模型可能忘了调） | **确定**（条件满足必执行） |
| **能否阻断流程** | 工具只是干活 | **能拦截/阻断主流程**（如拒绝工具调用） |
| **典型用途** | 读文件、跑命令 | 权限校验、格式化、通知、注入上下文 |

> 官方文档原话：Hooks give you **deterministic control** —— certain actions **always** happen rather than relying on the LLM to choose to run them.
> **这正是 Hook 存在的根本理由：确定性。**

---

## 二、生命周期：Hook 能挂在哪

Claude Code 把整个会话切成若干"事件点"，Hook 按**三种粒度**分布：

| 粒度 | 事件 | 触发时机 |
|------|------|---------|
| **每会话** | `SessionStart` / `SessionEnd` | 会话开始/恢复、会话结束 |
| **每轮对话** | `UserPromptSubmit` / `Stop` / `StopFailure` | 用户提交提示词前、模型回复结束时、API 出错时 |
| **每次工具调用**（Agent Loop 内） | `PreToolUse` / `PostToolUse` / `PermissionRequest` / `PostToolUseFailure` … | 工具执行前/后、需要权限决策时 |
| 其他 | `PreCompact` / `PostCompact`、`SubagentStart/Stop`、`Notification`、`FileChanged`、`ConfigChange` … | 压缩上下文前后、子智能体启停、通知、文件变动 |

**完整生命周期（结合前三章的 Agent Loop 理解）：**

```
Setup（可选，CI 一次性准备）
   ↓
SessionStart ──────┬──── 每轮对话循环 ────────────────────────────┐
                   │                                            │
              UserPromptSubmit ──►【Agent Loop 内部】            │
                                     ↓                         │
                            ┌────────┴────────┐                │
                            │  PreToolUse      │ ← 可阻断工具调用 │
                            │       ↓          │                │
                            │  PermissionRequest│ ← 权限决策      │
                            │       ↓          │                │
                            │   工具真正执行     │                │
                            │       ↓          │                │
                            │  PostToolUse     │                │
                            │  (失败→PostToolUseFailure)        │
                            │  PostToolBatch（并行批量结束）      │
                            │  子智能体 SubagentStart / Stop     │
                            └────────┬────────┘                │
                                     ↓                         │
                                  Stop / StopFailure ──────────┘
                   ↓
        PreCompact → PostCompact
                   ↓
             SessionEnd
```

> ⚠️ 关键理解：**`PreToolUse` 在 Agent Loop 的每一次工具调用前都会触发**——这正是"命令许可检查"能挂进去的位置。

---

## 三、配置的三层结构

Hook 写在 JSON 设置文件里，**三层嵌套**：

1. **Hook 事件**（event）：挂在哪，如 `PreToolUse`
2. **matcher 匹配器**：什么条件下触发，如"只对 Bash 工具"
3. **hook handler（处理器）**：真正执行什么，如一条 shell 命令

```json
{
  "hooks": {
    "PreToolUse": [                      // ① 事件
      {
        "matcher": "Bash",               // ② 匹配器：只对 Bash 工具
        "hooks": [
          {
            "type": "command",           // ③ 处理器类型
            "command": "/path/to/check.sh"
          }
        ]
      }
    ]
  }
}
```

### 匹配器（matcher）的写法规则

| 写法 | 解释 |
|------|------|
| `""` / `"*"` / 省略 | 全部匹配 |
| 纯字母数字 `_,-` 空格 | **精确匹配**，或 `Edit\|Write`、`Edit, Write` 多值精确匹配 |
| 含其他字符 | **正则**（JavaScript 正则，非锚定，`Edit.*` 能匹配到 `NotebookEdit`） |
| MCP 工具 | 形如 `mcp__<server>__<tool>`，如 `mcp__memory__.*` 匹配 memory 服务器全部工具 |

> `if` 字段更进一步：用权限规则语法过滤到**参数级**，如 `"Bash(git *)"` 只在 git 命令时触发。

### 5 种处理器类型（不止 shell！）

| 类型 | 做什么 |
|------|--------|
| `command` | 跑 shell 命令（最常用） |
| `http` | POST 到 HTTP 端点 |
| `mcp_tool` | 调用已连接的 MCP 服务器上的工具 |
| `prompt` | 交给 Claude 模型单轮评估（**需要判断力**的场景） |
| `agent` | 起一个子智能体（可用 Read/Grep/Glob 调查后再决策，实验性） |

### 存放位置与作用范围

| 位置 | 范围 |
|------|------|
| `~/.claude/settings.json` | 我所有项目（本机） |
| `.claude/settings.json` | 单个项目（**可提交进仓库共享**） |
| `.claude/settings.local.json` | 单项目、不共享 |
| 企业管理策略 / 插件 / Skill 前置声明 | 组织级 / 随插件 / 从技能被调用起生效 |

> 多来源的 hook 是**合并**的，不是覆盖。

---

## 四、Hook 怎么和宿主程序"对话"

三种通信机制，按能力递增：

### 1. 输入：JSON 从 stdin 进来

```json
{
  "session_id": "abc123",
  "cwd": "/home/user/my-project",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" },
  "tool_use_id": "toolu_01ABC123..."
}
```

### 2. 简单控制：**退出码**

| 退出码 | 含义 |
|--------|------|
| `0` | 成功，不干预（也可以顺便打印 JSON 做精细控制） |
| `2` | **阻断**（PreToolUse 阻断工具调用、UserPromptSubmit 驳回提示词…） |
| 其他 | 默认**不阻断**（注意：`1` 也不阻断，这是个大坑 ⚠️） |

> ⚠️ **踩坑点**：想强制拦截策略，必须用 `exit 2`，用 `exit 1` 不但拦不住还会被当成非阻断错误放行。官方文档专门警告了这条。

### 3. 精细控制：**stdout 打印 JSON**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked by hook"
  }
}
```

> 文档还提醒：**同一条 hook 要么只用退出码，要么只用 JSON**，混用容易出意外（exit 2 的阻断优先级最高，连 `"allow"` 都盖不住）。

---

## 五、⭐ 核心：Hook 怎么接管权限检查

这是本次学习最核心的部分——**前三章讲的"三层权限隔离"，其可配置化的落地形式就是 Hook 事件**。

### 1. `PreToolUse`：工具执行前的闸门（对应第一、二层）

无论工具需不需要权限，**每次工具调用前都会触发**，返回 4 种决策：

| `permissionDecision` | 效果 |
|----------------------|------|
| `"allow"` | **跳过权限弹窗**，直接放行 |
| `"deny"` | **阻止工具调用**（reason 会给 Claude 看） |
| `"ask"` | **强制弹窗问用户**（即使在 auto 模式下也强制弹，分类器不能偷偷批准） |
| `"defer"` | 挂起（非交互 `-p` 模式下，交给调用方稍后恢复） |

还能改参数：
- `updatedInput` —— **执行前替换工具的入参**（例如把 `rm -rf` 换成安全命令）
- `additionalContext` —— 往上下文里插一段额外信息给模型看

**多个 hook 返回不同决策时的优先级：`deny` > `defer` > `ask` > `allow`**（拒绝优先，安全默认 ✅）

### 2. `PermissionRequest`：真正要问用户的那一刻（对应第三层）

区别很关键：
- `PreToolUse` = **每次工具调用都触发**（可以抢在权限判断之前就拦截）
- `PermissionRequest` = **只在"即将弹权限窗"或"本该自动拒绝"时才触发**

返回 `decision` 对象：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": { "command": "npm run lint" }
    }
  }
}
```

| 字段 | 作用 |
|------|------|
| `behavior` | `allow` / `deny` |
| `updatedInput` | allow 时改参数 |
| `updatedPermissions` | allow 时顺便**写权限规则**，下次不再问（对应我们熟悉的"总是允许"） |
| `message` / `interrupt` | deny 时告诉 Claude 原因 / 直接中断 |

`updatedPermissions` 里 `destination` 决定规则写哪：
`session`（仅本次会话，内存）→ `localSettings`（`.claude/settings.local.json`）→ `projectSettings` → `userSettings`

> 👉 这套东西就是我们平时用的 **"允许一次 / 总是允许 / 拒绝"** 背后的机制，只不过在 Claude Code 里可以**由你自己的脚本自动决定**，甚至自动写规则。

### 3. 三种权限相关事件的对照

| 事件 | 触发时机 | 能做的事 |
|------|---------|---------|
| `PreToolUse` | 每次工具调用前 | allow / deny / ask / defer、改参数（**能力边界 + 参数校验**） |
| `PermissionRequest` | 即将问用户权限时 | allow / deny、改参数、写权限规则（**人工确认的自动化**） |
| `PermissionDenied` | auto 模式自动拒绝后 | 告知模型可以重试（`retry: true`） |

**→ 与前三章三层的映射：**

| 前三章三层 | Hook 中的对应 |
|-----------|--------------|
| 第一层 工具白名单（能力边界） | 配置里不给某个 hook 装 → 或 `PreToolUse` 里 `deny` 掉 |
| 第二层 参数级校验 | `PreToolUse` 读 `tool_input`，按参数决定 allow/deny |
| 第三层 人工确认 | `PermissionRequest` 的 `ask` / 自动 `allow` + `updatedPermissions` |

---

## 六、其他典型 Hook 事件速览

| 事件 | 能做什么 | 关键点 |
|------|---------|--------|
| `UserPromptSubmit` | 注入上下文、**驳回提示词**（`decision: "block"`） | 每次提交前跑，默认超时只有 30s；stdout 纯文本会作为上下文进模型 |
| `Stop` | **拦住模型"收工"**，让它继续干 | 返回 block 可继续对话；连续 8 次被拦后强制结束（防死循环）；输入带 `last_assistant_message`、`background_tasks`、`session_crons` |
| `SessionStart` | 注入开发上下文（issue、最近改动）、设会话标题 | matcher：`startup` / `resume` / `clear` / `compact` / `fork`；输出 `additionalContext` |
| `PreCompact` | 上下文压缩前干预 | 可阻断压缩 |
| `PostToolUse` | 编辑后格式化（如 prettier）、跑 lint | 工具**已经执行完**，不能阻断，只能给 Claude 反馈（exit 2 把 stderr 给模型看） |
| `SubagentStart/Stop` | 子智能体的启停监控 | 主会话与子智能体的 hook 各自生效 |
| `Notification` | 桌面通知（"Claude 等你输入了"） | 最经典入门例子 |
| `FileChanged` / `ConfigChange` | 监听文件/配置变化 | 反应式环境管理（如 direnv） |

### 一个典型的实战例子：PostToolUse 自动格式化

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write" }
        ]
      }
    ]
  }
}
```

> 这段代码的含义：**每次 Claude 编辑或写入文件之后，自动拿被改的文件路径去跑 prettier。** 这就是"确定性地保证格式统一"——不靠模型记得格式化。

### 拦截危险命令的例子（配合 `exit 2`）

```bash
#!/bin/bash
input=$(cat)
command=$(jq -r '.tool_input.command' <<<"$input")

if [[ "$command" == rm* ]]; then
  echo "Blocked: rm commands are not allowed" >&2
  exit 2   # ← 必须是 2，才能真的阻断
fi

exit 0     # 不干预，走正常权限流程
```

---

## 七、与 hello-agents / 前三章的串联

| 学过的概念 | Hook 里的体现 |
|-----------|--------------|
| Agent Loop（TAO 循环） | 生命周期图就是循环的"钩子位"标注版：`PreToolUse` 挂在 Action 前，`PostToolUse` 挂在 Observation 后 |
| 工具调用链路（提议→权限→执行→回灌） | `PreToolUse` 就插在"权限"这一步，还能用 `updatedInput` 改写"提议" |
| 三层权限隔离 | 可配置化落地：白名单 / 参数校验 / 人工确认分别对应不同事件与决策字段 |
| OpenClaw 自身的 approval 卡片 + `/approve` | 就是 `PermissionRequest` + 人机交互的同类设计 |
| 上下文工程（GSSC） | `UserPromptSubmit` / `SessionStart` 的 `additionalContext` 就是"注入上下文"的钩子位 |

### 💡 最大认知升级

**Agent 的"可靠性"不来自模型，而来自宿主的确定性机制。**

- 模型负责"聪明"（推理、决策）
- **Hook 负责"靠谱"**（该拦的必拦、该做的必做、该记的必记）

前三章讲的是"怎么让模型能干活"，这一章讲的是"**怎么让工程层面可控地给模型加规矩**"——**可插拔、可配置、不改主干代码**。

一句话：**Loop 是骨架，Tools 是手脚，Permissions 是刹车，Hooks 是"电路的接线端子"——你想在哪一步接什么，就接什么。**

---

## 八、待补 / 后续

- [ ] 动手实践：写一个自己的 `PreToolUse` hook，拦截 `rm -rf` 类命令（复现上面的 bash 例子）
- [ ] 试试 `PostToolUse` 自动格式化（prettier / black）
- [ ] 了解 `prompt` / `agent` 类型 hook（需要判断力而非确定性规则的场景）
- [ ] 后续章节：记忆/上下文管理、多 Agent 协作、MCP 集成
