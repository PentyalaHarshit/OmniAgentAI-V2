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

    # Use detect_services to determine services - only add PostgreSQL/Redis if explicitly requested
    services = detect_services(query)
    database = "postgres" if "postgres" in services else ("mysql" if "mysql" in services else None)

    return {"framework": fw_info, "platform": platform, "app_name": app_name, "database": database, "services": services}


def is_crud_app_request(query: str) -> bool:
    q = query.lower()
    return (
        any(term in q for term in ("crud", "rest api", "api application", "web application"))
        and any(term in q for term in ("fastapi", "flask", "django", "express", "spring boot"))
    )


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


def gen_compose(fw: dict, app_name: str, database: str = "postgres") -> str:
    port = fw["port"]
    lang = fw["lang"]
    db_service = ""
    db_env = ""
    if lang == "python":
        if database == "mysql":
            db_service = """
  db:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      MYSQL_USER: ${DB_USER:-user}
      MYSQL_PASSWORD: ${DB_PASSWORD:-password}
      MYSQL_DATABASE: ${DB_NAME:-appdb}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:-root-password}
    command: --default-authentication-plugin=mysql_native_password
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
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
      - DB_URL=mysql+pymysql://${DB_USER:-user}:${DB_PASSWORD:-password}@db:3306/${DB_NAME:-appdb}
      - REDIS_URL=redis://redis:6379"""
        else:
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
        volume_name = "mysql_data" if database == "mysql" else "postgres_data"
        volumes = f"""
volumes:
  {volume_name}:
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


def gen_nginx(fw: dict, app_name: str) -> str:
    port = fw["port"]
    return f"""# nginx/{app_name}.conf
server {{
    listen 80;
    server_name _;

    client_max_body_size 25m;

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300;
    }}

    location /health {{
        proxy_pass http://127.0.0.1:{port}/health;
        access_log off;
    }}
}}
"""


def gen_aws_ec2(fw: dict, app_name: str) -> str:
    port = fw["port"]
    return f"""# aws/ec2-user-data.sh
#!/usr/bin/env bash
set -euo pipefail

APP_NAME="{app_name}"
APP_DIR="/opt/${{APP_NAME}}"

apt-get update -y
apt-get install -y ca-certificates curl git nginx

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker
systemctl enable --now nginx

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Replace this with your repo URL or copy files onto the instance.
# git clone https://github.com/your-org/{app_name}.git .

cat >/etc/nginx/sites-available/$APP_NAME <<'NGINX'
server {{
    listen 80;
    server_name _;

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /health {{
        proxy_pass http://127.0.0.1:{port}/health;
        access_log off;
    }}
}}
NGINX

ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/$APP_NAME
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if [ -f docker-compose.yml ]; then
  docker compose up --build -d
fi
"""


def gen_env_example(fw: dict, app_name: str, database: str = "postgres") -> str:
    lang = fw["lang"]
    base = f"""# ── .env.example ──────────────────────────────────────────────────────
# Copy to .env and fill in your values — never commit .env to git!

ENV=production
APP_PORT={fw['port']}
SECRET_KEY=change-me-to-a-random-secret
"""
    if lang == "python":
        if database == "mysql":
            base += """
# Database
DB_USER=user
DB_PASSWORD=password
DB_ROOT_PASSWORD=root-password
DB_NAME=appdb
DB_URL=mysql+pymysql://user:password@db:3306/appdb

# Redis
REDIS_URL=redis://redis:6379

# External APIs
OPENAI_API_KEY=sk-...
"""
        else:
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


def gen_fastapi_crud_files(database: str = "postgres") -> dict:
    db_url = (
        "mysql+pymysql://user:password@localhost:3306/appdb"
        if database == "mysql"
        else "postgresql://user:password@localhost:5432/appdb"
    )
    return {
        "requirements.txt": """fastapi==0.115.6
uvicorn[standard]==0.34.0
SQLAlchemy==2.0.36
pydantic==2.10.4
python-dotenv==1.0.1
PyMySQL==1.1.1
cryptography==44.0.0
""",
        "app/database.py": f"""import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DB_URL", "{db_url}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
        "app/models.py": """from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
""",
        "app/schemas.py": """from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ItemRead(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
""",
        "app/main.py": """from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI CRUD with MySQL")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/items", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    item = models.Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/items", response_model=list[schemas.ItemRead])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Item).offset(skip).limit(limit).all()


@app.get("/items/{item_id}", response_model=schemas.ItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{item_id}", response_model=schemas.ItemRead)
def update_item(item_id: int, payload: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return None
""",
    }


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

    elif platform == "aws":
        lines += [
            "## AWS EC2 Prerequisites",
            "- Ubuntu 22.04 EC2 instance",
            "- Security group allows inbound ports 22, 80, and 443",
            "- SSH key pair for the instance",
            "- Optional: DNS A record pointing to the EC2 public IP",
            "",
            "## Steps",
            "```bash",
            "# 1. SSH into the instance",
            "ssh -i path/to/key.pem ubuntu@EC2_PUBLIC_IP",
            "",
            "# 2. Install Docker, Docker Compose, and Nginx",
            "sudo bash aws/ec2-user-data.sh",
            "",
            "# 3. Copy project files or clone your repo",
            f"cd /opt/{app_name}",
            "cp .env.example .env",
            "# Edit .env with production values",
            "",
            "# 4. Start containers",
            "docker compose up --build -d",
            "",
            "# 5. Validate and reload Nginx",
            "sudo nginx -t && sudo systemctl reload nginx",
            "```",
        ]

    return "\n".join(lines)


