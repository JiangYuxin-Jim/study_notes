# Learn Claude Code · 第六章：Subagent 与 Skill 加载

> 学习日期：2026-09-21
> 内容类型：AI 编程智能体（Coding Agent）工程实现原理
> 前置：前五章（Agent Loop / 工具调用 / 三层权限隔离 / 钩子函数 / TodoWrite）
> 一句话：**前五章都在讲"一个 Agent 怎么干活"，这一章开始讲"怎么用上下文工程把 Agent 组织起来"——Subagent 解决"上下文别被淹"，Skill 解决"知识别常驻"，两者正好是一枚硬币的两面。**

---

## 一、一句话理解这两个东西

到第五章为止，Agent 的能力（Loop / Tools / Permissions / Hooks / Todo）都齐了。但真干起活来会撞上两堵墙：

| 墙 | 症状 | 解法 |
|----|------|------|
| **上下文被淹** | 让它"去把整个代码库摸一遍"，几十个文件的搜索结果全灌进主对话，主对话直接废掉 | **Subagent**：换个窗口干活，只把摘要带回来 |
| **知识常驻太贵** | 一堆规范、清单、流程塞进 CLAUDE.md，每轮请求都烧一遍 token，但 90% 的时间用不上 | **Skill**：描述常驻（便宜），正文**用到才加载** |

一句话总结：

- **Subagent = 上下文隔离**（"派个下属去干，回来只汇报结论"）
- **Skill = 按需加载的知识/流程**（"手册放架子上，用到哪本抽哪本"）

> 官方文档对 Subagent 的定义非常直白：**当"一个副任务会把搜索结果、日志、文件内容灌满你的主对话而你根本不会再回头看它们"时，就用 subagent** —— 它在自己的上下文里干完活，只返回摘要。

---

## 二、⭐ 上下文成本：为什么要搞这两个东西

这是本章的**核心视角**，来自官方《Extend Claude Code》的对照表：

| 功能 | 何时加载 | 加载什么 | 上下文成本 |
|------|---------|---------|-----------|
| **CLAUDE.md** | 会话开始 | 全文 | **每次请求都付** |
| **Skills** | 会话开始 + 使用时 | 开始时只加载**描述**，用到才加载**全文** | 低（每轮只付描述）|
| **MCP servers** | 会话开始 | 工具**名字**；schema 按需 | 用到前很低 |
| **Subagents** | 被 spawn 时 | 全新上下文（或用指定 skills）| **与主会话隔离** |
| **Hooks** | 触发时 | 无（在外部跑）| **零**（除非返回 additionalContext）|

**这张表值得反复看，它解释了整个扩展体系的"经济学"：**

- CLAUDE.md 是**订阅制**（每轮都付，所以要短，官方建议 < 200 行）
- Skill 是**按次付费**（描述常驻很便宜，正文只在用到的那轮进场）
- Subagent 是**独立核算**（完全不占主会话额度）
- Hook 是**免费外包**（跑在宿主里，不占模型上下文）

→ 第五章我们学的那条判断（工具价值 = 能力增益 − 上下文成本）在这里升级成了**一套完整的选型框架**：**不是"能不能做"，而是"这份东西该不该常驻、该在谁的上下文里付钱"。**

---

## 三、Subagent（子智能体）

### 1. 本质：隔离的上下文窗口 + 独立人格

每个 subagent：

- **独立上下文窗口**（看不到你的对话历史、已读文件、已加载的 skill）
- **独立系统提示词**（自定义 subagent 自己写；内置的有预设）
- **独立工具集**（可以限定它能用哪些工具 → 顺手变成"约束手段"）
- **独立权限**（有自己的 permissionMode）

主会话**只收到它的最终结果**（摘要），中间的搜索、日志、文件内容全留在它的窗口里。

**它能帮你做什么（官方五条）**：

| 好处 | 说明 |
|------|------|
| **保住上下文** | 探索/实现过程不进主对话 |
| **强制约束** | 限定工具集（比如只读）|
| **复用配置** | user 级 subagent 跨项目通用 |
| **专精行为** | 聚焦某个领域的系统提示词 |
| **控制成本** | 把任务路由到更快更便宜的模型（如 Haiku）|

