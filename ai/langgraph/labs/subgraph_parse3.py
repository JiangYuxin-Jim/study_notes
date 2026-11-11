"""
验证：【4】子图 checkpoint 快照是否需要独立 checkpointer
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

def make_sub(cp=None):
    sb = StateGraph(SubState)
    sb.add_node("sub_step1", sub_step1)
    sb.add_node("sub_step2", sub_step2)
    sb.add_edge(START, "sub_step1")
    sb.add_edge("sub_step1", "sub_step2")
    sb.add_edge("sub_step2", END)
    return sb.compile(checkpointer=cp)

def probe(label, g, cfg):
    hist = list(g.get_state_history(cfg))
    nss = [h.config.get("configurable", {}).get("checkpoint_ns", "") for h in hist]
    child = [n for n in nss if n]
    print(f"  {label}")
    print(f"    checkpoint 总数 = {len(hist)}")
    print(f"    ns 列表 = {nss}")
    print(f"    含子图 ns({len(child)}) ? {bool(child)}")

print("=" * 72)
print("【1】子图 & 父图 各自独立 InMemorySaver")
sub_a = make_sub(InMemorySaver())
b = StateGraph(ParentState)
b.add_node("parent", lambda s: {"result": sub_a.invoke({"raw_text": s["raw_text"]})["processed"]})
b.add_edge(START, "parent"); b.add_edge("parent", END)
g_a = b.compile(checkpointer=InMemorySaver())
cfg = {"configurable": {"thread_id": "t1"}}
print("  invoke:", g_a.invoke({"raw_text": "hi"}, cfg))
probe("父图 history:", g_a, cfg)
print("  子图自身 history:", list(sub_a.get_state_history({"configurable": {"thread_id": "t1"}})))
