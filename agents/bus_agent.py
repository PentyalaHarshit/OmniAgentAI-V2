from agents.base_agent import BaseAgent


class BusAgent(BaseAgent):
    name = "BusAgent"
    agent_type = "Bus"
    rag_category = "booking"
    required_fields = ['source', 'destination', 'date', 'time', 'bus_type', 'passengers', 'budget']
    optional_fields = ['time', 'bus_type', 'budget']
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
