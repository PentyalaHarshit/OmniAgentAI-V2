from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.ai_architect_crew import AIArchitectCrew


class AIArchitectAgent(BaseAgent):
    name = "AIArchitectAgent"
    agent_type = "AIArchitect"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = AIArchitectCrew()

    def run(self, query: str):
        tasks = [
            "Detect agentic system type",
            "Estimate system complexity",
            "Design router agent",
            "Design ToT agent",
            "Design ReAct agent",
            "Design memory system",
            "Design RAG system",
            "Design verification layer",
            "Design multi-LLM integration",
            "Design deployment strategy",
            "Provide comprehensive AI architecture"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=16)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_ai_architect_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_ai_architect_answer(self, crew_result: dict):
        router = crew_result.get("router_agent", {})
        tot = crew_result.get("tot_agent", {})
        react = crew_result.get("react_agent", {})
        memory = crew_result.get("memory_system", {})
        rag = crew_result.get("rag_system", {})
        verification = crew_result.get("verification", {})
        multi_llm = crew_result.get("multi_llm", {})
        deployment = crew_result.get("deployment", {})
        complexity = crew_result.get("complexity", {})
        
        return (
            "AIArchitect Agent selected.\n\n"
            f"System Type: {crew_result.get('system_type', 'Unknown')}\n\n"
            "Complexity Estimation:\n"
            f"- Level: {complexity.get('level', 'Unknown')}\n"
            f"- Agents: {complexity.get('agents', 'Unknown')}\n"
            f"- Reasoning Depth: {complexity.get('reasoning_depth', 'Unknown')}\n\n"
            "Router Agent:\n"
            f"- Purpose: {router.get('purpose', 'Unknown')}\n"
            f"- Features: {', '.join(router.get('features', []))}\n\n"
            "ToT Agent:\n"
            f"- Purpose: {tot.get('purpose', 'Unknown')}\n"
            f"- Features: {', '.join(tot.get('features', []))}\n\n"
            "ReAct Agent:\n"
            f"- Purpose: {react.get('purpose', 'Unknown')}\n"
            f"- Features: {', '.join(react.get('features', []))}\n\n"
            "Memory System:\n"
            f"- Architecture: {memory.get('architecture', 'Unknown')}\n"
            f"- Components: {len(memory.get('components', []))} layers\n"
            f"- Retrieval: {', '.join(memory.get('retrieval', []))}\n\n"
            "RAG System:\n"
            f"- Purpose: {rag.get('purpose', 'Unknown')}\n"
            f"- Architecture: {rag.get('architecture', 'Unknown')}\n"
            f"- Optimizations: {', '.join(rag.get('optimizations', []))}\n\n"
            "Verification:\n"
            f"- Layers: {len(verification.get('layers', []))} verification layers\n"
            f"- Metrics: {', '.join(verification.get('metrics', []))}\n\n"
            "Multi-LLM Integration:\n"
            f"- Strategy: {multi_llm.get('strategy', 'Unknown')}\n"
            f"- Models: {len(multi_llm.get('models', []))} specialized models\n\n"
            "Deployment:\n"
            f"- Architecture: {deployment.get('architecture', 'Unknown')}\n"
            f"- Components: {', '.join(deployment.get('components', []))}\n"
            f"- Infrastructure: {', '.join(deployment.get('infrastructure', []))}"
        )
