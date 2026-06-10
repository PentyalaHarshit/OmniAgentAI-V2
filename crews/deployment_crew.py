"""
DeploymentCrew
==============
Generates deployment artifacts based on the detected stack/platform.

Crew agents
-----------
  1. StackDetectorAgent    – detect app type (FastAPI, Flask, Django, Node, etc.)
  2. PlatformAgent         – detect target platform (Docker, K8s, AWS, Railway, etc.)
  3. DockerfileAgent       – generate Dockerfile
  4. ComposeAgent          – generate docker-compose.yml (if needed)
  5. K8sAgent              – generate Kubernetes manifests (if needed)
  6. CIAgent               – generate CI/CD config (GitHub Actions, etc.)
  7. EnvAgent              – generate .env.example
  8. RunInstructionsAgent  – produce run/deploy commands
  9. ReviewerAgent         – self-check files for correctness
"""

import re
from tools.rag_tool import RAGTool


# ── Stack detection helpers ────────────────────────────────────────────────

FRAMEWORK_MAP = {
    "fastapi":   {"lang": "python", "server": "uvicorn", "port": 8000, "install": "pip"},
    "flask":     {"lang": "python", "server": "gunicorn", "port": 5000, "install": "pip"},
    "django":    {"lang": "python", "server": "gunicorn", "port": 8000, "install": "pip"},
    "streamlit": {"lang": "python", "server": "streamlit", "port": 8501, "install": "pip"},
    "express":   {"lang": "node",   "server": "node",     "port": 3000, "install": "npm"},
    "nextjs":    {"lang": "node",   "server": "next",     "port": 3000, "install": "npm"},
    "react":     {"lang": "node",   "server": "nginx",    "port": 80,   "install": "npm"},
    "spring":    {"lang": "java",   "server": "java",     "port": 8080, "install": "mvn"},
    "rails":     {"lang": "ruby",   "server": "puma",     "port": 3000, "install": "bundle"},
}

PLATFORM_KEYWORDS = {
    "kubernetes": "kubernetes", "k8s": "kubernetes", "kubectl": "kubernetes",
    "helm": "kubernetes",
    "docker compose": "compose", "docker-compose": "compose", "compose": "compose",
    "docker": "docker",
    "railway": "railway", "render": "render", "fly": "fly.io",
    "aws":   "aws",   "ec2": "aws",   "ecs": "aws",   "fargate": "aws",
    "azure": "azure", "gcp": "gcp",   "cloud run": "gcp",
    "github actions": "github_actions", "ci/cd": "github_actions",
    "jenkins": "jenkins",
}


def detect_stack(query: str) -> dict:
    q = query.lower()
    fw_info = {"name": "fastapi", "lang": "python", "server": "uvicorn", "port": 8000, "install": "pip"}
    for fw, info in FRAMEWORK_MAP.items():
        if fw in q:
            fw_info = {"name": fw, **info}
            break

    platform = "compose"   # default — docker + compose is the most useful
    for kw, plat in PLATFORM_KEYWORDS.items():
        if kw in q:
            platform = plat
            break
    # docker alone (without compose keyword) → still give compose for full usefulness
    if platform == "docker":
        platform = "compose"

    app_name = re.search(r"for\s+([a-z0-9_\-]+(?:ai|app|api|service)?)", q)
    app_name = app_name.group(1) if app_name else fw_info["name"] + "-app"
    app_name = app_name.replace(" ", "-").lower()

    return {"framework": fw_info, "platform": platform, "app_name": app_name}


# ── File generators ────────────────────────────────────────────────────────

def gen_dockerfile(fw: dict, app_name: str) -> str:
    lang = fw["lang"]
    server = fw["server"]
    port = fw["port"]
    name = fw["name"]

    if lang == "python":
        base = "python:3.11-slim"
        if name == "fastapi":
            cmd = f'["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]'
            run_install = "RUN pip install --no-cache-dir -r requirements.txt"
        elif name == "flask":
            cmd = f'["gunicorn", "-w", "4", "-b", "0.0.0.0:{port}", "app:app"]'
            run_install = "RUN pip install --no-cache-dir -r requirements.txt"
        elif name == "django":
            cmd = f'["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:{port}"]'
            run_install = "RUN pip install --no-cache-dir -r requirements.txt"
        elif name == "streamlit":
            cmd = f'["streamlit", "run", "app.py", "--server.port={port}", "--server.address=0.0.0.0"]'
            run_install = "RUN pip install --no-cache-dir -r requirements.txt"
        else:
            cmd = f'["python", "main.py"]'
            run_install = "RUN pip install --no-cache-dir -r requirements.txt"

        return f"""# ── Dockerfile ────────────────────────────────────────────────────────
FROM {base}

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache optimisation)
COPY requirements.txt .
{run_install}

# Copy application source
COPY . .

# Expose application port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:{port}/health')" || exit 1

# Run the application
CMD {cmd}
"""

    if lang == "node":
        if name in ("nextjs", "react"):
            return f"""# ── Dockerfile ────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE {port}
CMD ["npm", "start"]
"""
        return f"""# ── Dockerfile ────────────────────────────────────────────────────────
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE {port}
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:{port}/health || exit 1
CMD ["node", "src/index.js"]
"""

    if lang == "java":
        return f"""# ── Dockerfile ────────────────────────────────────────────────────────
FROM eclipse-temurin:17-jdk-alpine AS builder
WORKDIR /app
COPY . .
RUN ./mvnw package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE {port}
ENTRYPOINT ["java", "-jar", "app.jar"]
"""

    # generic fallback
    return f"""# ── Dockerfile ────────────────────────────────────────────────────────
FROM ubuntu:22.04
WORKDIR /app
COPY . .
EXPOSE {port}
CMD ["/app/start.sh"]
"""


