from agents.base_agent import BaseAgent


class EventAgent(BaseAgent):
    name = "EventAgent"
    agent_type = "Event"
    rag_category = "booking"
    required_fields = ['event_type', 'location', 'date', 'time', 'tickets', 'budget']
    optional_fields = ['time', 'budget']
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
