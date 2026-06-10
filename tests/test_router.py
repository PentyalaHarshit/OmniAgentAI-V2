from agents.agent_router import AgentRouter


def test_healthcare_route():
    r = AgentRouter()
    route, agent = r.route("I have chest pain and diabetes")
    assert route == "healthcare"


def test_coding_route():
    r = AgentRouter()
    route, agent = r.route("generate c++ code for dijkstra")
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
