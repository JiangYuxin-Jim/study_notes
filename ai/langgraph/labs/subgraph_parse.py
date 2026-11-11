"""
验证：子图调用「链式 vs 赋值再取」是否影响 LangGraph 的图结构解析
环境：langgraph 1.2.16
"""
import operator
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# ============ 子图 ============
class SubState(TypedDict):
    raw_text: str
    processed: str

def sub_step1(s: SubState):
    return {"processed": s["raw_text"].upper()}

def sub_step2(s: SubState):
    return {"processed": s["processed"] + "_END"}

sub_builder = StateGraph(SubState)
sub_builder.add_node("sub_step1", sub_step1)
sub_builder.add_node("sub_step2", sub_step2)
sub_builder.add_edge(START, "sub_step1")
sub_builder.add_edge("sub_step1", "sub_step2")
sub_builder.add_edge("sub_step2", END)
subgraph = sub_builder.compile()

# ============ 父图 A：正确写法（赋值再取）============
class ParentState(TypedDict):
    raw_text: str
    result: str

def parent_chained(s: ParentState):
    # ❌ 链式调用：一行里 invoke 完直接索引
    return {"result": subgraph.invoke({"raw_text": s["raw_text"]})["processed"]}

def parent_assigned(s: ParentState):
    # ✅ 先赋值，再取
    res = subgraph.invoke({"raw_text": s["raw_text"]})
    return {"result": res["processed"]}

# ============ 建两张父图对照 ============
def build(node_fn, name):
    b = StateGraph(ParentState)
    b.add_node(name, node_fn)
    b.add_edge(START, name)
    b.add_edge(name, END)
    return b.compile(checkpointer=InMemorySaver())

g_chained = build(parent_chained, "parent")
g_assigned = build(parent_assigned, "parent")

print("=" * 70)
print("【1】用 get_graph() 看父图的节点结构")
for label, g in [("链式 ❌", g_chained), ("赋值 ✅", g_assigned)]:
    graph = g.get_graph()
    nodes = [n for n in graph.nodes]
    print(f"  {label}: nodes = {nodes}")

print()
print("=" * 70)
print("【2】draw_mermaid() 是否包含子图内容")
for label, g in [("链式 ❌", g_chained), ("赋值 ✅", g_assigned)]:
    mermaid = g.get_graph().draw_mermaid()
    has_sub = ("sub_step1" in mermaid) or ("sub_step2" in mermaid)
    print(f"  {label}: mermaid 里出现子图节点? {has_sub}")

print()
print("=" * 70)
print("【3】实际运行结果是否一致")
cfg_c = {"configurable": {"thread_id": "c1"}}
cfg_a = {"configurable": {"thread_id": "a1"}}
r1 = g_chained.invoke({"raw_text": "hello"}, cfg_c)
r2 = g_assigned.invoke({"raw_text": "hello"}, cfg_a)
print(f"  链式结果: {r1}")
print(f"  赋值结果: {r2}")
print(f"  结果一致? {r1['result'] == r2['result']}")

print()
print("=" * 70)
print("【4】checkpoint 里能不能看到子图的快照")
for label, g, cfg in [("链式 ❌", g_chained, cfg_c), ("赋值 ✅", g_assigned, cfg_a)]:
    hist = list(g.get_state_history(cfg))
    print(f"  {label}: checkpoint 数量 = {len(hist)}")
    ns_list = [h.config.get("configurable", {}).get("checkpoint_ns", "") for h in hist]
    has_child_ns = any("sub" in ns for ns in ns_list)
    print(f"    checkpoint_ns 列表 = {ns_list}")
    print(f"    含子图命名空间? {has_child_ns}")
