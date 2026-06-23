from agents.agent_router import AgentRouter
from agents.coding_ai_agent import CodingAIAgent


def test_healthcare_route():
    r = AgentRouter()
    route, agent = r.route("I have chest pain and diabetes")
    assert route == "healthcare"


def test_coding_route():
    r = AgentRouter()
    route, agent = r.route("generate c++ code for dijkstra")
    assert route == "coding"

    route, agent = r.route("write a python function to sort a list")
    assert route == "coding"

    route, agent = r.route("Create Segment Tree with range sum queries")
    assert route == "coding"

    route, agent = r.route("Fenwick tree for point updates and range queries")
    assert route == "coding"

    route, agent = r.route("Create Heavy Light Decomposition")
    assert route == "coding"

    route, agent = r.route("Create Heavy Light Decomposition in C++.")
    assert route == "coding"

    route, agent = r.route("Create Lowest Common Ancestor using Binary Lifting in C++.")
    assert route == "coding"

    for query in [
        "Implement graph DP in cpp",
        "HLD tree path query C++17",
        "Segment tree range max point update",
        "Create centroid decomposition for tree distance queries",
    ]:
        route, agent = r.route(query)
        assert route == "coding"


def test_shopping_route():
    r = AgentRouter()
    route, agent = r.route("buy laptop under $800")
    assert route == "shopping"


def test_router_precision_general_vs_shopping():
    r = AgentRouter()

    # Who invented the telephone? -> GeneralAgent
    route, agent = r.route("Who invented the telephone?")
    assert route == "general"

    # What is the capital of France? -> CountryAgent
    route, agent = r.route("What is the capital of France?")
    assert route == "country"

    # What is machine learning? -> GeneralAgent
    route, agent = r.route("What is machine learning?")
    assert route == "general"

    # I want to buy a phone. -> ShoppingAgent
    route, agent = r.route("I want to buy a phone.")
    assert route == "shopping"

    # Recommend a laptop under $1500. -> ShoppingAgent
    route, agent = r.route("Recommend a laptop under $1500.")
    assert route == "shopping"

    # Compare iPhone and Samsung. -> ShoppingAgent
    route, agent = r.route("Compare iPhone and Samsung.")
    assert route == "shopping"

    # What is the telephone? -> GeneralAgent
    route, agent = r.route("What is the telephone?")
    assert route == "general"

    # Programming-language facts are general knowledge, not coding tasks.
    route, agent = r.route("Who invented Python?")
    assert route == "general"

    route, agent = r.route("Who created Java?")
    assert route == "general"

    route, agent = r.route("Why did the Roman Empire fall?")
    assert route == "general"


def test_router_priority_deployment_before_general_and_coding():
    r = AgentRouter()

    route, agent = r.route("What is the best way to deploy a Python API with Docker and Nginx?")
    assert route == "deployment"

    route, agent = r.route("Create GitHub Actions for Kubernetes deployment")
    assert route == "deployment"


def test_router_priority_booking_travel_before_coding():
    r = AgentRouter()

    route, agent = r.route("Build an API to book a hotel room")
    assert route == "hotel"

    route, agent = r.route("Python script for flight ticket booking")
    assert route == "flight"


def test_router_priority_shopping_before_general():
    r = AgentRouter()

    route, agent = r.route("What is the best laptop under $1200?")
    assert route == "shopping"


def test_clear_ml_request_exits_active_loan_conversation():
    r = AgentRouter()
    session_id = "test_exit_loan_for_ml"

    first = r.run("Help me pay off my loan", session_id=session_id)
    assert first["agent"] == "LoanAgent"
    assert first["router"]["route"] == "loan"
    assert "current loan balance" in first["answer"].lower()

    followup = r.run(
        "Build a machine learning pipeline for customer churn prediction.",
        session_id=session_id,
        original_query="Build a machine learning pipeline for customer churn prediction.",
    )

    assert followup["agent"] == "MLAgent"
    assert followup["router"]["route"] == "ml"
    assert "ML Agent selected" in followup["answer"]
    assert "current loan balance" not in followup["answer"].lower()