### 2. 内置的四个 + 其他

| Subagent | 模型 | 工具 | 何时用 |
|----------|------|------|--------|
| **Explore** | 继承主会话（Claude API 上封顶 Opus）| **只读**（禁 Write/Edit）| 搜代码、摸代码库，**不修改** |
| **Plan** | 继承主会话 | **只读** | plan 模式下的调研，为主会话出方案铺路 |
| **general-purpose** | 按模型顺序 | subagent 可用的**全部**工具 | 既要探索又要改的多步复杂任务 |
| `claude` | 跟随模型顺序 | 全部 | 兜底（什么活都能接，也是后台会话的默认 agent）|

⚠️ **一个反直觉的细节**：**Explore 和 Plan 会跳过 CLAUDE.md 和 git status**（为了快和便宜）；其它 subagent 默认都会加载各级 CLAUDE.md。

> 💡 也就是说：**"研究型" subagent 故意做成"轻装上阵"的**——连项目规则都不带，纯去摸信息。规则在主会话里还在，读结果时照样能用上，所以大多数规则不需要下沉到 subagent。

**还能怎么禁掉内置的：**

- `permissions.deny` 里点名某个类型 → 禁单个
- `permissions.deny` 直接禁 `Agent` 工具 → **禁止任何委派**
- `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` → 只去掉 Explore/Plan（Claude 改为自己直接读文件）

### 3. 配置：Markdown + YAML frontmatter

**一个 subagent 就是一个 md 文件**，只有 `name` 和 `description` 是必填：

```markdown
---
name: code-improver
description: 扫描文件并给出可读性/性能/最佳实践改进建议。代码改完后主动使用。
tools: Read, Grep, Glob
model: sonnet
permissionMode: default
maxTurns: 20
skills: api-conventions        # 预加载指定 skill 全文
---

你是一位资深代码审查员，关注代码质量、安全性和最佳实践……
```

**Frontmatter 字段速查：**

| 字段 | 作用 |
|------|------|
| `name` | 唯一标识（小写字母+连字符，**不能含 `:`**，那是插件作用域的保留符）|
| `description` | **决定 Claude 何时委派给它** ⭐ 也是唯一常驻上下文的部分，要短 |
| `tools` / `disallowedTools` | 白名单 / 黑名单（注意：`disallowedTools` 里写了 `Bash(git push *)` 这类带限定符的，会**整条工具**被移除）|
| `model` | `sonnet`/`opus`/`haiku`/完整 ID/`inherit` |
| `permissionMode` | `default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`/`plan` |
| `maxTurns` | 最大回合数；到顶会把输出标记为 **partial**（可 resume 续跑）|
| `skills` | **启动时预加载**的 skill（注入的是**全文**，不只是描述）|
| `omitClaudeMd` | 跳过 user/project/local 的 CLAUDE.md |
| `background` | 强制后台运行 |
| `memory` | 给它自己的持久记忆（主会话的 auto memory 不加载）|

### 4. 存在哪：五级作用域（按优先级）

| 位置 | 范围 | 优先级 |
|------|------|--------|
| Managed settings（组织级）| 全组织 | 1（最高）|
| `--agents` CLI 参数（JSON）| 仅当前会话，**不落盘** | 2 |
| `.claude/agents/` | 当前项目（**建议进版本控制，团队共享**）| 3 |
| `~/.claude/agents/` | 你的所有项目 | 4 |
| 插件的 `agents/` 目录 | 插件启用处 | 5（最低）|

> ⚠️ `name` 必须在整棵树里唯一。同名时：**嵌套项目目录里"离工作目录最近的"胜出**；同一目录内同名则按**文件系统读取顺序**取一个（没有文档化优先级——所以要靠 `/doctor` 查重）。
>
> 📁 `.claude/agents/` 是**递归扫描**的，可以按 `agents/review/`、`agents/research/` 分子目录整理——**子目录不影响标识**（标识只来自 `name` 字段）。但**插件的**子目录会进作用域名：`my-plugin:review:security`。

