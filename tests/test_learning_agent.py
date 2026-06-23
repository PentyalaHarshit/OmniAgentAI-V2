from agents.learning_agent import LearningAgent


def test_learning_agent_generates_aws_beginner_to_advanced_roadmap():
    result = LearningAgent().run("Teach me AWS from beginner to advanced")

    assert result["agent"] == "LearningAgent"
    assert "AWS Beginner" in result["answer"]
    assert "- Cloud Computing Basics" in result["answer"]
    assert "- IAM" in result["answer"]
    assert "- EC2" in result["answer"]
    assert "- S3" in result["answer"]
    assert "AWS Intermediate" in result["answer"]
    assert "- VPC" in result["answer"]
    assert "- Lambda" in result["answer"]
    assert "AWS Advanced" in result["answer"]
    assert "- EKS" in result["answer"]
    assert "- Terraform" in result["answer"]
    assert "- Multi-region Architecture" in result["answer"]
    assert "- Security and Cost Optimization" in result["answer"]
    assert "Examples" in result["answer"]
    assert "Exercises" in result["answer"]
    assert result["extra"]["source_stage"] == "learning_roadmap"
