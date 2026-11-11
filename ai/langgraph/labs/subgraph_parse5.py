"""
验证：【5】链式 vs 赋值 在「需要 stream 中间过程」的场景下是否有差别
以及 AST 层面的可解析性对照
"""
import ast, inspect, operator
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

def parent_chained(s):
    return {"result": subgraph.invoke({"raw_text": s["raw_text"]})["processed"]}

def parent_assigned(s):
    res = subgraph.invoke({"raw_text": s["raw_text"]})
    return {"result": res["processed"]}

print("=" * 72)
print("【5-A】AST 分析：节点函数源码里能否静态识别出 subgraph.invoke 调用")
for label, fn in [("链式 ❌", parent_chained), ("赋值 ✅", parent_assigned)]:
    src = inspect.getsource(fn)
    tree = ast.parse(src.strip())
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr == "invoke":
                # 判断这个 Call 是否是 Subscript 的值（即链式索引）
                found.append(ast.unparse(node))
    print(f"  {label}: 找到 invoke 调用 = {found}")

    # 关键差异：赋值写法里 invoke 的返回值绑定给了变量名
    assigns = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            v = node.value
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "invoke":
                assigns.append(ast.unparse(node))
    print(f"           独立赋值语句 = {assigns}")
    print()

print()
print("=" * 72)
print("【5-B】get_graph 的 xray 参数（递归展开子图）")
saver = InMemorySaver()
b = StateGraph(dict)
b.add_node("sub", subgraph)
b.add_edge(START, "sub"); b.add_edge("sub", END)
g = b.compile(checkpointer=saver)

plain = g.get_graph()
print("  get_graph() 默认 nodes:", list(plain.nodes))
try:
    x = g.get_graph(xray=True)
    print("  get_graph(xray=1) nodes:", list(x.nodes))
except Exception as e:
    print("  xray 报错:", type(e).__name__, e)
