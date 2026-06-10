from agents.base_agent import BaseAgent


class PaymentAgent(BaseAgent):
    name = "PaymentAgent"
    agent_type = "Payment"
    rag_category = "shopping"
    required_fields = ['amount', 'payment_method', 'currency']
    optional_fields = ['currency']
    base_tasks = [
        "Parse user request",
        "Generate N thought branches",
        "Retrieve RAG knowledge",
        "Check missing required fields",
        "Ask follow-up question if needed",
        "Call CrewAI-style sub-agents",
        "Verify safety",
        "Return final recommendation"
    ]
