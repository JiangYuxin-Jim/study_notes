"""
验证：【4-b】父图 compile 时传 checkpointer，子图不传 —— 是否能自动继承？
以及 add_node(subgraph) 方式下的 ns 归属
"""
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class SubState(TypedDict):
    raw_text: str
    processed: str

def sub_step1(s): return {"processed": s["raw_text"].upper()}
def sub_step2(s): return {"processed": s["processed"] + "_END"}

class ParentState(TypedDict):
    raw_text: str
    result: str

sb = StateGraph(SubState)
sb.add_node("sub_step1", sub_step1)
sb.add_node("sub_step2", sub_step2)
sb.add_edge(START, "sub_step1")
sb.add_edge("sub_step1", "sub_step2")
sb.add_edge("sub_step2", END)
subgraph = sb.compile()            # ← 子图不挂 checkpointer

saver = InMemorySaver()

def parent_fn(s):
    return {"result": subgraph.invoke({"raw_text": s["raw_text"]})["processed"]}

b = StateGraph(ParentState)
b.add_node("parent", parent_fn)
b.add_edge(START, "parent"); b.add_edge("parent", END)
g = b.compile(checkpointer=saver)

cfg = {"configurable": {"thread_id": "t2"}}
print("invoke:", g.invoke({"raw_text": "hi"}, cfg))
hist = list(g.get_state_history(cfg))
nss = [h.config.get("configurable", {}).get("checkpoint_ns", "") for h in hist]
print("父图 ns 列表:", nss)

print()
print("=" * 72)
print("【4-c】add_node(subgraph) 方式 —— 子图 checkpoint 归属")
saver2 = InMemorySaver()
b2 = StateGraph(ParentState)
b2.add_node("sub", subgraph)
b2.add_edge(START, "sub"); b2.add_edge("sub", END)
g2 = b2.compile(checkpointer=saver2)
cfg2 = {"configurable": {"thread_id": "t3"}}
print("invoke:", g2.invoke({"raw_text": "hi"}, cfg2))
h2 = list(g2.get_state_history(cfg2))
print("父图 ns 列表:", [h.config.get("configurable", {}).get("checkpoint_ns", "") for h in h2])
print("checkpoint 数:", len(h2))
