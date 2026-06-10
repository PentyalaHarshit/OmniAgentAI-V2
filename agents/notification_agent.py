from agents.base_agent import BaseAgent


class NotificationAgent(BaseAgent):
    name = "NotificationAgent"
    agent_type = "Notification"
    rag_category = "booking"
    required_fields = ['booking_id', 'channel', 'date', 'time', 'message']
    optional_fields = ['time']
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
