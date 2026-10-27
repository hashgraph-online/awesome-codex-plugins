"""Evaluate bounded arithmetic from agent input without executing Python code."""

import ast
import math
import operator


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def calculate(expression: str) -> float:
    if len(expression) > 80:
        raise ValueError("expression is too long")

    def walk(node: ast.AST, depth: int = 0) -> float:
        if depth > 12:
            raise ValueError("expression is too deep")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = float(node.value)
        elif isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            value = _OPERATORS[type(node.op)](walk(node.left, depth + 1), walk(node.right, depth + 1))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            value = _UNARY[type(node.op)](walk(node.operand, depth + 1))
        else:
            raise ValueError("only numeric literals and +, -, *, / are allowed")
        if not math.isfinite(value) or abs(value) > 1e12:
            raise ValueError("result is out of range")
        return value

    return walk(ast.parse(expression, mode="eval").body)
