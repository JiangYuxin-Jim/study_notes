"""
验证：子图的结构解析 —— 对比三种接入方式
A) 节点函数里调用 subgraph.invoke()（链式 / 赋值两种写法）
B) add_node("x", subgraph) 把编译好的图当节点
"""
import operator
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class SubState(TypedDict):
    raw_text: str
    processed: str

def sub_step1(s): return {"processed": s["raw_text"].upper()}
def sub_step2(s): return {"processed": s["processed"] + "_END"}

sb = StateGraph(SubState)
sb.add_node("sub_step1", sub_step1)
sb.add_node("sub_step2", sub_step2)
sb.add_edge(START, "sub_step1")
sb.add_edge("sub_step1", "sub_step2")
sb.add_edge("sub_step2", END)
subgraph = sb.compile()

class ParentState(TypedDict):
    raw_text: str
    result: str

def parent_chained(s):
    return {"result": subgraph.invoke({"raw_text": s["raw_text"]})["processed"]}

def parent_assigned(s):
    res = subgraph.invoke({"raw_text": s["raw_text"]})
    return {"result": res["processed"]}

def build(node_fn, name, cp=True):
    b = StateGraph(ParentState)
    b.add_node(name, node_fn)
    b.add_edge(START, name)
    b.add_edge(name, END)
    return b.compile(checkpointer=InMemorySaver() if cp else None)

g_chained = build(parent_chained, "parent")
g_assigned = build(parent_assigned, "parent")

# B) 把子图直接当节点注册
b_node = StateGraph(ParentState)
b_node.add_node("sub", subgraph)
b_node.add_edge(START, "sub")
b_node.add_edge("sub", END)
g_asis = b_node.compile(checkpointer=InMemorySaver())

print("=" * 72)
print("A. 节点函数内 invoke 子图 —— 链式 vs 赋值")
for label, g in [("链式 ❌", g_chained), ("赋值 ✅", g_assigned)]:
    m = g.get_graph().draw_mermaid()
    print(f"  {label}: 拓扑里含 sub_step → {'sub_step' in m}")
    print(f"           nodes = {list(g.get_graph().nodes)}")

print()
print("B. 子图直接当节点 add_node('sub', subgraph)")
m = g_asis.get_graph().draw_mermaid()
print(f"  拓扑里含 sub_step → {'sub_step' in m}")
print(f"  nodes = {list(g_asis.get_graph().nodes)}")
print()
print("  渲染片段（含子图的部分）：")
for ln in m.split("\n"):
    if "sub" in ln.lower():
        print("   ", ln)
