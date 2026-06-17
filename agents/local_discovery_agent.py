from agents.base_agent import BaseAgent


class LocalDiscoveryAgent(BaseAgent):
    name = "LocalDiscoveryAgent"
    agent_type = "LocalDiscovery"
    rag_category = "local"

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        answer = "\n".join([
            "LocalDiscoveryAgent / local_discovery",
            "",
            "Top Places",
            "",
            "1. Dallas Arboretum",
            "2. Reunion Tower",
            "3. Perot Museum",
            "4. Dallas Zoo",
        ])
        return self.response(query, ["LocalDiscoveryAgent: returned top local attractions."], answer, {})
