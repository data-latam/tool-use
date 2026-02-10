"""Calculator — safe math evaluation. No external API needed."""

import ast
import operator

from app.sdk import ToolServer

server = ToolServer("calculator", "Safe math calculator")

# -- safe eval engine -------------------------------------------------------

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op = _OPS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _OPS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_node(node.operand))
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


# -- tool -------------------------------------------------------------------

@server.register("calculate", description="Evaluate a mathematical expression")
async def calculate(expression: str) -> dict:
    tree = ast.parse(expression, mode="eval")
    result = _eval_node(tree.body)
    return {"result": result, "expression": expression}
