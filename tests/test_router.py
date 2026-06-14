from agents.agent_router import AgentRouter


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


def test_shopping_route():
    r = AgentRouter()
    route, agent = r.route("buy laptop under $800")
    assert route == "shopping"


def test_router_precision_general_vs_shopping():
    r = AgentRouter()

    # Who invented the telephone? -> GeneralAgent
    route, agent = r.route("Who invented the telephone?")
    assert route == "general"

    # What is the capital of France? -> GeneralAgent
    route, agent = r.route("What is the capital of France?")
    assert route == "general"

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
