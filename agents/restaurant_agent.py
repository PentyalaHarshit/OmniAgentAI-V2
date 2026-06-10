from agents.base_agent import BaseAgent


class RestaurantAgent(BaseAgent):
    name = "RestaurantAgent"
    agent_type = "Restaurant"
    rag_category = "booking"
    required_fields = ['cuisine', 'location', 'party_size', 'date', 'time', 'budget']
    optional_fields = ['budget']
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
