# LangGraph（九）Subgraph 子图：两种接入方式与「静态发现」的真实边界

> 学习日期：2026-11-11
> 环境：本机 `langgraph 1.2.16`，下述**五组实验全部实跑**，输出原样贴出
> 承接：[（八）中断 · 工具节点 · 流式执行](./langgraph-08-中断-工具节点-流式执行.md)（那里留了个尾巴：父图/子图各自的中断归谁）
> 一句话：**子图有两种接入方式 —— 注册成节点（图能看见）vs 函数里 invoke（图看不见）。所有"看不见"的问题都源于接入方式，不源于你代码怎么排版。**

---

## 〇、先破除一个流传很广的误判

网上（包括一些教程）会说：**调用子图时不要写成链式，否则 LangGraph 解析失败、感知不到子图。**

原话大概是这样：

```python
# ❌ "错误"写法
assistant_response = subgraph.invoke({"messages": messages})["messages"][-1].content

# ✅ "正确"写法
subgraph_response = subgraph.invoke({"messages": messages})
assistant_response = subgraph_response["messages"][-1].content
```

**结论：这个建议本身是对的（实践上应该这么写），但归因是错的。**

它不是因为"链式调用"导致 LangGraph 解析失败。真正的机制是 **Subgraph Discovery（子图静态发现）的限制**，而限制的触发条件跟你怎么排版**没有关系**。

下面用**控制变量实验**把它拆干净。

> ⚠️ 术语澄清：本文说的"链式"指 **`invoke(...)[...]` 这种调用后立即下标的表达式嵌套**，
> 和 LangChain 的 **LCEL 管道操作符**（`prompt | model | parser`）完全是两回事。两者不要混为一谈。

---

## 一、子图的两种接入方式（这才是分水岭）

### 方式一：把编译好的图注册为父图节点 ⭐ 首选

```python
builder.add_node("sub", subgraph)
```

- LangGraph **明确知道**这个节点就是一个子图，不需要任何推断
- `get_graph(xray=True)` 能展开完整拓扑
- 子图的 checkpoint 归属清晰
- **适合父子 state 结构一致（共享字段）的场景**

### 方式二：在普通节点函数内部 `invoke` 子图

```python
def parent_node(state):
    subgraph_response = subgraph.invoke({"messages": state["messages"]})
    return {"response": subgraph_response["messages"][-1].content}

builder.add_node("parent_node", parent_node)
```

- 父图只看到一个**黑盒节点**
- 图拓扑里没有子图内容（默认渲染就是这样）
- **适合父子 state 结构不同、需要手动转换输入输出的场景**

**这是真正的分水岭。** 方式二天然"看不见"子图，跟你怎么写表达式无关。

---

## 二、实验一：纯粹改表达式形态，xray 展开有没有变化？

四个节点函数，**函数体里全都有字面 `SUB.invoke(`**，只有表达式形态不同：

```python
# ① 单行嵌套（"错误"写法）
def form1(s):
    return {"messages": [AIMessage(content=SUB.invoke({"messages": s["messages"]})["messages"][-1].content)]}

# ② 拆两句（"推荐"写法）
def form2(s):
    resp = SUB.invoke({"messages": s["messages"]})
    return {"messages": [AIMessage(content=resp["messages"][-1].content)]}

# ③ 单行更深嵌套（末尾再加 "!"）
def form3(s):
    return {"messages": [AIMessage(content=SUB.invoke({"messages": s["messages"]})["messages"][-1].content + "!")]}

# ④ 拆多句
def form4(s):
    a = SUB.invoke({"messages": s["messages"]})
    b = a["messages"][-1]
    return {"messages": [AIMessage(content=b.content)]}
```

实测：

```
① 单行链式        xray展开=True  回复=R1
② 拆两句(推荐)     xray展开=True  回复=R1
③ 单行更深链式     xray展开=True  回复=R1!
④ 拆多句          xray展开=True  回复=R1
```

**四种写法 xray 全部能展开。**

> ✅ 结论 1：**表示形态（链式 vs 拆分）对子图发现没有任何影响。**

---

## 三、实验二：改「变量怎么指到子图」，才有差异

三个节点函数，**全部写成规范的"先赋值再取"**，只有变量来源不同：

```python
# A：函数体里字面写 SUB.invoke(...)
def has_invoke(s):
    r = SUB.invoke({"x": s["x"]})
    return {"x": r["x"]}

# B：变量从字典取，且用 __getattribute__ 绕开字面量 "invoke"
_ALIAS = {"g": SUB}
def no_invoke_text(s):
    g = _ALIAS["g"]
    r = g.__getattribute__("invoke")({"x": s["x"]})
    return {"x": r["x"]}

# C：压根不调子图
def no_sub(s):
    return {"x": s["x"] + "_plain"}
```

