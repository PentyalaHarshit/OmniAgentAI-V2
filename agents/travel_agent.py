from agents.base_agent import BaseAgent


class TravelAgent(BaseAgent):
    name = "TravelAgent"
    agent_type = "Travel"
    rag_category = "booking"
    required_fields = ['destination', 'dates', 'travelers', 'budget', 'interests']
    optional_fields = ['interests', 'budget']
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