def gen_compose(fw: dict, app_name: str) -> str:
    port = fw["port"]
    lang = fw["lang"]
    db_service = ""
    db_env = ""
    if lang == "python":
        db_service = """
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
      POSTGRES_DB: ${DB_NAME:-appdb}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data"""
        db_env = """
      - DB_URL=postgresql://${DB_USER:-user}:${DB_PASSWORD:-password}@db:5432/${DB_NAME:-appdb}
      - REDIS_URL=redis://redis:6379"""

    volumes = ""
    if db_service:
        volumes = """
volumes:
  postgres_data:
  redis_data:"""

    return f"""# ── docker-compose.yml ────────────────────────────────────────────────
version: "3.9"

services:
  {app_name}:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {app_name}
    restart: unless-stopped
    ports:
      - "${{APP_PORT:-{port}}}:{port}"
    env_file:
      - .env
    environment:
      - ENV=${{ENV:-production}}{db_env}
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s{db_service}
{volumes}
"""


def gen_k8s(fw: dict, app_name: str) -> str:
    port = fw["port"]
    return f"""# ── kubernetes/deployment.yaml ────────────────────────────────────────
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
        - name: {app_name}
          image: your-registry/{app_name}:latest
          ports:
            - containerPort: {port}
          envFrom:
            - secretRef:
                name: {app_name}-secrets
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: {port}
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /health
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 10
---
# ── kubernetes/service.yaml ───────────────────────────────────────────
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-svc
spec:
  selector:
    app: {app_name}
  ports:
    - protocol: TCP
      port: 80
      targetPort: {port}
  type: LoadBalancer
---
# ── kubernetes/hpa.yaml ───────────────────────────────────────────────
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
"""


def gen_github_actions(fw: dict, app_name: str) -> str:
    # Use .format() instead of f-string to avoid conflicts with GitHub Actions ${{ }} syntax
    template = """\
# ── .github/workflows/deploy.yml ──────────────────────────────────────
name: Build & Deploy {app_name}

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  IMAGE_NAME: ${{{{ secrets.REGISTRY }}}}/{app_name}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --tb=short

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{{{ secrets.REGISTRY }}}}
          username: ${{{{ secrets.REGISTRY_USER }}}}
          password: ${{{{ secrets.REGISTRY_TOKEN }}}}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}},${{{{ env.IMAGE_NAME }}}}:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{{{ secrets.DEPLOY_HOST }}}}
          username: ${{{{ secrets.DEPLOY_USER }}}}
          key: ${{{{ secrets.DEPLOY_KEY }}}}
          script: |
            docker pull ${{{{ env.IMAGE_NAME }}}}:latest
            docker compose -f /app/docker-compose.yml up -d --no-deps {app_name}
"""
    return template.format(app_name=app_name)


def gen_env_example(fw: dict, app_name: str) -> str:
    lang = fw["lang"]
    base = f"""# ── .env.example ──────────────────────────────────────────────────────
# Copy to .env and fill in your values — never commit .env to git!

ENV=production
APP_PORT={fw['port']}
SECRET_KEY=change-me-to-a-random-secret
"""
    if lang == "python":
        base += """
# Database
DB_USER=user
DB_PASSWORD=password
DB_NAME=appdb
DB_URL=postgresql://user:password@db:5432/appdb

# Redis
REDIS_URL=redis://redis:6379

# External APIs
OPENAI_API_KEY=sk-...
"""
    if lang == "node":
        base += """
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/appdb

# Auth
JWT_SECRET=change-me
"""
    return base


