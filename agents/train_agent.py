from agents.base_agent import BaseAgent


class TrainAgent(BaseAgent):
    name = "TrainAgent"
    agent_type = "Train"
    rag_category = "booking"
    required_fields = ['source', 'destination', 'date', 'time', 'class', 'passengers', 'budget']
    optional_fields = ['time', 'class', 'budget']
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
