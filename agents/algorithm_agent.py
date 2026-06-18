from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.algorithm_crew import AlgorithmCrew


class AlgorithmAgent(BaseAgent):
    name = "AlgorithmAgent"
    agent_type = "Algorithm"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = AlgorithmCrew()

    def run(self, query: str):
        tasks = [
            "Detect problem type from query",
            "Extract constraints",
            "Identify problem patterns",
            "Rank candidate algorithms",
            "Select best algorithm",
            "Provide algorithm recommendations",
            "Explain reasoning"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=10)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_algorithm_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_algorithm_answer(self, crew_result: dict):
        ranked = crew_result.get("ranked_algorithms", [])
        best = crew_result.get("best_algorithm", {})
        constraints = crew_result.get("constraints", {})
        
        return (
            "Algorithm Agent selected.\n\n"
            f"Problem Type: {crew_result.get('problem_type', 'Unknown')}\n\n"
            "Constraints:\n"
            f"- N: {constraints.get('n', 'Not specified')}\n"
            f"- M: {constraints.get('m', 'Not specified')}\n"
            f"- Time Limit: {constraints.get('time_limit', 'Not specified')}\n"
            f"- Memory Limit: {constraints.get('memory_limit', 'Not specified')}\n"
            f"- Special: {', '.join(constraints.get('special', ['None']))}\n\n"
            "Ranked Algorithms:\n"
            + "\n".join(
                f"{i+1}. {algo['name']} (Score: {algo['score']}/100)\n"
                f"   Time: {algo['time_complexity']}\n"
                f"   Space: {algo['space_complexity']}\n"
                f"   Best for: {', '.join(algo['best_for'])}"
                for i, algo in enumerate(ranked[:5])
            )
            + "\n\n"
            "Best Algorithm:\n"
            f"- {best['name']}\n"
            f"- Time Complexity: {best['time_complexity']}\n"
            f"- Space Complexity: {best['space_complexity']}\n"
            f"- Score: {best['score']}/100"
        )
