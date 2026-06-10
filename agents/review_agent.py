from agents.base_agent import BaseAgent


class ReviewAgent(BaseAgent):
    name = "ReviewAgent"
    agent_type = "Review"
    rag_category = "booking"
    required_fields = ['booking_id', 'rating', 'feedback']
    optional_fields = []
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
