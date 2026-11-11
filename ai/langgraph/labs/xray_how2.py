"""xray 靠什么发现子图？—— 关键对照：函数里「有 invoke 调用」vs「没有」"""
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class S(TypedDict):
    x: str

def s1(s): return {"x": s["x"] + "1"}
def s2(s): return {"x": s["x"] + "2"}

def mk():
    sb = StateGraph(S)
    sb.add_node("sg_step1", s1); sb.add_node("sg_step2", s2)
    sb.add_edge(START, "sg_step1"); sb.add_edge("sg_step1", "sg_step2"); sb.add_edge("sg_step2", END)
    return sb.compile()

SUB = mk()

class P(TypedDict):
    x: str

# A: 函数体里出现了 .invoke( —— 静态可见
def has_invoke(s):
    r = SUB.invoke({"x": s["x"]})
    return {"x": r["x"]}

# B: 函数体里【没有】.invoke( 字样，但运行时仍会去调子图（通过闭包 & 别名字典）
_ALIAS = {"g": SUB}
def no_invoke_text(s):
    g = _ALIAS["g"]
    # 用 __getattribute__ 绕开字面量 "invoke"
    r = g.__getattribute__("invoke")({"x": s["x"]})
    return {"x": r["x"]}

# C: 压根不调用子图
def no_sub(s):
    return {"x": s["x"] + "_plain"}

for label, fn in [("A 有字面 .invoke( ✅", has_invoke),
                  ("B 无字面 invoke，运行时才调", no_invoke_text),
                  ("C 完全不调子图", no_sub)]:
    b = StateGraph(P); b.add_node("n", fn)
    b.add_edge(START, "n"); b.add_edge("n", END)
    g = b.compile(checkpointer=InMemorySaver())
    before = [n for n in g.get_graph(xray=1).nodes if "sg_step" in n]
    out = g.invoke({"x": "v"}, {"configurable": {"thread_id": label}})
    after = [n for n in g.get_graph(xray=1).nodes if "sg_step" in n]
    print(f"{label:32} xray展开={bool(before)}  结果={out['x']}")
