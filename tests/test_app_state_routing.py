from fastapi.testclient import TestClient

from app import app, conversation_state


def test_clear_travel_request_exits_healthcare_slot_selection():
    session_id = "test_exit_healthcare_for_travel"
    conversation_state.set(session_id, {
        "active_agent": "HealthcareAgent",
        "flow": "healthcare_slot_selection",
        "missing_fields": ["slot_selection"],
        "fields": {"slot_selection": "not provided"},
    })

    client = TestClient(app)
    response = client.post("/ask", json={
        "session_id": session_id,
        "query": "I want to travel from Dallas to New York",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["agent_result"]["router"]["route"] == "travel"
    assert data["agent_result"]["agent"] == "TravelAgent"
    assert "TripAgent / travel" in data["final_answer"]
    assert "What is your departure city?" in data["final_answer"]
