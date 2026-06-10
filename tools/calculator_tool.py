import ast
import operator as op
import math


class CalculatorTool:
    allowed_ops = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
        ast.USub: op.neg,
        ast.UAdd: op.pos,
    }

    allowed_funcs = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "abs": abs,
        "round": round,
    }

    allowed_names = {
        "pi": math.pi,
        "e": math.e,
    }

    def calculate(self, expression: str):
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._eval(tree.body)

            return {
                "success": True,
                "expression": expression,
                "result": result
            }

        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }

    def _eval(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed")

        if isinstance(node, ast.BinOp):
            if type(node.op) not in self.allowed_ops:
                raise ValueError("Operator not allowed")
            return self.allowed_ops[type(node.op)](
                self._eval(node.left),
                self._eval(node.right)
            )

        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.allowed_ops:
                raise ValueError("Unary operator not allowed")
            return self.allowed_ops[type(node.op)](
                self._eval(node.operand)
            )

        if isinstance(node, ast.Name):
            if node.id in self.allowed_names:
                return self.allowed_names[node.id]
            raise ValueError(f"Name not allowed: {node.id}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple functions allowed")

            func_name = node.func.id

            if func_name not in self.allowed_funcs:
                raise ValueError(f"Function not allowed: {func_name}")

            args = [self._eval(arg) for arg in node.args]

            return self.allowed_funcs[func_name](*args)

        raise ValueError("Invalid expression")