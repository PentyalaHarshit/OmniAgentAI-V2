from agents.base_agent import BaseAgent


class CancellationAgent(BaseAgent):
    name = "CancellationAgent"
    agent_type = "Cancellation"
    rag_category = "booking"
    required_fields = ['booking_id', 'reason', 'new_date', 'refund_method']
    optional_fields = ['new_date', 'refund_method']
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
