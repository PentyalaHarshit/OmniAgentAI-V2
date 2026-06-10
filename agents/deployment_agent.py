from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.deployment_crew import DeploymentCrew


class DeploymentAgent(BaseAgent):
    name = "DeploymentAgent"
    agent_type = "Deployment"
    rag_category = "coding"
    required_fields = []
    optional_fields = []

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = DeploymentCrew()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        tasks = [
            "Detect framework and language",
            "Detect target platform",
            "Generate Dockerfile",
            "Generate docker-compose.yml",
            "Generate Kubernetes manifests (if needed)",
            "Generate CI/CD pipeline (if needed)",
            "Generate .env.example",
            "Produce run/deploy instructions",
            "Review all files for correctness",
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]

        stack = crew_result["stack"]
        fw = stack["framework"]
        app_name = stack["app_name"]
        files = crew_result["files"]
        platform = stack["platform"]

        # Build a clean, well-structured markdown answer
        parts = [
            f"**Deployment Agent** — `{app_name}` on **{platform}**\n",
            f"Detected: **{fw['name'].title()}** ({fw['lang']}) · port `{fw['port']}` · "
            f"server `{fw['server']}`\n",
        ]

        # Always show Dockerfile
        parts.append(f"### 📄 Dockerfile\n```dockerfile\n{files['Dockerfile'].strip()}\n```\n")

        # Always show docker-compose.yml
        parts.append(f"### 📄 docker-compose.yml\n```yaml\n{files['docker-compose.yml'].strip()}\n```\n")

        # K8s manifests only if generated
        if files["kubernetes_manifests"]:
            parts.append(
                f"### ☸️ Kubernetes Manifests\n```yaml\n{files['kubernetes_manifests'].strip()}\n```\n"
            )

        # CI/CD only if generated
        if files["github_actions"]:
            parts.append(
                f"### ⚙️ GitHub Actions Workflow\n```yaml\n{files['github_actions'].strip()}\n```\n"
            )

        # .env.example
        parts.append(f"### 🔐 .env.example\n```bash\n{files['.env.example'].strip()}\n```\n")

        # Run instructions
        parts.append(f"### 🚀 Deploy Commands\n{crew_result['run_instructions']}\n")

        # Reviewer notes
        issues = crew_result["reviewer"]["issues"]
        reviewer_line = "✅ " + " · ".join(issues)
        parts.append(f"### 🔍 Review\n{reviewer_line}\n")

        answer = "\n".join(parts)

        return self.response(query, thoughts + crew_thoughts, answer, {
            "slot_filling": False,
            "stack": stack,
            "files": files,
            "run_instructions": crew_result["run_instructions"],
        })
