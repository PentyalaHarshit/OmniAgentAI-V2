from agents.base_agent import BaseAgent


class CouponAgent(BaseAgent):
    name = "CouponAgent"
    agent_type = "Coupon"
    rag_category = "shopping"
    required_fields = ['booking_type', 'coupon_code', 'amount', 'user_status']
    optional_fields = ['coupon_code', 'user_status']
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