def test_coding_ai_architecture_example_routes():
    r = AgentRouter()

    examples = [
        ("Create Dijkstra algorithm in C++", "coding", "CodingAgent"),
        ("Build FastAPI CRUD application", "coding", "CodingAgent"),
        ("Why am I getting Memory Limit Exceeded?", "debug", "DebugAgent"),
        ("Fix this segmentation fault.", "debug", "DebugAgent"),
        ("Generate edge cases for segment tree.", "test_case", "TestCaseAgent"),
        ("Solve range query problem.", "algorithm", "AlgorithmAgent"),
        ("Design YouTube architecture.", "system_design", "SystemDesignAgent"),
        ("Design WhatsApp backend.", "system_design", "SystemDesignAgent"),
        ("Deploy FastAPI using Docker.", "deployment", "DeploymentAgent"),
        ("Train house price prediction model.", "ml", "MLAgent"),
        ("Analyze customer churn dataset.", "data_science", "DataScienceAgent"),
        ("Build multi-document RAG.", "rag", "RAGAgent"),
        ("Create ML pipeline.", "mlops", "MLOpsAgent"),
        ("Design Agentic RAG platform.", "ai_architect", "AIArchitectAgent"),
    ]

    for query, expected_route, expected_agent in examples:
        route, agent = r.route(query)
        assert route == expected_route, query
        assert agent.name == expected_agent, query


def test_coding_ai_parent_routes_specific_architecture_examples():
    agent = CodingAIAgent()

    examples = [
        ("Generate edge cases for segment tree.", "TestCaseAgent"),
        ("Create ML pipeline.", "MLOpsAgent"),
        ("Design Agentic RAG platform.", "AIArchitectAgent"),
        ("Build multi-document RAG.", "RAGAgent"),
    ]

    for query, expected_agent in examples:
        _, agent_name = agent.route_to_sub_agent(query)
        assert agent_name == expected_agent, query


def test_fastapi_crud_mysql_project_code_routes_to_coding_not_deployment():
    router = AgentRouter()

    route, agent = router.route(
        "Build a FastAPI CRUD application with MySQL. "
        "Generate full project code with SQLAlchemy models, schemas, routes, "
        "database connection, requirements.txt, and run command. "
        "Do not generate Docker files unless I ask for deployment."
    )

    assert route == "coding"
    assert agent.name == "CodingAgent"


def test_multithreaded_web_crawler_routes_to_coding():
    router = AgentRouter()

    route, agent = router.route("Build a multithreaded web crawler.")

    assert route == "coding"
    assert agent.name == "CodingAgent"


def test_router_sends_sports_standings_to_sports_agent():
    router = AgentRouter()

    examples = [
        "FIFA World Cup 2026 standings",
        "IPL points table",
        "NBA standings",
        "Premier League table",
    ]

    for query in examples:
        route, agent = router.route(query)
        assert route == "sports", query
        assert agent.name == "SportsAgent", query


def test_router_sends_information_queries_to_general_agent():
    router = AgentRouter()

    examples = [
        "What is agentic AI?",
        "Explain Retrieval-Augmented Generation with examples.",
        "What is the difference between CrewAI and AutoGen?",
        "How does a vector database work?",
        "Explain quantum computing in simple terms.",
        "What causes black holes to form?",
        "How does CRISPR gene editing work?",
        "Find recent research papers on multi-agent AI systems.",
        "Summarize the latest developments in agentic RAG.",
        "Compare Tree of Thoughts and Chain of Thought reasoning.",
        "What are the latest AI model releases this month?",
        "What are the latest trends in autonomous AI agents?",
        "Summarize today's major AI news.",
        "Explain distributed systems with examples.",
        "How does Kubernetes work internally?",
        "Who invented the World Wide Web?",
        "What is the history of artificial intelligence?",
        "Explain the evolution of programming languages.",
    ]

    for query in examples:
        route, agent = router.route(query)
        assert route == "general", query
        assert agent.name == "GeneralAgent", query


def test_router_sends_learning_queries_to_learning_agent():
    router = AgentRouter()

    examples = [
        "Teach me AWS from beginner to advanced.",
        "Teach me Kubernetes",
        "Teach me Reinforcement Learning",
        "Teach me System Design",
        "Create a Kubernetes roadmap",
        "I want to learn AWS",
    ]

    for query in examples:
        route, agent = router.route(query)
        assert route == "learning", query
        assert agent.name == "LearningAgent", query
