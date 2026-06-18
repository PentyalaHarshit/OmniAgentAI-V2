from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.code_review_crew import CodeReviewCrew


class CodeReviewAgent(BaseAgent):
    name = "CodeReviewAgent"
    agent_type = "CodeReview"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = CodeReviewCrew()

    def run(self, query: str, code: str = None):
        tasks = [
            "Extract code from query",
            "Detect programming language",
            "Analyze code quality",
            "Calculate time complexity",
            "Calculate memory complexity",
            "Detect potential bugs",
            "Scan for security issues",
            "Suggest optimizations",
            "Generate comprehensive report"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=12)
        crew_result = self.crew.run(query, code)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_review_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_review_answer(self, crew_result: dict):
        if crew_result.get("status") == "need_code":
            return crew_result.get(
                "message",
                "Please paste your C++ code so I can find the TLE bottleneck and optimize it."
            )

        quality = crew_result.get("code_quality_score", {})
        bugs = crew_result.get("potential_bugs", [])
        security = crew_result.get("security_issues", [])
        optimizations = crew_result.get("optimization_suggestions", [])
        
        return (
            "Code Review Agent selected.\n\n"
            f"Language: {crew_result.get('language', 'Unknown')}\n\n"
            "Code Quality Score:\n"
            f"- Overall: {quality.get('overall', 0)}/100\n"
            f"- Readability: {quality.get('readability', 0)}/100\n"
            f"- Maintainability: {quality.get('maintainability', 0)}/100\n"
            f"- Documentation: {quality.get('documentation', 0)}/100\n\n"
            f"Time Complexity:\n{crew_result.get('time_complexity', 'Unknown')}\n\n"
            f"Memory Complexity:\n{crew_result.get('memory_complexity', 'Unknown')}\n\n"
            f"Potential Bugs ({len(bugs)} found):\n"
            + ("\n".join(f"- {bug['type']} ({bug['severity']}): {bug['description']}" for bug in bugs) if bugs else "- No bugs detected")
            + "\n\n"
            f"Security Issues ({len(security)} found):\n"
            + ("\n".join(f"- {issue['type']} ({issue['severity']}): {issue['description']}" for issue in security) if security else "- No security issues detected")
            + "\n\n"
            f"Optimization Suggestions ({len(optimizations)}):\n"
            + ("\n".join(f"- {opt['type']} ({opt['impact']}): {opt['description']}" for opt in optimizations) if optimizations else "- No optimization suggestions")
            + "\n\n"
            "Reviewed Code:\n"
            f"```{crew_result.get('language', 'python')}\n{crew_result.get('reviewed_code', 'No code provided')}\n```"
        )