实测：

```
A 有字面 .invoke( ✅              xray展开=True   结果=v12
B 无字面 invoke，运行时才调         xray展开=False  结果=v12
C 完全不调子图                    xray展开=False  结果=v_plain
```

**A 和 B 的运行结果完全一样（都是 `v12`），但 A 能展开、B 不能。**

> ✅ 结论 2：差异来自 **子图那个变量在别处被 `.invoke` 过** —— 这是**静态分析**在做**变量名绑定**，不是运行时记录。
> 变量怎么来的（直接名 / 字典取 / `getattr`）决定了静态分析看不看得见。

---

## 四、实验三：静态绑定是「编译期单值」的

同一个节点函数，**运行时**根据 state 决定调哪个子图：

```python
SUB_ALPHA = mk_sub("alpha")   # 节点名 alpha_step1 / alpha_step2
SUB_BETA  = mk_sub("beta")    # 节点名 beta_step1  / beta_step2

def switcher(s):
    g = SUB_ALPHA if s["flag"] else SUB_BETA
    r = g.invoke({"x": s["x"]})
    return {"x": r["x"]}
```

实测：

```
运行前 xray nodes: ['__start__', '__end__', 'sw:alpha_step1', 'sw:alpha_step2']

flag=True  结果=alphaB  之后 xray nodes: ['__start__','__end__','sw:alpha_step1','sw:alpha_step2']
flag=False 结果=betaB   之后 xray nodes: ['__start__','__end__','sw:alpha_step1','sw:alpha_step2']
```

**`flag=False` 实际跑的是 beta，但图里显示的仍然是 alpha 的拓扑。**

> ✅ 结论 3：静态发现给 `g` 只绑定**一个**子图（这里是 alpha）。运行时切成 beta 也不会更新。
> 这就是为什么材料里说"动态创建子图、间接调用、复杂封装时限制更明显"。

---

## 五、实验四：`xray=True` 是查看子图拓扑的唯一开关

方式一（注册成节点）下，两种渲染对照：

```python
b.add_node("sub", subgraph)
g = b.compile(checkpointer=saver)

g.get_graph()            # 黑盒
g.get_graph(xray=1)      # 展开
```

`get_graph()` 默认输出：

```
graph TD;
	__start__ --> sub;
	sub --> __end__;
```

`get_graph(xray=1)` 输出：

```
graph TD;
	__start__ --> sub\3asub_step1;
	sub\3asub_step2 --> __end__;
	subgraph sub
	sub\3asub_step1(sub_step1)
	sub\3asub_step2(sub_step2)
	sub\3asub_step1 --> sub\3asub_step2;
	end
```

节点集合对照：

```
get_graph()        nodes = ['__start__', 'sub', '__end__']
get_graph(xray=1)  nodes = ['__start__', '__end__', 'sub:sub_step1', 'sub:sub_step2']
```

> ✅ 结论 4：**看不到子图拓扑，第一件事先检查有没有加 `xray=True`**，别急着改代码。

---

## 六、实验五：三件事必须分开 —— 拓扑 / 保存 / 查询

材料里特别强调的那一点，我实测确认了它是对的：

> 「无法发现子图」≠「子图没有保存 checkpoint」

实测（方式二，子图不独立持 saver）：

```
父图 checkpoint 总数 = 3
父图 ns 列表 = ['', '', '']        ← 没有子图命名空间
子图自身 get_state_history = []    ← 子图自己那里也没有历史
```

再看方式二 + **子图独立持 saver** 的情况：

```
父图 ns: ['', '', '']
子图自己的历史条数: 3              ← 子图有完整历史，只是归它自己
```

| 关注点 | 取决于什么 | 与子图"被父图发现"的关系 |
|---|---|---|
| **拓扑可视化** | 接入方式 + `xray=True` | 直接相关 |
| **子图 checkpoint 是否保存** | 执行是否真的发生 + 子图自己有没有挂 saver | **无关** |
| **能否用父图查子图状态** | `get_state(cfg, subgraphs=True)` + 子图发现机制 | 部分相关 |

> ✅ 结论 5：**"父图看不见子图" 只说明拓扑不可视，不说明子图没跑、也没说明没存快照。**

---

## 七、父子 state 结构不同时怎么写（方式二的正经用法）

```python
class ParentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    draft: str          # ← 父图多出来的字段

class SubState(TypedDict):
    messages: Annotated[list, add_messages]      # ← 子图只要 messages

def call_sub(s):
    r = SUB.invoke({"messages": s["messages"]})   # 只挑需要的字段进去
    return {"draft": r["messages"][-1].content}   # 只取需要的字段出来

b.add_node("call_sub", call_sub)
```

