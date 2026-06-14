from agents.deployment_agent import DeploymentAgent
from crews.deployment_crew import DeploymentCrew


def test_deployment_crew_generates_aws_ec2_nginx_and_github_actions():
    result = DeploymentCrew().run("Deploy FastAPI to AWS EC2 with Docker, Nginx, and GitHub Actions")
    files = result["files"]

    assert result["stack"]["platform"] == "aws"
    assert "docker compose up --build -d" in files["aws_ec2_user_data"]
    assert "apt-get install -y ca-certificates curl git nginx" in files["aws_ec2_user_data"]
    assert "proxy_pass http://127.0.0.1:8000" in files["nginx.conf"]
    assert "docker/build-push-action" in files["github_actions"]
    assert "AWS EC2 Prerequisites" in result["run_instructions"]


def test_deployment_crew_generates_kubernetes_when_requested():
    result = DeploymentCrew().run("Create Kubernetes deployment for FastAPI")
    files = result["files"]

    assert result["stack"]["platform"] == "kubernetes"
    assert "kind: Deployment" in files["kubernetes_manifests"]
    assert "kind: Service" in files["kubernetes_manifests"]
    assert "kubectl apply -f kubernetes/" in result["run_instructions"]


def test_deployment_crew_combined_request_includes_all_requested_artifacts():
    result = DeploymentCrew().run(
        "Deploy FastAPI for omniagentai on AWS EC2 with Docker, GitHub Actions, Nginx, and Kubernetes"
    )
    files = result["files"]

    assert files["Dockerfile"]
    assert files["docker-compose.yml"]
    assert files["aws_ec2_user_data"]
    assert files["github_actions"]
    assert files["nginx.conf"]
    assert files["kubernetes_manifests"]


def test_deployment_agent_renders_aws_and_nginx_sections():
    result = DeploymentAgent().run("Deploy FastAPI to AWS EC2 with Nginx")

    assert "AWS EC2 User Data" in result["answer"]
    assert "Nginx Reverse Proxy" in result["answer"]
    assert result["extra"]["files"]["aws_ec2_user_data"]
    assert result["extra"]["files"]["nginx.conf"]
