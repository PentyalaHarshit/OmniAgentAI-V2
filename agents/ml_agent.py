from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.ml_crew import MLCrew


class MLAgent(BaseAgent):
    name = "MLAgent"
    agent_type = "ML"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = MLCrew()

    def run(self, query: str):
        tasks = [
            "Detect ML task type",
            "Identify data type",
            "Extract requirements",
            "Design preprocessing pipeline",
            "Select appropriate model",
            "Design training strategy",
            "Select evaluation metrics",
            "Plan deployment strategy",
            "Provide comprehensive ML pipeline"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_ml_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_ml_answer(self, crew_result: dict):
        model = crew_result.get("model_selection", {})
        preprocessing = crew_result.get("preprocessing", {})
        training = crew_result.get("training_strategy", {})
        deployment = crew_result.get("deployment_strategy", {})
        
        return (
            "ML Agent selected.\n\n"
            f"Task Type: {crew_result.get('task_type', 'Unknown')}\n"
            f"Data Type: {crew_result.get('data_type', 'Unknown')}\n\n"
            "Preprocessing Pipeline:\n"
            "- Steps:\n"
            + "\n".join(f"  • {step}" for step in preprocessing.get("steps", []))
            + "\n\n"
            "Model Selection:\n"
            f"- Recommended: {model.get('model', 'Unknown')}\n"
            f"- Alternatives: {', '.join(model.get('alternatives', []))}\n"
            f"- Reason: {model.get('reason', 'N/A')}\n\n"
            "Training Strategy:\n"
            f"- Validation: {training.get('validation', 'Unknown')}\n"
            f"- Hyperparameter Tuning: {training.get('hyperparameter_tuning', 'Unknown')}\n"
            f"- Early Stopping: {training.get('early_stopping', 'Unknown')}\n"
            f"- Regularization: {training.get('regularization', 'Unknown')}\n\n"
            "Evaluation Metrics:\n"
            + "\n".join(f"  • {metric}" for metric in crew_result.get("evaluation_metrics", []))
            + "\n\n"
            "Deployment Strategy:\n"
            f"- Format: {deployment.get('format', 'Unknown')}\n"
            f"- Serving: {deployment.get('serving', 'Unknown')}\n"
            f"- Scaling: {deployment.get('scaling', 'Unknown')}\n"
            f"- Monitoring: {deployment.get('monitoring', 'Unknown')}"
        )
