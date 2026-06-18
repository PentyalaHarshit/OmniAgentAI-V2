from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.system_design_crew import SystemDesignCrew


class SystemDesignAgent(BaseAgent):
    name = "SystemDesignAgent"
    agent_type = "SystemDesign"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = SystemDesignCrew()

    def run(self, query: str):
        tasks = [
            "Detect system type from query",
            "Extract functional and non-functional requirements",
            "Estimate system scale",
            "Generate system architecture",
            "Design database schema",
            "Plan scaling strategy",
            "Design caching layers",
            "Configure load balancing",
            "Provide comprehensive design document"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_system_design_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_system_design_answer(self, crew_result: dict):
        architecture = crew_result.get("architecture", {})
        database = crew_result.get("database_design", {})
        scaling = crew_result.get("scaling_strategy", {})
        caching = crew_result.get("caching_strategy", {})
        load_balancing = crew_result.get("load_balancing", {})
        scale = crew_result.get("scale", {})
        requirements = crew_result.get("requirements", {})
        
        return (
            "System Design Agent selected.\n\n"
            f"System Type: {crew_result.get('system_type', 'Unknown')}\n\n"
            "Requirements:\n"
            f"- Functional: {', '.join(requirements.get('functional', ['None']))}\n"
            f"- Non-Functional: {', '.join(requirements.get('non_functional', ['None']))}\n"
            f"- Constraints: {', '.join(requirements.get('constraints', ['None']))}\n\n"
            "Scale Estimation:\n"
            f"- Users: {scale.get('users', 'Unknown')}\n"
            f"- Requests/Second: {scale.get('requests_per_second', 'Unknown')}\n"
            f"- Data Size: {scale.get('data_size', 'Unknown')}\n"
            f"- Growth Rate: {scale.get('growth_rate', 'Unknown')}\n\n"
            "Architecture:\n"
            f"- Pattern: {architecture.get('pattern', 'Unknown')}\n"
            f"- Components: {', '.join(architecture.get('components', []))}\n\n"
            "Database Design:\n"
            f"- Primary: {database.get('primary', 'Unknown')}\n"
            f"- Secondary: {database.get('secondary', 'Unknown')}\n"
            f"- Cache: {database.get('cache', 'Unknown')}\n"
            f"- Storage: {database.get('storage', 'Not specified')}\n\n"
            "Scaling Strategy:\n"
            f"- Strategy: {scaling.get('strategy', 'Unknown')}\n"
            f"- Horizontal Scaling: {scaling.get('horizontal_scaling', 'Unknown')}\n"
            f"- Database Scaling: {scaling.get('database_scaling', 'Unknown')}\n\n"
            "Caching Strategy:\n"
            f"- Cache Layers: {', '.join(caching.get('cache_layers', []))}\n"
            f"- Cache Type: {caching.get('cache_type', 'Unknown')}\n"
            f"- Strategy: {caching.get('cache_strategy', 'Unknown')}\n\n"
            "Load Balancing:\n"
            f"- Type: {load_balancing.get('type', 'Unknown')}\n"
            f"- Algorithm: {load_balancing.get('algorithm', 'Unknown')}\n"
            f"- Health Checks: {load_balancing.get('health_checks', 'Unknown')}"
        )