### 5. 怎么触发

| 方式 | 说明 |
|------|------|
| **自动委派** | Claude 根据你的请求 + 各 subagent 的 `description` 决定。想让它"更主动"，描述里写 **"use proactively"** |
| **自然语言点名** | "用 code-reviewer 这个 subagent 看看我最近的改动" |
| **@ 提及**（保证触发）| `@"code-reviewer (agent)"` 或手敲 `@agent-code-reviewer` —— 它控制的是**用哪个** subagent，提示词仍由 Claude 根据你说的话来写 |
| **整场会话都用它** | `claude --agent code-reviewer`；或写进 `.claude/settings.json` 的 `agent` 字段（CLI 参数优先）|

> ⚠️ **15,000 token 警告线**：所有自定义 subagent 的 `description` 加起来超过 15,000 token，启动会告警（而且**仍然全部加载**）。官方建议：**`description` 写短，细节挪进系统提示词**（系统提示词只在该 subagent 运行时才加载）。

### 6. 前台 / 后台

| | 前台 | 后台 |
|---|------|------|
| 行为 | **阻塞主对话**直到完成 | **并发**跑，你继续干活 |
| 权限提示 | 正常透传给你 | 在主会话里弹，**并标明是哪个 subagent 在问**；Esc 可拒掉**这一个**工具调用而不杀掉它 |
| 工具集 | 完整 | **更窄的内置工具集**（对话 fork 和 resume 的除外）|

**默认怎么选（按顺序命中第一条）：**

1. 由 **agent team 队友** spawn 的 → 强制**前台**
2. 设了 `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` → 一律**前台**
3. **fork 模式开着**（交互式会话默认开）→ 一律**后台**，Claude 无法要求前台
4. fork 模式关着 → 默认后台；**需要结果才能继续时**才前台

> 💡 一句话：**"能不能等"决定前后台，而 fork 模式一开就"全都后台化"了。**

### 7. ⭐ Subagent 启动时到底加载了什么

**非 fork 的 subagent 的初始上下文 =**

| 内容 | 说明 |
|------|------|
| **自己的系统提示词** | 自定义的写入 md 正文；**不是** Claude Code 的系统提示词 |
| **任务消息** | Claude 写的委派提示词（它会把任务**总结**一遍再交出去）|
| **CLAUDE.md 各级** | `~/.claude/CLAUDE.md`、项目规则、`CLAUDE.local.md`、组织策略、AGENTS.md（Explore/Plan 跳过；`omitClaudeMd: true` 只保留组织策略）|
| **git status** | 父会话开始时的快照（非 git 仓库或关掉时没有；Explore/Plan 一律跳过）|
| **预加载的 skills** | `skills` 字段里那些的全文 |
| **兄弟名册**（sibling roster）| 列出 `main` 和会话里其它具名 agent，作为 `SendMessage` 的合法 `to` 值 |

**明确不传过去的**：

- ❌ 你的**输出风格**（output style）——每个 subagent 跑自己的系统提示词
- ❌ 主会话的 **auto memory**
- ❌ 主会话的**上下文窗口大小**——subagent 的窗口由**它自己的模型**决定（换小模型 = 给小窗口）

> 🎯 **实操建议**：既然大多数规则主会话读结果时仍然有效，**没必要把规则都下沉到 subagent**；但如果某条规则必须让它遵守（比如"忽略 `vendor/` 目录"），**就在委派的那句提示词里再说一遍**。

### 8. Resume：可以接着干，不是一次性

- **每次调用都是新实例**；想续用就让 Claude resume 它（subagent 完成时会拿到 agent ID）
- Resume 后**保留完整历史**（含之前的工具调用、结果、推理，以及它自己 spawn 的 subagent 送回来的结果）——**从停下的地方接着走，而不是重来**
- ⚠️ 内置的 **Explore / Plan 是一次性的、不返回 agent ID，无法 resume**；要续跑就用 general-purpose 或自定义 subagent

### 9. 顺带：对话 fork（fork the current conversation）

