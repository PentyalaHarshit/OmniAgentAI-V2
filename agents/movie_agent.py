from agents.base_agent import BaseAgent


class MovieAgent(BaseAgent):
    name = "MovieAgent"
    agent_type = "Movie"
    rag_category = "booking"
    required_fields = ['movie', 'city', 'theater', 'date', 'time', 'tickets', 'seats']
    optional_fields = ['theater', 'seats']
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
