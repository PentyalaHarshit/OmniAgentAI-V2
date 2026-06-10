from agents.base_agent import BaseAgent


class VacationPackageAgent(BaseAgent):
    name = "VacationPackageAgent"
    agent_type = "VacationPackage"
    rag_category = "booking"
    required_fields = ['destination', 'duration', 'dates', 'travelers', 'budget', 'interests']
    optional_fields = ['interests']
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