与上面几个是不同东西：**fork 会继承父对话**（而不是从零开始）——所以它能看到你们聊过的一切。规则上也有例外（前后台、工具集豁免都不同）。**技能里的 `context: fork` 并不是这个**（见下节）。

---

## 四、Skill（技能）

### 1. 本质：一份"用到才加载"的知识/流程

> 官方原话：**当你发现自己反复往对话里粘贴同一段指令、清单或多步流程时；或者 CLAUDE.md 里某一段已经从"事实"长成了"流程"时——就该写成 skill。**
>
> 与 CLAUDE.md 最大的区别：**Skill 的正文只在被使用时才加载**，所以再长的参考资料，在你需要之前**几乎不花成本**。

**几个关键事实：**

- Skill 遵循 **Agent Skills 开放标准**（agentskills.io，跨 AI 工具通用），Claude Code 在其上加了扩展（调用控制、subagent 执行、动态上下文注入）
- **自定义命令已经并入 skill**：`.claude/commands/deploy.md` 和 `.claude/skills/deploy/SKILL.md` 都产生 `/deploy`，行为一致；老文件继续可用
- **内置 skill**（bundled skills）：`/doctor`、`/code-review`、`/batch`、`/debug`、`/loop`、`/claude-api` 等。它们是**提示词型**的（给 Claude 详细指令，让它用自己的工具去编排），与"内置命令直接执行固定逻辑"不同
  - 想关掉：`disableBundledSkills` 设置

### 2. 两种内容类型（这是设计 skill 的第一决策）

| 类型 | 是什么 | 怎么用 | 例子 |
|------|--------|--------|------|
| **参考内容（Reference）** | 知识：约定、模式、风格指南、领域知识 | **内联**加载，和当前对话一起用 | API 设计规范、本项目命名约定 |
| **任务内容（Task）** | 分步操作：部署、提交、代码生成 | 通常你**直接用 `/name` 触发**，不想让 Claude 自己挑时机 → 加 `disable-model-invocation: true` | `/deploy` 跑部署清单 |

> ⚠️ 正文要**短**。因为**skill 一旦加载，内容会在后续每轮都留在上下文里**——每一行都是持续的 token 成本。原则：**写"做什么"，不要叙述"怎么做/为什么"**（跟写 CLAUDE.md 一个标准）。

### 3. Frontmatter 速查

```yaml
---
name: my-skill
description: 这个 skill 做什么、什么时候用
when_to_use: 补充触发场景（触发词、示例请求）
disable-model-invocation: true    # 禁止模型自动加载，只能手动 /name
user-invocable: false             # 反过来：只允许模型调，人看不到
allowed-tools: Read Grep          # 当轮免审批
disallowed-tools: AskUserQuestion # 当轮从池子里移除
model: sonnet                     # 当轮换模型（下条消息恢复）
context: fork                     # 放到隔离子 agent 里跑
agent: code-reviewer              # 配 context: fork 用的 agent 类型
background: false                 # fork 时改为"等结果"
arguments: [issue-number]         # 命名位置参数
---
```

| 字段 | 关键点 |
|------|--------|
| `description` | **Claude 靠它决定何时用**。把最关键的用例放最前；`description` + `when_to_use` 在清单里会被**截断到 1,536 字符**（省上下文）|
| `disable-model-invocation` | 禁止模型自动加载（也不允许被预加载进 subagent；v2.1.196 起也不会被定时任务触发）|
| `user-invocable` | `false` = 只有模型能用，`/` 菜单里隐藏 |
| `allowed-tools` | **当轮**免审批，**你发下一条消息就失效**（内容留在上下文，权限不留）|
| `disallowed-tools` | 当轮从可用池移除（比如后台循环里禁掉 `AskUserQuestion`）|
| `model` | 当轮生效，不写进设置 |

> 🔒 **安全提醒（官方专门警告）**：`allowed-tools` **不受工作区信任（workspace trust）约束**——项目 skill 的 `allowed-tools` 在你或 Claude 调用它时一律生效，**哪怕是在你从未信任过的目录里跑 `-p`**。所以**签出别人的仓库、跑 Claude Code 之前，先看看里面的 skill 给了自己什么工具权限。**

