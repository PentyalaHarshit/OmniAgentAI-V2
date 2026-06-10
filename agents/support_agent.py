from agents.base_agent import BaseAgent


class SupportAgent(BaseAgent):
    name = "SupportAgent"
    agent_type = "Support"
    rag_category = "booking"
    required_fields = ['booking_id', 'issue_type', 'message']
    optional_fields = ['booking_id']
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
