from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.coding_crew import CodingCrew


class CodingAgent(BaseAgent):
    name = "CodingAgent"
    agent_type = "Coding"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = CodingCrew()

    def run(self, query: str):
        tasks = [
            "Analyze problem statement",
            "Retrieve coding RAG",
            "Identify constraints",
            "Generate algorithm candidates",
            "Score algorithms",
            "Generate code",
            "Compile code",
            "Run sample tests",
            "Self-correct if failed",
            "Review complexity"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=18)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = (
            "Coding Agent selected.\n\n"
            f"RAG Sources: {crew_result['rag']['sources']}\n"
            f"Selected Algorithm: {crew_result['selected_algorithm']}\n"
            f"Language: {crew_result['language']}\n"
            f"Status: {crew_result['status']}\n\n"
            f"Compile Output:\n{crew_result['compile_result']['output']}\n\n"
            f"Test Output:\n{crew_result['test_result']['output']}\n\n"
            f"Code:\n```{crew_result['language']}\n{crew_result['code']}\n```"
        )
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})