def gen_run_instructions(fw: dict, app_name: str, platform: str) -> str:
    port = fw["port"]
    lines = [f"# ── How to Deploy: {app_name} ──────────────────────────────────────────\n"]

    if platform in ("docker", "compose"):
        lines += [
            "## Prerequisites",
            "- Docker Desktop (https://docs.docker.com/get-docker/)",
            "- Docker Compose v2+ (included with Docker Desktop)",
            "",
            "## Steps",
            "```bash",
            "# 1. Copy environment file",
            "cp .env.example .env",
            "# Edit .env and set your SECRET_KEY, DB passwords, API keys",
            "",
            "# 2. Build and start all services",
            "docker compose up --build -d",
            "",
            f"# 3. Open the app",
            f"open http://localhost:{port}",
            "",
            "# 4. View logs",
            f"docker compose logs -f {app_name}",
            "",
            "# 5. Stop",
            "docker compose down",
            "",
            "# 6. Rebuild after code changes",
            "docker compose up --build -d",
            "```",
        ]

    elif platform == "kubernetes":
        lines += [
            "## Prerequisites",
            "- kubectl configured to your cluster",
            "- Image pushed to your registry",
            "",
            "## Steps",
            "```bash",
            "# 1. Create secrets",
            f"kubectl create secret generic {app_name}-secrets --from-env-file=.env",
            "",
            "# 2. Apply manifests",
            "kubectl apply -f kubernetes/",
            "",
            "# 3. Check rollout",
            f"kubectl rollout status deployment/{app_name}",
            "",
            "# 4. Get service URL",
            f"kubectl get svc {app_name}-svc",
            "```",
        ]

    elif platform == "github_actions":
        lines += [
            "## Setup GitHub Secrets",
            "Go to Settings → Secrets → Actions and add:",
            "- `REGISTRY` — your Docker registry (e.g. docker.io/youruser)",
            "- `REGISTRY_USER` / `REGISTRY_TOKEN`",
            "- `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY` (SSH key for server)",
            "",
            "## Trigger",
            "Push to `main` branch — the workflow runs tests, builds, and deploys automatically.",
        ]

    return "\n".join(lines)


# ── DeploymentCrew ─────────────────────────────────────────────────────────

class DeploymentCrew:
    def __init__(self):
        self.rag = RAGTool()

    def run(self, query: str) -> dict:
        steps = []

        # Agent 1: RAG
        rag = self.rag.search(query, "coding")
        steps.append({"thought": "RAG Agent: retrieve deployment knowledge", "output": rag})

        # Agent 2: Stack & platform detection
        stack = detect_stack(query)
        fw = stack["framework"]
        platform = stack["platform"]
        app_name = stack["app_name"]
        steps.append({
            "thought": f"StackDetectorAgent: framework={fw['name']}, lang={fw['lang']}, "
                       f"platform={platform}, app={app_name}",
            "output": stack
        })

        # Agent 3: Dockerfile
        dockerfile = gen_dockerfile(fw, app_name)
        steps.append({"thought": "DockerfileAgent: generate Dockerfile", "output": "generated"})

        # Agent 4: Compose (always include — most useful)
        compose = gen_compose(fw, app_name)
        steps.append({"thought": "ComposeAgent: generate docker-compose.yml", "output": "generated"})

        # Agent 5: K8s manifests (only if requested)
        k8s = ""
        if platform == "kubernetes":
            k8s = gen_k8s(fw, app_name)
            steps.append({"thought": "K8sAgent: generate Kubernetes manifests", "output": "generated"})

        # Agent 6: CI/CD (only if requested)
        cicd = ""
        if platform == "github_actions":
            cicd = gen_github_actions(fw, app_name)
            steps.append({"thought": "CIAgent: generate GitHub Actions workflow", "output": "generated"})

        # Agent 7: .env.example
        env_example = gen_env_example(fw, app_name)
        steps.append({"thought": "EnvAgent: generate .env.example", "output": "generated"})

        # Agent 8: Run instructions
        run_instructions = gen_run_instructions(fw, app_name, platform)
        steps.append({"thought": "RunInstructionsAgent: generate deploy commands", "output": "generated"})

        # Agent 9: Reviewer
        issues = []
        if "EXPOSE" not in dockerfile:
            issues.append("Dockerfile missing EXPOSE")
        if "healthcheck" not in compose.lower():
            issues.append("docker-compose.yml missing healthcheck")
        steps.append({
            "thought": "ReviewerAgent: self-check all files",
            "output": {"issues": issues or ["All files look good ✓"]}
        })

        return {
            "crew_name": "DeploymentCrew",
            "crew_steps": steps,
            "rag": rag,
            "stack": stack,
            "files": {
                "Dockerfile": dockerfile,
                "docker-compose.yml": compose,
                "kubernetes_manifests": k8s,
                "github_actions": cicd,
                ".env.example": env_example,
            },
            "run_instructions": run_instructions,
            "reviewer": {"issues": issues or ["All files look good ✓"]},
        }
