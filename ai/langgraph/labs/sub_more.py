"""补充实验：父子状态不同时的三种转换写法 + 子图 checkpoint 独立性"""
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage

# ===== 父 state 有 user_name/session_id，子 state 只要 messages =====
class ParentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    draft: str

class SubState(TypedDict):
    messages: Annotated[list, add_messages]

def sub_reply(s):
    return {"messages": [AIMessage(content=f"子图看到 {len(s['messages'])} 条消息")]}

sb = StateGraph(SubState)
sb.add_node("reply", sub_reply)
sb.add_edge(START, "reply"); sb.add_edge("reply", END)
SUB = sb.compile()

# 父子 state 不同 → 必须手动转换
def call_sub(s):
    r = SUB.invoke({"messages": s["messages"]})        # 只挑需要的字段进去
    return {"draft": r["messages"][-1].content}        # 只取需要的字段出来

b = StateGraph(ParentState)
b.add_node("call_sub", call_sub)
b.add_edge(START, "call_sub"); b.add_edge("call_sub", END)
g = b.compile(checkpointer=InMemorySaver())

cfg = {"configurable": {"thread_id": "p1"}}
out = g.invoke({"messages": [HumanMessage("hi")], "user_name": "江雨欣"}, cfg)
print("=" * 70)
print("【A】父 state 多条字段，子 state 只要 messages")
print("  父 state 结果 keys:", list(out.keys()))
print("  draft =", out["draft"])
print("  子图没有反过来污染父 state:", "user_name" in out, "(应为 True)")

print()
print("=" * 70)
print("【B】子图独立持 saver → 它的 checkpoint 归自己")
SUB2 = sb.compile(checkpointer=InMemorySaver())
def call_sub2(s):
    r = SUB2.invoke({"messages": s["messages"]}, {"configurable": {"thread_id": "sub-own"}})
    return {"draft": r["messages"][-1].content}
b2 = StateGraph(ParentState)
b2.add_node("call_sub2", call_sub2)
b2.add_edge(START, "call_sub2"); b2.add_edge("call_sub2", END)
g2 = b2.compile(checkpointer=InMemorySaver())
out2 = g2.invoke({"messages": [HumanMessage("hi")], "user_name": "x"}, {"configurable": {"thread_id": "p2"}})
print("  父图 ns:", [h.config["configurable"].get("checkpoint_ns","") for h in g2.get_state_history({"configurable":{"thread_id":"p2"}})])
print("  子图自己的历史条数:", len(list(SUB2.get_state_history({"configurable":{"thread_id":"sub-own"}}))))