实测：

```
父 state 结果 keys: ['messages', 'user_name', 'draft']
draft = 子图看到 1 条消息
子图没有反过来污染父 state: True
```

**关键点：进子图时手动挑字段，出子图时手动挑字段。** 父子 state 不共享，中间这一层转换就是方式二存在的理由。

---

## 八、那到底该怎么写？—— 实践建议 + 真实理由

```python
# ✅ 推荐
subgraph_response = subgraph.invoke(inputs)
result = subgraph_response["messages"][-1].content
```

**推荐它的真实理由是"工程可维护性"，不是"LangGraph 才能解析"：**

1. **断点调试**：能在 `subgraph_response` 上停住，直接看子图返回的全貌
2. **异常处理**：能单独 `try/except` 包住子图调用，不让异常吞掉父节点的返回值
3. **日志/校验**：能先打日志、先验字段再取下标，避免 `KeyError` / `IndexError` 混在深层表达式里
4. **报错堆栈干净**：一行嵌套里出错的栈会把 invoke 与下标访问混在一起

> 就算 LangGraph 完全不需要这点，这四条也足够支撑你写成两步。

**而如果想让图能看见子图，唯一的办法是换接入方式：**

```python
builder.add_node("sub", subgraph)     # 而不是 lambda s: subgraph.invoke(s)
```

---

## 九、踩坑清单

| # | 坑 | 现象 | 解法 |
|---|---|---|---|
| 1 | 以为"链式写法"导致子图丢失 | 改了写法 xray 照样展不开 | 检查是不是**方式二**接入（函数内 invoke） |
| 2 | 忘了 `xray=True` | 方式一也看不到子图 | `get_graph(xray=1)` |
| 3 | 运行时动态选子图 | 图里只显示其中一路拓扑 | 静态图不反映运行时分支，接受或拆成多个节点 |
| 4 | 子图变量通过字典/`getattr` 间接取得 | 静态发现失败 | 子图用**模块级常量名**直接引用 |
| 5 | 认为"图看不见 = 没存 checkpoint" | 误删 saver 配置 | 拓扑/保存/查询是三件事，分开排查 |
| 6 | 父子 state 不同还硬用方式一 | 字段错位或 KeyError | 方式二 + 手动转换 |
| 7 | 方式二下想查子图 checkpoint | 父图 `ns` 全空 | 子图编译时独立挂 saver，用它自己的 config 查 |
| 8 | 把 LCEL 管道当成本文的"链式" | 概念混淆 | `prompt \| model \| parser` 是运算符重载，与下标访问无关 |

---

## 十、和前面章节的连线

- **（五）持久化**：`checkpoint_ns` 是子图命名空间 —— 那里说"不能当业务隔离"，这里补上了"什么时候才会有 ns"
- **（八）中断**：父图/子图中断 id 归属问题，根源就在于**子图是不是被注册成节点**（方式一能拿到，方式二拿不到）
- **（三）静态扇入**：那里"图的画法相同必须看代码"，这里"图的画法不同可能只是没加 xray" —— 同一个教训的两面
- **LangChain（四）Agent**：`create_agent` 内部就是一个编译好的子图，被当节点注册
- **learn Claude Code 第六章 Subagent**：Claude Code 的 subagent 是"黑盒 + 只回摘要"，正是**方式二**的语义

---

## 十一、下一步

- **方式一下的中断**：父图 resume 与子图 resume 的 id 归属实测
- **`Command(goto=[...])` 节点内静态并行分派**
- **手搓 ReAct 图**对照 `create_agent`，把子图 + 中断 + 流式全接上
- LangChain RAG 线：Embeddings → VectorStore → Retriever

---

## 附录：实验脚本

| 脚本 | 验证内容 |
|---|---|
| `subgraph_parse.py` | 链式/赋值 的结果一致性、默认图、ns |
| `subgraph_parse2.py` | 方式一 vs 方式二 的拓扑对照 |
| `subgraph_parse4.py` | 父子 saver 独立 / xray 展开 |
| `subgraph_parse5.py` | AST 层面：字面 invoke 调用 vs 独立赋值语句 |
| `xray_form.py` | ⭐ 实验一：四种表达式形态，xray 全 True |
| `xray_how2.py` | ⭐ 实验二：字面 invoke vs 间接取用，结果同拓扑不同 |
| `xray_how.py` | ⭐ 实验三：运行时切换子图，静态绑定只认一个 |
| `sub_more.py` | 父子 state 不同时的手动转换 + 子图独立 saver |
