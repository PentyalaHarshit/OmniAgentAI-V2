from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.test_case_crew import TestCaseCrew


class TestCaseAgent(BaseAgent):
    name = "TestCaseAgent"
    agent_type = "TestCase"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = TestCaseCrew()

    def run(self, query: str, code: str = None):
        tasks = [
            "Extract code from query",
            "Detect algorithm type",
            "Detect programming language",
            "Generate edge cases",
            "Generate stress tests",
            "Compute expected outputs",
            "Format test cases",
            "Provide comprehensive test suite"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=12)
        crew_result = self.crew.run(query, code)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_test_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_test_answer(self, crew_result: dict):
        edge_cases = crew_result.get("edge_cases", [])
        stress_tests = crew_result.get("stress_tests", [])
        expected_outputs = crew_result.get("expected_outputs", [])
        
        return (
            "TestCase Agent selected.\n\n"
            f"Algorithm Type: {crew_result.get('algorithm_type', 'Unknown')}\n"
            f"Language: {crew_result.get('language', 'Unknown')}\n\n"
            f"Edge Cases ({len(edge_cases)}):\n"
            + "\n".join(f"- {case['name']}: {case['description']}" for case in edge_cases)
            + "\n\n"
            f"Stress Tests ({len(stress_tests)}):\n"
            + "\n".join(f"- {test['name']}: {test['description']}" for test in stress_tests)
            + "\n\n"
            f"Expected Outputs ({len(expected_outputs)}):\n"
            + "\n".join(f"- {output['test_name']}: {output['expected_output']}" for output in expected_outputs[:5])
            + ("\n... (showing first 5)" if len(expected_outputs) > 5 else "")
        )