### 4. ⭐ Skill 内容生命周期（最容易被忽略的机制）

| 阶段 | 行为 |
|------|------|
| **加载** | 渲染后的 `SKILL.md` 作为**一条消息**进入对话，**并留在后续所有轮次** |
| **重复调用** | 若渲染内容与已加载的**完全一致** → 只加一句"已加载"的提示，**不再塞一份**；若因参数变化/动态上下文产生**不同**内容 → **再追加全文** |
| **自动压缩（auto-compaction）后** | Claude Code 把**每个 skill 最近一次调用**重新挂到摘要之后，**各保留前 5,000 token**；这些重挂的 skill **共享 25,000 token 预算**，**从最近调用的开始填**——所以一次会话里调用过很多 skill，老的**可能被整个丢弃** |

> 💡 这条有三层实操含义：
> 1. **别把 skill 写成"一次性步骤"，要写成贯穿任务始终的定语**——因为它不会在后续轮次被重读
> 2. **skill 似乎"失效"了？** 通常内容还在，只是模型选了别的工具 → 去**强化 description 和指令**，或者干脆**用 hook 做确定性强制**
> 3. **skill 很大、或者你之后又调用了好几个** → **压缩之后重新调用一次**，把全文恢复回来

### 5. Skill ↔ Subagent 的两种组合方式（很实用）

| 方式 | 系统提示词来自 | 任务来自 | 还会加载 |
|------|--------------|---------|---------|
| **Skill 加 `context: fork`** | agent 类型 | **SKILL.md 内容** | CLAUDE.md（按该 agent 的启动上下文）|
| **Subagent 加 `skills` 字段** | subagent 的 md 正文 | **Claude 的委派消息** | 预加载的 skill 全文 + CLAUDE.md |

**`context: fork` 的细节：**

- Claude Code 会按 `agent` 字段指定类型**新起一个 subagent**，把 skill 内容当它的提示词
- ⚠️ **它看不到你的对话历史**，所以 skill 指令必须**自洽**（别依赖上文）
- ⚠️ **名字骗人**：`context: fork` **≠** 前文的"对话 fork"（后者会把全部历史交给 subagent）。**任务依赖对话历史时，要 fork 对话，而不是用 `context: fork`。**
- 默认**后台跑**（结果好了再回来）；`background: false` 改成当轮等结果
- 这几种情况会强制等：`-p` / Agent SDK 非交互、`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`、同一 skill 上一次还在跑、定时任务触发
- ⚠️ 后台 fork 的编辑**在会话 checkpoint 之外**，`/rewind` 撤不掉，得用 git
- ⚠️ **`context: fork` 只适合"有明确指令"的 skill**。纯参考型（"用这些 API 约定"）会被投进去但没任务可做，**空跑回来**。

> 记住这张双向表：**"任务写在 skill 里、让人挑执行者" vs "人把任务交出去、给 subagent 预装知识"。**

---

## 五、选型：Skill / Subagent / CLAUDE.md / Hook 到底怎么选

官方给的对照（浓缩版）：

| 维度 | **Skill** | **Subagent** |
|------|-----------|--------------|
| 是什么 | 可复用的指令/知识/流程 | 有自己上下文的隔离工人 |
| 核心好处 | 内容跨上下文复用 | **上下文隔离**，只回摘要 |
| 上下文影响 | **加进你的主窗口** | **用独立窗口**，自己的输入输出 token |
| 最适合 | 参考资料、可调用流程 | 读很多文件的任务、并行、专精工人 |

| 维度 | **CLAUDE.md** | **Skill** |
|------|--------------|-----------|
| 加载 | **每会话自动** | **按需** |
| 触发流程 | ❌ | ✅ `/name` |
| 最适合 | "永远要遵守 X" | 参考资料、可触发流程 |

**判断口诀：**

