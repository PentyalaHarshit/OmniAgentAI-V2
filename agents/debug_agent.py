from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.debug_crew import DebugCrew


class DebugAgent(BaseAgent):
    name = "DebugAgent"
    agent_type = "Debug"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = DebugCrew()

    def run(self, query: str, code: str = None, error_message: str = None):
        tasks = [
            "Extract error information from query",
            "Extract code snippet",
            "Detect programming language",
            "Analyze root cause of error",
            "Generate fix suggestion",
            "Apply fix to code",
            "Verify corrected code",
            "Provide debugging report"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=12)
        crew_result = self.crew.run(query, code, error_message)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_debug_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_debug_answer(self, crew_result: dict):
        root_cause = crew_result.get("root_cause", {})
        error_msg = crew_result.get("error_message", "No error message provided")
        
        return (
            "Debug Agent selected.\n\n"
            f"Language: {crew_result.get('language', 'Unknown')}\n\n"
            f"Error Message:\n{error_msg}\n\n"
            "Root Cause Analysis:\n"
            f"- Type: {root_cause.get('type', 'Unknown')}\n"
            f"- Description: {root_cause.get('description', 'N/A')}\n"
            f"- Location: {root_cause.get('location', 'Unknown')}\n"
            f"- Severity: {root_cause.get('severity', 'Unknown')}\n\n"
            f"Fix Suggestion:\n{crew_result.get('fix_suggestion', 'No suggestion available')}\n\n"
            "Original Code:\n"
            f"```{crew_result.get('language', 'python')}\n{crew_result.get('original_code', 'No code provided')}\n```\n\n"
            "Corrected Code:\n"
            f"```{crew_result.get('language', 'python')}\n{crew_result.get('corrected_code', 'No corrected code available')}\n```"
        )
