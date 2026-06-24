# OmniAgentAI AWS EC2 Deployment

Deploy OmniAgentAI on an Ubuntu EC2 instance with FastAPI, Ollama, and ChromaDB using Docker Compose.

## 1. Create EC2 Instance

In AWS Console:

```text
EC2
Launch Instance
Ubuntu 22.04 LTS
t3.large recommended
Create or select a key pair
Launch
```

Recommended security group rules:

| Type | Port | Source |
| --- | ---: | --- |
| SSH | 22 | Your IP |
| HTTP | 80 | Anywhere |
| HTTPS | 443 | Anywhere |
| FastAPI | 8000 | Anywhere |

Do not expose Ollama port `11434` publicly. The Docker Compose setup keeps Ollama internal to the EC2 host.

## 2. Connect From Windows PowerShell

```powershell
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP
```

If Windows rejects the key permissions, run:

```powershell
icacls your-key.pem /inheritance:r
icacls your-key.pem /grant:r "$env:USERNAME:R"
```

Then try the SSH command again.

## 3. Install Docker, Compose, And Git

On the EC2 Ubuntu server:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git

sudo systemctl start docker
sudo systemctl enable docker

docker --version
docker compose version
```

Optional: allow the `ubuntu` user to run Docker without `sudo`.

```bash
sudo usermod -aG docker ubuntu
newgrp docker
```

## 4. Clone OmniAgentAI

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

Verify the required files exist:

```bash
ls Dockerfile docker-compose.yml requirements.txt app.py
```

## 5. Configure Environment

Create a local `.env` file:

```bash
cp .env.example .env
```

For Docker Compose, `docker-compose.yml` already sets:

```env
OLLAMA_BASE_URL=http://ollama:11434
CHROMA_SERVER_HOST=chromadb
CHROMA_SERVER_HTTP_PORT=8000
```

Keep secrets such as API keys only in `.env`. Do not commit `.env`.

## 6. Start Containers

```bash
docker compose up --build -d
```

Check running containers:

```bash
docker ps
```

You should see:

```text
omniagentai
ollama
chromadb
```

## 7. Pull Ollama Models

The Ollama container starts empty. Pull at least one model before asking LLM questions:

```bash
docker exec -it ollama ollama pull llama3.2:3b
```

Optional models from `.env.example`:

```bash
docker exec -it ollama ollama pull qwen2.5-coder:7b
docker exec -it ollama ollama pull mistral:7b
docker exec -it ollama ollama pull phi3:mini
```

`t3.large` is a practical starting point, but CPU inference can be slow. Use smaller models first, or move to a larger/GPU instance for heavier local LLM workloads.

## 8. View Logs

```bash
docker compose logs -f
```

For one service:

```bash
docker compose logs -f omniagentai
docker compose logs -f ollama
docker compose logs -f chromadb
```

## 9. Open The App

Health check from EC2:

```bash
curl http://localhost:8000/health
```

Open Swagger UI in your browser:

```text
http://YOUR_PUBLIC_IP:8000/docs
```

## Common Commands

Restart after a code update:

```bash
git pull
docker compose up --build -d
```

Stop services:

```bash
docker compose down
```

Check resource usage:

```bash
docker stats
```

## Persistence

Docker Compose persists runtime data in:

```text
ollama_data   Ollama models
chroma_data   ChromaDB vectors/cache
./knowledge   project knowledge files
./uploads     uploaded documents
```

Keep the EC2 EBS volume attached if you want to preserve ChromaDB and Ollama data across restarts.
