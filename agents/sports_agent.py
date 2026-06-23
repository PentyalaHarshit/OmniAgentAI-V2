from agents.base_agent import BaseAgent
from tools.mcp_live_tools import SportsTool


class SportsAgent(BaseAgent):
    name = "SportsAgent"
    agent_type = "Sports"
    base_tasks = [
        "Detect sports query",
        "Fetch live standings or sports data",
        "Generate sourced answer",
    ]

    def __init__(self):
        super().__init__()
        self.sports_tool = SportsTool()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        thoughts = self.tot.create_thoughts(self.agent_type, query, self.base_tasks)
        thoughts.append("SportsAgent: calling live sports API source.")

        answer = self.sports_tool.execute(query)
        if not answer:
            answer = (
                "I could not fetch live sports standings for that query right now. "
                "Try a league-specific query such as NBA standings, IPL points table, "
                "Premier League table, or FIFA World Cup standings."
            )
            verification = {
                "verified": False,
                "confidence": 0.0,
                "reason": "No live sports API result was available.",
                "corrected": "",
                "sources_used": 0,
            }
        else:
            verification = {
                "verified": True,
                "confidence": 0.85,
                "reason": "Returned by live sports API/source.",
                "corrected": answer,
                "sources_used": 1,
            }

        return self.response(query, thoughts, answer, {
            "slot_filling": False,
            "source_stage": "sports_api",
            "api_route": "SportsAgent",
            "verification": verification,
        })
