from agents.agent_router import AgentRouter
from tools.safety_layer import SafetyLayer


def test_safety_layer_strips_checkout_form_and_requires_confirmation():
    result = {
        "answer": (
            "Order confirmed!\n"
            "---CHECKOUT_FORM---\n"
            "PRODUCT_NAME:Laptop\n"
            "---END_CHECKOUT_FORM---"
        ),
        "extra": {"checkout": {"show_checkout_form": True}},
    }

    guarded = SafetyLayer().enforce(result, query="buy laptop", route="shopping")

    assert "---CHECKOUT_FORM---" not in guarded["answer"]
    assert "Order confirmed" not in guarded["answer"]
    assert "No purchase has been made" in guarded["answer"]
    assert "No payment has been made" in guarded["answer"]
    assert guarded["extra"]["checkout"]["show_checkout_form"] is False
    assert guarded["extra"]["safety_layer"]["requires_confirmation"] is True


def test_safety_layer_blocks_booking_cancellation_and_diagnosis_claims():
    answer = "booking confirmed. cancellation confirmed. diagnosis is flu."
    result = {"answer": answer, "extra": {}}

    guarded = SafetyLayer().enforce(
        result,
        query="book appointment and cancel old booking after diagnosis",
        route="healthcare",
    )

    assert "booking confirmed" not in guarded["answer"].lower()
    assert "cancellation confirmed" not in guarded["answer"].lower()
    assert "diagnosis is" not in guarded["answer"].lower()
    assert "No booking or reservation has been confirmed" in guarded["answer"]
    assert "No booking, order, or service has been cancelled" in guarded["answer"]
    assert "This is not a medical diagnosis" in guarded["answer"]


def test_router_applies_safety_layer_to_shopping_response():
    result = AgentRouter().run("Recommend a laptop for AI and machine learning under $1500")

    assert "---CHECKOUT_FORM---" not in result["answer"]
    assert "Preferred RAM?" in result["answer"]
    assert result["extra"]["safety_layer"]["requires_confirmation"] is False
    assert result["extra"]["safety_layer"]["blocked_auto_actions"] == []


def test_safety_layer_allows_explicitly_confirmed_booking_action():
    result = {
        "answer": "Status: Confirmed\n\nBooking ID: TRIP-20260616-001\nE-ticket generated.",
        "extra": {"confirmed_actions": ["book"]},
    }

    guarded = SafetyLayer().enforce(result, query="yes", route="travel")

    assert "No booking or reservation has been confirmed" not in guarded["answer"]
    assert guarded["extra"]["safety_layer"]["requires_confirmation"] is False
