from agents.base_agent import BaseAgent


class FlightAgent(BaseAgent):
    name = "FlightAgent"
    agent_type = "Flight"
    rag_category = "booking"
    required_fields = ['origin', 'destination', 'date', 'time', 'passengers', 'budget', 'airline', 'baggage']
    optional_fields = ['time', 'budget', 'airline', 'baggage']
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
