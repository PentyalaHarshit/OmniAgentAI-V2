import json

from agents.shopping_agent import ShoppingAgent
from tools.shopping_data_store import ShoppingDataStore


def make_shopping_agent(tmp_path):
    agent = ShoppingAgent()
    agent.shopping_store = ShoppingDataStore(data_dir=str(tmp_path / "shopping_data"))
    agent.shopping_store.ensure_ready()
    return agent


def test_shopping_agent_asks_requirements_then_recommends_and_orders(tmp_path):
    agent = make_shopping_agent(tmp_path)
    session_id = "shopping_laptop_flow"

    use_case = agent.run("I want a laptop under $1200.", session_id=session_id)
    assert "What will you use it for?" in use_case["answer"]

    ram = agent.run("AI/ML", session_id=session_id)
    assert "Preferred RAM?" in ram["answer"]

    brand = agent.run("32GB", session_id=session_id)
    assert "Preferred Brand?" in brand["answer"]

    recommendations = agent.run("Any", session_id=session_id)
    assert "Top Recommendations" in recommendations["answer"]
    assert "Lenovo Legion 5" in recommendations["answer"]
    assert "Add Lenovo Legion 5 to cart?" in recommendations["answer"]

    payment = agent.run("yes", session_id=session_id)
    assert "Do you confirm payment of $1199?" in payment["answer"]

    confirmed = agent.run("yes", session_id=session_id)
    assert "Payment Status: Success" in confirmed["answer"]
    assert "Order ID: SHOP-" in confirmed["answer"]
    assert confirmed["extra"]["order"]["product_name"] == "Lenovo Legion 5"
    assert confirmed["extra"]["order"]["payment_status"] == "paid"

    saved = json.loads((tmp_path / "shopping_data" / "orders.json").read_text(encoding="utf-8"))
    assert saved[0]["product_name"] == "Lenovo Legion 5"
    assert saved[0]["order_status"] == "confirmed"


def test_shopping_agent_direct_smart_query_recommends_top_options(tmp_path):
    agent = make_shopping_agent(tmp_path)

    result = agent.run(
        "I want a laptop for machine learning. Budget: $1200 RAM: 32GB Brand: Any",
        session_id="shopping_direct_query",
    )

    assert "Top Recommendations" in result["answer"]
    assert "Lenovo Legion 5" in result["answer"]
    assert "ASUS TUF A15" in result["answer"]
    assert "Recommended:\nLenovo Legion 5" in result["answer"]
