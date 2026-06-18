class CodingAIRouter:
    def route(self, query: str, has_code: bool = False):
        q = query.lower()

        deployment_keywords = [
            "deploy", "docker", "kubernetes", "k8s",
            "ci/cd", "jenkins", "aws", "azure", "gcp"
        ]

        software_keywords = [
            "fastapi", "crud", "api", "mysql", "sqlalchemy",
            "web crawler", "crawler", "scraper", "multithreaded",
            "threading", "requests", "beautifulsoup",
            "backend", "frontend", "full stack", "project"
        ]

        review_keywords = [
            "review", "optimize", "time limit exceeded",
            "tle", "memory limit", "segmentation fault",
            "bug", "debug", "fix error"
        ]

        ai_keywords = [
            "rag", "agentic", "llm", "ollama", "chromadb",
            "pinecone", "embedding", "vector database",
            "langchain", "crewai", "autogen"
        ]

        if any(w in q for w in deployment_keywords):
            return "deployment"

        if any(w in q for w in review_keywords):
            if not has_code:
                return "need_code"
            return "code_review"

        if any(w in q for w in software_keywords):
            return "software_engineering"

        if any(w in q for w in ai_keywords):
            return "ai_architect"

        return "coding"


def route_user_query(query: str, uploaded_code: str | None = None):
    router = CodingAIRouter()
    has_code = bool(uploaded_code and uploaded_code.strip())

    coding_route = router.route(query, has_code)

    if coding_route == "need_code":
        return {
            "agent": "CodeReviewAgent / code_review",
            "status": "need_code",
            "message": "Please paste your code so I can find the bottleneck and optimize it."
        }

    if coding_route == "deployment":
        return {
            "agent": "DeploymentAgent / deployment",
            "task": query
        }

    if coding_route == "software_engineering":
        return {
            "agent": "SoftwareEngineeringAgent / coding",
            "task": query
        }

    if coding_route == "ai_architect":
        return {
            "agent": "AIArchitectAgent / ai",
            "task": query
        }

    return {
        "agent": "CodingAgent / coding",
        "task": query
    }


def detect_services(query: str):
    q = query.lower()
    services = ["fastapi-app"]

    if "ollama" in q:
        services.append("ollama")

    if "chromadb" in q or "chroma" in q:
        services.append("chromadb")

    if "mysql" in q:
        services.append("mysql")

    if "postgres" in q or "postgresql" in q:
        services.append("postgres")

    if "redis" in q:
        services.append("redis")

    return services
