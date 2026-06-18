from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.mlops_crew import MLOpsCrew


class MLOpsAgent(BaseAgent):
    name = "MLOpsAgent"
    agent_type = "MLOps"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = MLOpsCrew()

    def run(self, query: str):
        tasks = [
            "Detect ML pipeline type",
            "Estimate system scale",
            "Design data pipeline",
            "Design training pipeline",
            "Design model registry",
            "Design monitoring system",
            "Design deployment strategy",
            "Design CI/CD pipeline",
            "Provide comprehensive MLOps architecture"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_mlops_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_mlops_answer(self, crew_result: dict):
        data = crew_result.get("data_pipeline", {})
        training = crew_result.get("training_pipeline", {})
        registry = crew_result.get("model_registry", {})
        monitoring = crew_result.get("monitoring", {})
        deployment = crew_result.get("deployment", {})
        cicd = crew_result.get("ci_cd", {})
        scale = crew_result.get("scale", {})
        
        return (
            "MLOps Agent selected.\n\n"
            f"Pipeline Type: {crew_result.get('pipeline_type', 'Unknown')}\n\n"
            "Scale Estimation:\n"
            f"- Models: {scale.get('models', 'Unknown')}\n"
            f"- Predictions/Second: {scale.get('predictions_per_second', 'Unknown')}\n"
            f"- Data Volume: {scale.get('data_volume', 'Unknown')}\n\n"
            "Data Pipeline:\n"
            f"- Ingestion: {', '.join(data.get('ingestion', []))}\n"
            f"- Processing: {', '.join(data.get('processing', []))}\n"
            f"- Storage: {', '.join(data.get('storage', []))}\n\n"
            "Training Pipeline:\n"
            f"- Orchestrator: {training.get('orchestrator', 'Unknown')}\n"
            f"- Compute: {', '.join(training.get('compute', []))}\n"
            f"- Hyperparameter Tuning: {', '.join(training.get('hyperparameter_tuning', []))}\n\n"
            "Model Registry:\n"
            f"- Solution: {registry.get('solution', 'Unknown')}\n"
            f"- Features: {', '.join(registry.get('features', []))}\n\n"
            "Monitoring:\n"
            f"- Performance: {', '.join(monitoring.get('performance_monitoring', []))}\n"
            f"- Data Drift: {', '.join(monitoring.get('data_drift', []))}\n"
            f"- Alerting: {', '.join(monitoring.get('alerting', []))}\n\n"
            "Deployment:\n"
            f"- Serving: {', '.join(deployment.get('serving', []))}\n"
            f"- Packaging: {', '.join(deployment.get('packaging', []))}\n"
            f"- Scaling: {', '.join(deployment.get('scaling', []))}\n\n"
            "CI/CD Pipeline:\n"
            f"- Tools: {', '.join(cicd.get('tools', []))}\n"
            f"- Stages: {len(cicd.get('stages', []))} stages"
        )
