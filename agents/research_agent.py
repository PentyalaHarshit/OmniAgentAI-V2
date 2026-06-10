from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.research_crew import ResearchCrew


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    agent_type = "Research"
    rag_category = "research"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = ResearchCrew()

    def run(self, query: str):
        file_context = query.split("[Uploaded File Context]", 1)[-1].strip() if "[Uploaded File Context]" in query else ""
        tasks = ["Understand topic", "Retrieve research RAG", "Use uploaded context", "Find methods", "Find gaps", "Self-check claims"]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        result = self.crew.run(query, file_context)
        crew_thoughts = [s["thought"] for s in result["crew_steps"]]
        return self.response(query, thoughts + crew_thoughts, result["answer"], {"crew_result": result})
