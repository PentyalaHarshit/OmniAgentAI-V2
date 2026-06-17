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
        answer = self.build_coding_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_coding_answer(self, crew_result: dict):
        candidates = crew_result.get("algorithm_candidates", [])
        alternatives = [
            f"{idx}. {candidate['name']} - {candidate['score']}/100"
            for idx, candidate in enumerate(candidates, start=1)
            if candidate["name"] != crew_result.get("selected_algorithm_label")
        ]
        react_lines = [
            f"- Reason: {step['reason']} | Action: {step['action']} | Observation: {step['observation']}"
            for step in crew_result.get("react_trace", [])
        ]
        crew_ai = crew_result.get("crew_ai", {})
        multi_llm = crew_result.get("multi_llm", {})
        verification = crew_result.get("verification", {})
        reasoning_mode = crew_result.get("reasoning_mode", {})
        alphacode_search = crew_result.get("alphacode_search", {})
        alphacode_section = ""
        if alphacode_search.get("enabled"):
            strategies = alphacode_search.get("strategy_candidates", [])[:5]
            strategy_lines = [
                f"- {item.get('name', 'unknown')} ({item.get('source', 'unknown')}) - {item.get('score', 0)}/100"
                for item in strategies
            ]
            alphacode_section = (
                "AlphaCode-Style Search:\n"
                f"- Status: {alphacode_search.get('status', 'unknown')}\n"
                f"- Policy: {alphacode_search.get('policy', '')}\n"
                "- Strategy Candidates:\n"
                + ("\n".join(strategy_lines) if strategy_lines else "- None")
                + "\n\n"
            )
        return (
            "Coding Agent selected.\n\n"
            + alphacode_section
            + (
                "Adaptive Reasoning:\n"
                f"- Level: {reasoning_mode.get('level', 'unknown')}\n"
                f"- Agents: {', '.join(reasoning_mode.get('agents', []))}\n"
                f"- Reason: {reasoning_mode.get('reason', 'n/a')}\n\n"
                if reasoning_mode else ""
            )
            + f"Selected Algorithm:\n{crew_result.get('selected_algorithm_label', crew_result['selected_algorithm'])}\n\n"
            + "Alternative Candidates:\n"
            + ("\n".join(alternatives) if alternatives else "- No alternatives found")
            + "\n\n"
            f"Reasoning Score:\n{crew_result.get('reasoning_score', 0)}/100\n\n"
            f"Time Complexity:\n{crew_result['reviewer']['time_complexity']}\n\n"
            f"Memory Complexity:\n{crew_result['reviewer']['space_complexity']}\n\n"
            "ReAct Trace:\n"
            + "\n".join(react_lines)
            + "\n\n"
            "CrewAI Review:\n"
            f"- Evaluator Agent: {crew_ai.get('evaluator', {}).get('notes', 'n/a')}\n"
            f"- Analyzer Agent: {crew_ai.get('analyzer', {}).get('time_complexity', 'n/a')} time, "
            f"{crew_ai.get('analyzer', {}).get('memory_complexity', 'n/a')} memory\n"
            f"- Validator Agent: {crew_ai.get('validator', {}).get('notes', 'n/a')}\n\n"
            "Multi-LLM Improvements:\n"
            + "\n".join(f"- {model}: {suggestion}" for model, suggestion in multi_llm.items())
            + "\n\n"
            "Validation:\n"
            f"- Compilation {verification.get('compilation', 'Unknown')}\n"
            f"- Problem Solved {'Yes' if verification.get('problem_solved') else 'No'}\n"
            f"- Reason: {verification.get('reason', 'n/a')}\n"
            f"- Retry Required {'Yes' if verification.get('retry_required') else 'No'}\n"
            f"- Unit Tests {verification.get('unit_tests', 'Unknown')}\n"
            f"- Complexity {'Verified' if verification.get('complexity_verified') else 'Not verified'}\n\n"
            f"- Problem Logic {'Verified' if verification.get('problem_specific_logic') else 'Not verified'}\n\n"
            f"Confidence:\n{verification.get('confidence', 0)}%\n\n"
            f"RAG Sources: {crew_result['rag']['sources']}\n"
            f"Language: {crew_result['language']}\n"
            f"Status: {crew_result['status']}\n\n"
            f"Compile Output:\n{crew_result['compile_result']['output']}\n\n"
            f"Test Output:\n{crew_result['test_result']['output']}\n\n"
            f"Code:\n```{crew_result['language']}\n{crew_result['code']}\n```"
        )
