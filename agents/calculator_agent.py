import re
from agents.base_agent import BaseAgent
from tools.calculator_tool import CalculatorTool


class CalculatorAgent(BaseAgent):
    name = "CalculatorAgent"
    agent_type = "Calculator"
    rag_category = "general"
    required_fields = []
    optional_fields = []

    def __init__(self):
        super().__init__()
        self.calculator = CalculatorTool()

    def run(self, query: str, prefilled_fields=None, session_id: str = "default"):
        thoughts = []

        expression = self.extract_expression(query)

        thoughts.append("Thought: User query looks like a mathematical expression.")
        thoughts.append(f"Action: Send expression to CalculatorTool: {expression}")

        result = self.calculator.calculate(expression)

        thoughts.append(f"Observation: {result}")

        if result["success"]:
            answer = f"{expression} = **{result['result']}**"
        else:
            answer = f"I could not calculate this expression: {result['error']}"

        return self.response(
            query,
            thoughts,
            answer,
            {
                "slot_filling": False,
                "source_stage": "calculator_tool",
                "calculation": result
            }
        )

    def extract_expression(self, query: str) -> str:
        # Strip LLM Tree guidance and uploaded file context first
        q = query
        if "[Free LLM Tree Guidance]" in q:
            q = q.split("[Free LLM Tree Guidance]", 1)[0]
        if "[Uploaded File Context]" in q:
            q = q.split("[Uploaded File Context]", 1)[0]

        q = q.strip()
        q = q.replace("×", "*").replace("÷", "/")
        q = q.replace("^", "**")
        q = re.sub(r"\b(calculate|what is|what's|solve|compute|evaluate|=)\b", "", q, flags=re.I)
        q = q.strip()
        return q