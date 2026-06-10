from agents.travel_agent import TravelAgent


def test_travel_asks_destination():
    agent = TravelAgent()
    result = agent.run("I need trip", session_id="test_slot")
    assert result["extra"]["slot_filling"] is True
    assert "Which place" in result["answer"]
