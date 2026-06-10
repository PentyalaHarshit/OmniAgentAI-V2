from agents.base_agent import BaseAgent


class CabAgent(BaseAgent):
    name = "CabAgent"
    agent_type = "Cab"
    rag_category = "booking"
    required_fields = ['pickup', 'drop', 'date', 'time', 'ride_type', 'passengers']
    optional_fields = ['date', 'ride_type', 'passengers']
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
