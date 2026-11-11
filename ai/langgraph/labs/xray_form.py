"""控制变量：函数体里都有字面 .invoke(，只改表达式形态，看 xray 是否变化"""
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from typing import Annotated

class SU(TypedDict):
    messages: Annotated[list, add_messages]
def reply(s): return {"messages": [AIMessage(content="R" + str(len(s["messages"])))]}
sb = StateGraph(SU); sb.add_node("reply", reply); sb.add_edge(START,"reply"); sb.add_edge("reply",END)
SUB = sb.compile()

class P(TypedDict):
    messages: Annotated[list, add_messages]

# ① 原文「错误」写法：一行链式
def form1(s):
    return {"messages": [AIMessage(content=SUB.invoke({"messages": s["messages"]})["messages"][-1].content)]}

# ② 原文「推荐」写法：拆两句
def form2(s):
    resp = SUB.invoke({"messages": s["messages"]})
    return {"messages": [AIMessage(content=resp["messages"][-1].content)]}

# ③ 更极端的链式：连 return 都写在同一个表达式里
def form3(s):
    return {"messages": [AIMessage(content=SUB.invoke({"messages": s["messages"]})["messages"][-1].content + "!")]}

# ④ 分两句但多一层中间变量
def form4(s):
    a = SUB.invoke({"messages": s["messages"]})
    b = a["messages"][-1]
    return {"messages": [AIMessage(content=b.content)]}

for label, fn in [("① 单行链式", form1), ("② 拆两句(推荐)", form2),
                  ("③ 单行更深链式", form3), ("④ 拆多句", form4)]:
    b = StateGraph(P); b.add_node("chat", fn)
    b.add_edge(START,"chat"); b.add_edge("chat",END)
    g = b.compile(checkpointer=InMemorySaver())
    xr = [n for n in g.get_graph(xray=1).nodes if "reply" in n]
    out = g.invoke({"messages": [HumanMessage(content="q")]}, {"configurable": {"thread_id": label}})
    print(f"{label:18} xray展开={bool(xr)}  回复={out['messages'][-1].content}")