- **"永远要知道"** → CLAUDE.md（保持 < 200 行）
- **"有时候需要"的参考资料 / 想用 `/name` 触发的流程** → Skill
- **"要读一堆文件但只想要结论" / 想并行 / 想限定工具** → Subagent
- **"必须确定性发生"（不靠模型自觉）** → Hook（第四、五章的结论）

> 📌 三层叙事线收束一下就清楚了：
> **CLAUDE.md 是订阅制（每轮付）、Skill 是按次付费（用到才付）、Subagent 是独立核算（别人付）、Hook 是免费外包（机器付）。**

---

## 六、与前五章的串联

| 学过的概念 | 这一章的体现 |
|-----------|-------------|
| **Agent Loop（TAO）** | Subagent 就是**"再来一个 Loop"**——拥有自己完整的 TAO 循环，只是消息不外溢。**Agent 套 Agent 的结构性起点。** |
| **工具调用（提议→权限→执行→回灌）** | 委派靠 **`Agent` 工具**；`description` 就是该工具的 **description**（决定"模型什么时候调用它"）→ 和第三章"工具的 description 决定调用时机"是同一个机制，只是作用对象是 subagent |
| **三层权限隔离** | Subagent 把三层**打包带走**：`tools`/`disallowedTools`（能力边界）+ `permissionMode`（确认策略）+ 后台 subagent 的权限提示回弹到主会话 |
| **第四章 Hooks** | Hooks 是**零上下文成本**的扩展（跑在外部）；对照 Skill/Subagent/CLAUDE.md 的各自成本模型，**"扩展体系 = 一套上下文预算分配方案"** |
| **第五章 TodoWrite** | TodoWrite 是"**Agent 管自己**"；Subagent 是"**Agent 管 Agent**"。第五章那条"工具价值 = 增益 − 上下文成本"，在这一章扩展成了整张特征成本表 |
| **hello-agents 第六/七章** | 我们学的 AutoGen/AgentScope/LangGraph 是**多 Agent 框架**；Claude Code 的 Subagent 是**产品化的最小多 Agent 单元**：隔离上下文 + 委派消息 + 摘要回传 + Resume。**"多智能体"不是玄学，就是"再起一个循环 + 一条消息通道"。** |
| **hello-agents 第八章（记忆与检索）** | Skill 的"描述常驻 + 正文按需"= **典型的检索式加载（lazy retrieval）**；Subagent 的"启动时只带必要上下文"= **上下文工程里的"最小必要集"** |

### 💡 最大认知升级

**扩展 Agent 的本质工作，是"上下文预算分配"。**

- 每个功能都在问同一件事：**这份信息该什么时候进谁的上下文、付多少 token？**
  - 常驻（CLAUDE.md）→ 每轮付
  - 按需（Skill）→ 用到才付
  - 隔离（Subagent）→ 别人付，只要摘要
  - 外部（Hook）→ 机器付，零成本
- 所以"该用哪个功能"从来不是功能清单问题，而是**成本与收益的分配问题**

一句话：**第五章我们学会让 Agent 管理自己（TodoWrite）；这一章我们学会管理 Agent 的上下文（Subagent / Skill）。当 Agent 能自我管理、又能被组织化，它才真的从"能干活的程序"变成"能长期协作的系统"。**

---

## 七、待补 / 后续

- [ ] 动手：写一个只读的 `code-reviewer` subagent（`~/.claude/agents/`），用 `@agent-` 提及强制触发一次
- [ ] 动手：写一个 `context: fork` 的 `/deploy` skill，对比"内联 skill"与"fork skill"的上下文差异（用 `/context` 看）
- [ ] 试 `CLAUDE_CODE_SUBAGENT_MODEL` / `--agent` / `settings.json` 的 `agent` 字段，搞清模型继承顺序
- [ ] 读官方《Extend Claude Code》姊妹页：agent-teams（团队协作）、dynamic workflows（脚本编排大量 subagent）、worktrees（并行隔离）、cross-session messaging
- [ ] 后续章节：MCP 集成 / 记忆与上下文管理 / 多 Agent 协作

---

> 📎 参考：Claude Code 官方文档 —— Create custom subagents、Extend Claude with skills、Extend Claude Code（features overview）、Subagents in the SDK
