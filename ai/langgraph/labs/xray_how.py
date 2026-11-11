"""xray 展开到底靠什么？—— 用「同一个函数对象被两个节点共用」「运行时才决定调用哪个子图」来拆解"""
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

def mk_sub(pfx):
    class S(TypedDict):
        x: str
    def a(s): return {"x": pfx + "A"}
    def b(s): return {"x": pfx + "B"}
    sb = StateGraph(S)
    sb.add_node(pfx + "_step1", a); sb.add_node(pfx + "_step2", b)
    sb.add_edge(START, pfx + "_step1"); sb.add_edge(pfx + "_step1", pfx + "_step2"); sb.add_edge(pfx + "_step2", END)
    return sb.compile()

SUB_ALPHA = mk_sub("alpha")
SUB_BETA  = mk_sub("beta")

class P(TypedDict):
    x: str
    flag: bool

# 同一个节点函数，运行时根据 state 决定调哪个子图 —— 静态分析注定只能看到一个或都不确定
def switcher(s):
    g = SUB_ALPHA if s["flag"] else SUB_BETA
    r = g.invoke({"x": s["x"]})
    return {"x": r["x"]}

b = StateGraph(P)
b.add_node("sw", switcher)
b.add_edge(START, "sw"); b.add_edge("sw", END)
g = b.compile(checkpointer=InMemorySaver())

print("运行前 xray nodes:", [n for n in g.get_graph(xray=1).nodes])
print()
for flag in [True, False]:
    cfg = {"configurable": {"thread_id": f"t{flag}"}}
    out = g.invoke({"x": "v", "flag": flag}, cfg)
    print(f"flag={flag} 结果={out['x']}  之后 xray nodes:", [n for n in g.get_graph(xray=1).nodes])
