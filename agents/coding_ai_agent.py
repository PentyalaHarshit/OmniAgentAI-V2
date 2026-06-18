from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from agents.coding_agent import CodingAgent
from agents.debug_agent import DebugAgent
from agents.code_review_agent import CodeReviewAgent
from agents.test_case_agent import TestCaseAgent
from agents.algorithm_agent import AlgorithmAgent
from agents.system_design_agent import SystemDesignAgent
from agents.deployment_agent import DeploymentAgent
from agents.ml_agent import MLAgent
from agents.rag_agent import RAGAgent
from agents.research_agent import ResearchAgent
from agents.data_science_agent import DataScienceAgent
from agents.mlops_agent import MLOpsAgent
from agents.ai_architect_agent import AIArchitectAgent
from agents.self_correction_agent import SelfCorrectionAgent


class CodingAIAgent(BaseAgent):
    name = "CodingAIAgent"
    agent_type = "CodingAI"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        # Initialize all coding and AI sub-agents
        self.coding_agent = CodingAgent()
        self.debug_agent = DebugAgent()
        self.code_review_agent = CodeReviewAgent()
        self.test_case_agent = TestCaseAgent()
        self.algorithm_agent = AlgorithmAgent()
        self.system_design_agent = SystemDesignAgent()
        self.deployment_agent = DeploymentAgent()
        self.ml_agent = MLAgent()
        self.rag_agent = RAGAgent()
        self.research_agent = ResearchAgent()
        self.data_science_agent = DataScienceAgent()
        self.mlops_agent = MLOpsAgent()
        self.ai_architect_agent = AIArchitectAgent()
        self.self_correction_agent = SelfCorrectionAgent()

    def run(self, query: str, code: str = None, error_message: str = None):
        tasks = [
            "Analyze query type and complexity",
            "Route to appropriate specialized agent",
            "Execute specialized agent workflow",
            "Aggregate results from multiple agents if needed",
            "Coordinate agent collaboration",
            "Provide comprehensive response",
            "Ensure quality and verification"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        
        # Route to appropriate sub-agent
        sub_agent, agent_name = self.route_to_sub_agent(query)
        
        # Execute sub-agent
        try:
            if code or error_message:
                result = sub_agent.run(query, code=code, error_message=error_message)
            else:
                result = sub_agent.run(query)
        except TypeError:
            result = sub_agent.run(query)
        
        crew_thoughts = [s["thought"] for s in result.get("crew_steps", [])]
        answer = self.build_coding_ai_answer(result, agent_name)
        
        return self.response(query, thoughts + crew_thoughts, answer, {
            "sub_agent": agent_name,
            "crew_result": result
        })

    def route_to_sub_agent(self, query: str):
        """Route query to the most appropriate specialized agent."""
        q = query.lower()
        
        # Priority routing for coding and AI tasks
        if any(kw in q for kw in ["review", "code review", "optimize", "security check"]):
            return self.code_review_agent, "CodeReviewAgent"
        elif any(kw in q for kw in ["debug", "fix", "error", "bug", "segmentation fault"]):
            return self.debug_agent, "DebugAgent"
        elif any(kw in q for kw in ["test case", "edge case", "stress test", "generate test"]):
            return self.test_case_agent, "TestCaseAgent"
        elif any(kw in q for kw in ["algorithm", "best algorithm", "pattern detection"]):
            return self.algorithm_agent, "AlgorithmAgent"
        elif any(kw in q for kw in ["ai architect", "agentic system", "agentic rag", "multi-agent"]):
            return self.ai_architect_agent, "AIArchitectAgent"
        elif any(kw in q for kw in ["mlops", "ml pipeline", "model registry"]):
            return self.mlops_agent, "MLOpsAgent"
        elif any(kw in q for kw in ["rag", "retrieval", "vector database", "embedding"]):
            return self.rag_agent, "RAGAgent"
        elif any(kw in q for kw in ["design", "architecture", "youtube", "whatsapp"]):
            return self.system_design_agent, "SystemDesignAgent"
        elif any(kw in q for kw in ["deploy", "docker", "kubernetes", "ci/cd"]):
            return self.deployment_agent, "DeploymentAgent"
        elif any(kw in q for kw in ["train", "model", "prediction", "classification"]):
            return self.ml_agent, "MLAgent"
        elif any(kw in q for kw in ["data science", "eda", "analysis", "churn"]):
            return self.data_science_agent, "DataScienceAgent"
        elif any(kw in q for kw in ["self-correct", "improve", "retry", "correct"]):
            return self.self_correction_agent, "SelfCorrectionAgent"
        elif any(kw in q for kw in ["research", "paper", "literature"]):
            return self.research_agent, "ResearchAgent"
        else:
            # Default to coding agent for general coding tasks
            return self.coding_agent, "CodingAgent"

    def build_coding_ai_answer(self, result: dict, agent_name: str):
        """Build comprehensive answer from sub-agent result."""
        return (
            f"CodingAI Agent selected.\n"
            f"Routed to: {agent_name}\n\n"
            f"{result.get('answer', 'No answer available')}"
        )
