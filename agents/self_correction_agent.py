from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.self_correction_crew import SelfCorrectionCrew


class SelfCorrectionAgent(BaseAgent):
    name = "SelfCorrectionAgent"
    agent_type = "SelfCorrection"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = SelfCorrectionCrew()

    def run(self, query: str, code: str = None, test_result: str = None):
        tasks = [
            "Extract code and test results",
            "Detect programming language",
            "Analyze failure reason",
            "Develop improvement strategy",
            "Generate improved code",
            "Create verification plan",
            "Provide self-correction report"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=12)
        crew_result = self.crew.run(query, code, test_result)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_self_correction_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_self_correction_answer(self, crew_result: dict):
        failure = crew_result.get("failure_analysis", {})
        strategy = crew_result.get("improvement_strategy", {})
        verification = crew_result.get("verification_plan", {})
        
        return (
            "SelfCorrection Agent selected.\n\n"
            f"Language: {crew_result.get('language', 'Unknown')}\n\n"
            "Failure Analysis:\n"
            f"- Root Cause: {failure.get('root_cause', 'Unknown')}\n"
            f"- Failure Type: {failure.get('failure_type', 'Unknown')}\n"
            f"- Location: {failure.get('location', 'Unknown')}\n"
            f"- Confidence: {failure.get('confidence', 0)}%\n\n"
            "Improvement Strategy:\n"
            f"- Strategy: {strategy.get('strategy', 'Unknown')}\n"
            f"- Priority: {strategy.get('priority', 'Unknown')}\n"
            "- Actions:\n"
            + "\n".join(f"  • {action}" for action in strategy.get('actions', []))
            + "\n\n"
            "Original Code:\n"
            f"```{crew_result.get('language', 'python')}\n{crew_result.get('original_code', 'No code provided')}\n```\n\n"
            "Improved Code:\n"
            f"```{crew_result.get('language', 'python')}\n{crew_result.get('improved_code', 'No improved code available')}\n```\n\n"
            "Verification Plan:\n"
            "- Test Cases:\n"
            + "\n".join(f"  • {case}" for case in verification.get('test_cases', []))
            + "\n- Verification Steps:\n"
            + "\n".join(f"  • {step}" for step in verification.get('verification_steps', []))
            + "\n- Success Criteria:\n"
            + "\n".join(f"  • {criteria}" for criteria in verification.get('success_criteria', []))
        )
