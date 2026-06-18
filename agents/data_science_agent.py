from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.data_science_crew import DataScienceCrew


class DataScienceAgent(BaseAgent):
    name = "DataScienceAgent"
    agent_type = "DataScience"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = DataScienceCrew()

    def run(self, query: str):
        tasks = [
            "Detect data science task type",
            "Identify analysis type",
            "Design exploratory data analysis",
            "Suggest visualizations",
            "Analyze features",
            "Generate insights",
            "Provide comprehensive analysis plan"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=12)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_data_science_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_data_science_answer(self, crew_result: dict):
        eda = crew_result.get("eda_steps", [])
        visualizations = crew_result.get("visualizations", [])
        features = crew_result.get("feature_analysis", {})
        insights = crew_result.get("insights", [])
        
        return (
            "DataScience Agent selected.\n\n"
            f"Task Type: {crew_result.get('task_type', 'Unknown')}\n"
            f"Analysis Type: {crew_result.get('analysis_type', 'Unknown')}\n\n"
            "Exploratory Data Analysis Steps:\n"
            + "\n".join(f"{i+1}. {step}" for i, step in enumerate(eda))
            + "\n\n"
            f"Visualizations ({len(visualizations)}):\n"
            + "\n".join(f"- {viz['type']}: {viz['purpose']}" for viz in visualizations[:8])
            + ("\n... (showing first 8)" if len(visualizations) > 8 else "")
            + "\n\n"
            "Feature Analysis:\n"
            f"- Numerical Features: {', '.join(features.get('numerical_features', []))}\n"
            f"- Categorical Features: {', '.join(features.get('categorical_features', []))}\n"
            f"- Feature Engineering: {', '.join(features.get('feature_engineering', []))}\n"
            f"- Importance Methods: {', '.join(features.get('importance_methods', []))}\n\n"
            "Key Insights:\n"
            + "\n".join(f"• {insight}" for insight in insights)
        )