# ── DeploymentCrew ─────────────────────────────────────────────────────────

class DeploymentCrew:
    def __init__(self):
        self.rag = RAGTool()

    def run(self, query: str) -> dict:
        steps = []
        q = query.lower()

        # Agent 1: RAG
        rag = self.rag.search(query, "coding")
        steps.append({"thought": "RAG Agent: retrieve deployment knowledge", "output": rag})

        # Agent 2: Stack & platform detection
        stack = detect_stack(query)
        if any(kw in q for kw in ("aws", "ec2", "elastic compute")):
            stack["platform"] = "aws"
        fw = stack["framework"]
        platform = stack["platform"]
        app_name = stack["app_name"]
        database = stack.get("database", "postgres")
        steps.append({
            "thought": f"StackDetectorAgent: framework={fw['name']}, lang={fw['lang']}, "
                       f"platform={platform}, app={app_name}, database={database}",
            "output": stack
        })

        # Agent 3: Dockerfile
        dockerfile = gen_dockerfile(fw, app_name)
        steps.append({"thought": "DockerfileAgent: generate Dockerfile", "output": "generated"})

        # Agent 4: Compose (always include — most useful)
        compose = gen_compose(fw, app_name, database)
        steps.append({"thought": "ComposeAgent: generate docker-compose.yml", "output": "generated"})

        # Agent 5: K8s manifests (only if requested)
        k8s = ""
        if platform == "kubernetes" or any(kw in q for kw in ("kubernetes", "k8s", "kubectl", "helm")):
            k8s = gen_k8s(fw, app_name)
            steps.append({"thought": "K8sAgent: generate Kubernetes manifests", "output": "generated"})

        # Agent 6: CI/CD (if requested or useful for AWS image deploys)
        cicd = ""
        if platform in ("github_actions", "aws") or any(kw in q for kw in ("github actions", "ci/cd")):
            cicd = gen_github_actions(fw, app_name)
            steps.append({"thought": "CIAgent: generate GitHub Actions workflow", "output": "generated"})

        # Agent 7: Nginx reverse proxy (if requested or needed by AWS EC2)
        nginx = ""
        if platform == "aws" or "nginx" in q or "ec2" in q:
            nginx = gen_nginx(fw, app_name)
            steps.append({"thought": "NginxAgent: generate Nginx reverse proxy config", "output": "generated"})

        # Agent 8: AWS EC2 bootstrap (only if requested)
        aws_ec2 = ""
        if platform == "aws" or any(kw in q for kw in ("aws", "ec2", "elastic compute")):
            aws_ec2 = gen_aws_ec2(fw, app_name)
            steps.append({"thought": "AWSAgent: generate EC2 user-data bootstrap script", "output": "generated"})

        # Agent 9: .env.example
        env_example = gen_env_example(fw, app_name, database)
        steps.append({"thought": "EnvAgent: generate .env.example", "output": "generated"})

        source_files = {}
        if fw["name"] == "fastapi" and is_crud_app_request(query):
            source_files = gen_fastapi_crud_files(database)
            steps.append({"thought": "AppScaffoldAgent: generate FastAPI CRUD source files", "output": "generated"})

        # Agent 10: Run instructions
        run_instructions = gen_run_instructions(fw, app_name, platform)
        steps.append({"thought": "RunInstructionsAgent: generate deploy commands", "output": "generated"})

        # Agent 11: Reviewer
        issues = []
        if "EXPOSE" not in dockerfile:
            issues.append("Dockerfile missing EXPOSE")
        if "healthcheck" not in compose.lower():
            issues.append("docker-compose.yml missing healthcheck")
        if platform == "aws" and "docker compose up" not in aws_ec2:
            issues.append("AWS EC2 script missing docker compose startup")
        if nginx and "proxy_pass" not in nginx:
            issues.append("Nginx config missing proxy_pass")
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
                "nginx.conf": nginx,
                "aws_ec2_user_data": aws_ec2,
                ".env.example": env_example,
                **source_files,
            },
            "run_instructions": run_instructions,
            "reviewer": {"issues": issues or ["All files look good ✓"]},
        }
