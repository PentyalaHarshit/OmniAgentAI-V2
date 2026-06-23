import re

from agents.base_agent import BaseAgent


class LearningAgent(BaseAgent):
    name = "LearningAgent"
    agent_type = "Learning"
    base_tasks = [
        "Detect learning goal",
        "Generate roadmap",
        "Generate concepts",
        "Generate examples",
        "Generate exercises",
    ]

    TOPIC_ROADMAPS = {
        "aws": {
            "title": "AWS",
            "beginner": ["Cloud Computing Basics", "IAM", "EC2", "S3"],
            "intermediate": ["VPC", "RDS", "Lambda", "API Gateway", "CloudWatch"],
            "advanced": [
                "EKS", "ECS", "EventBridge", "Step Functions", "Terraform",
                "CI/CD", "Multi-region Architecture", "Security and Cost Optimization",
            ],
            "examples": [
                "Host a static website on S3 with CloudFront.",
                "Deploy a small API on Lambda behind API Gateway.",
                "Run a containerized service on ECS or EKS.",
            ],
            "exercises": [
                "Create an IAM user/role with least-privilege permissions.",
                "Launch an EC2 instance and connect to it securely.",
                "Design a multi-region architecture for a simple web app.",
            ],
        },
        "kubernetes": {
            "title": "Kubernetes",
            "beginner": ["Containers", "Pods", "Deployments", "Services", "kubectl"],
            "intermediate": ["ConfigMaps", "Secrets", "Ingress", "Storage", "Helm"],
            "advanced": [
                "Autoscaling", "Networking internals", "RBAC", "Operators",
                "Observability", "Security hardening", "Multi-cluster patterns",
            ],
            "examples": [
                "Deploy an Nginx app with a Service.",
                "Expose an API through Ingress.",
                "Package a microservice with Helm.",
            ],
            "exercises": [
                "Create a Deployment and scale it from 1 to 3 replicas.",
                "Add a ConfigMap and Secret to an app.",
                "Debug a crashing pod using logs and events.",
            ],
        },
        "reinforcement learning": {
            "title": "Reinforcement Learning",
            "beginner": ["Agents", "Environments", "Rewards", "Policies", "Value functions"],
            "intermediate": ["Q-learning", "Policy gradients", "Exploration", "Gymnasium environments"],
            "advanced": ["Actor-Critic", "PPO", "DQN", "Reward shaping", "Offline RL", "Multi-agent RL"],
            "examples": [
                "Train an agent to solve CartPole.",
                "Use Q-learning on a grid world.",
                "Compare random, greedy, and epsilon-greedy policies.",
            ],
            "exercises": [
                "Implement a tiny grid-world environment.",
                "Plot reward over training episodes.",
                "Tune exploration rate and compare outcomes.",
            ],
        },
        "system design": {
            "title": "System Design",
            "beginner": ["Client-server basics", "HTTP APIs", "Databases", "Caching", "Load balancers"],
            "intermediate": ["Queues", "Sharding", "Replication", "CDNs", "Rate limiting", "Observability"],
            "advanced": [
                "Distributed consensus", "Event-driven architecture", "Multi-region systems",
                "Fault tolerance", "Capacity planning", "Security and cost tradeoffs",
            ],
            "examples": [
                "Design a URL shortener.",
                "Design a chat system.",
                "Design a video feed or notification system.",
            ],
            "exercises": [
                "Estimate traffic, storage, and bandwidth for a simple service.",
                "Draw read/write flows and identify bottlenecks.",
                "Add failure handling for database or region outages.",
            ],
        },
    }

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        thoughts = self.tot.create_thoughts(self.agent_type, query, self.base_tasks)
        topic_key = self.detect_topic(query)
        roadmap = self.TOPIC_ROADMAPS.get(topic_key) or self.generic_roadmap(query)
        answer = self.format_roadmap(roadmap)
        return self.response(query, thoughts + [
            f"LearningAgent: selected roadmap topic = {roadmap['title']}.",
            "LearningAgent: generated concepts, examples, and exercises.",
        ], answer, {
            "slot_filling": False,
            "source_stage": "learning_roadmap",
            "topic": roadmap["title"],
        })

    def detect_topic(self, query: str) -> str:
        q = query.lower()
        for topic in self.TOPIC_ROADMAPS:
            if topic in q:
                return topic
        if re.search(r"\baws|amazon web services\b", q):
            return "aws"
        return ""

    @staticmethod
    def generic_roadmap(query: str) -> dict:
        topic = re.sub(
            r"\b(teach me|explain|tutorial|learn|course|roadmap|from beginner to advanced)\b",
            "",
            query,
            flags=re.I,
        )
        topic = re.sub(r"\s+", " ", topic).strip(" ?.") or "the topic"
        title = topic[:1].upper() + topic[1:]
        return {
            "title": title,
            "beginner": ["Core vocabulary", "Mental models", "Basic workflow", "Common tools"],
            "intermediate": ["Architecture", "Patterns", "Tradeoffs", "Debugging and observability"],
            "advanced": ["Scaling", "Security", "Automation", "Performance", "Real-world design"],
            "examples": [
                f"Build a small project using {topic}.",
                f"Explain a real-world use case for {topic}.",
                f"Compare two common approaches in {topic}.",
            ],
            "exercises": [
                "Create flashcards for the core concepts.",
                "Build one small hands-on example.",
                "Write a short design note explaining tradeoffs.",
            ],
        }

    @staticmethod
    def format_roadmap(roadmap: dict) -> str:
        title = roadmap["title"]
        lines = [f"{title} Beginner"]
        lines.extend(f"- {item}" for item in roadmap["beginner"])
        lines += ["", f"{title} Intermediate"]
        lines.extend(f"- {item}" for item in roadmap["intermediate"])
        lines += ["", f"{title} Advanced"]
        lines.extend(f"- {item}" for item in roadmap["advanced"])
        lines += ["", "Examples"]
        lines.extend(f"- {item}" for item in roadmap["examples"])
        lines += ["", "Exercises"]
        lines.extend(f"- {item}" for item in roadmap["exercises"])
        return "\n".join(lines)
