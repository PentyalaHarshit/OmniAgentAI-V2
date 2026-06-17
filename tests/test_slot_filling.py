from agents.travel_agent import TravelAgent
from tools.travel_data_store import TravelDataStore


def make_travel_agent(tmp_path):
    agent = TravelAgent()
    agent.travel_store = TravelDataStore(data_dir=str(tmp_path / "travel_data"))
    agent.travel_store.ensure_ready()
    return agent


def test_travel_asks_destination():
    agent = TravelAgent()
    result = agent.run("I need trip", session_id="test_slot")
    assert result["extra"]["slot_filling"] is True
    assert "What is your departure city?" in result["answer"]


def test_trip_agent_full_booking_flow(tmp_path):
    agent = make_travel_agent(tmp_path)
    session_id = "test_trip_full_booking"

    first = agent.run("I want to travel from Dallas to New York", session_id=session_id)
    assert "What is your departure city?" in first["answer"]

    destination = agent.run("Dallas", session_id=session_id)
    assert "What is your destination city?" in destination["answer"]

    date = agent.run("New York", session_id=session_id)
    assert "What date would you like to travel?" in date["answer"]

    passengers = agent.run("June 25", session_id=session_id)
    assert "How many passengers?" in passengers["answer"]

    budget = agent.run("2", session_id=session_id)
    assert "What is your budget?" in budget["answer"]

    analysis = agent.run("$500", session_id=session_id)
    assert "Trip Analysis" in analysis["answer"]
    assert "American Airlines" in analysis["answer"]
    assert "Would you like to book this trip" in analysis["answer"]
    assert analysis["extra"]["booking"]["requires_user_confirmation"] is True

    seats = agent.run("yes", session_id=session_id)
    assert "Available Seats" in seats["answer"]
    assert "12A" in seats["answer"]

    delivery = agent.run("12A, 12B", session_id=session_id)
    assert "Payment Agent" in delivery["answer"]
    assert "Total Price: $440" in delivery["answer"]
    assert "How would you like to receive your ticket?" in delivery["answer"]

    target = agent.run("Email", session_id=session_id)
    assert "Please enter your email address." in target["answer"]

    payment = agent.run("user@example.com", session_id=session_id)
    assert "Payment required: $440" in payment["answer"]
    assert "Do you confirm payment of $440?" in payment["answer"]

    confirmed = agent.run("yes", session_id=session_id)
    assert "Payment Status: Success" in confirmed["answer"]
    assert "Booking ID: TRIP-" in confirmed["answer"]
    assert "Ticket ID: TRIP-" in confirmed["answer"]
    assert "Delivery Method: Email" in confirmed["answer"]
    assert "Status: Sent" in confirmed["answer"]
    assert confirmed["extra"]["booking"]["user_confirmed"] is True
    assert confirmed["extra"]["booking"]["payment_confirmed"] is True
    assert confirmed["extra"]["booking"]["record"]["trip"]["trip_id"] == "FLT-001"
    assert confirmed["extra"]["booking"]["record"]["delivery_method"] == "email"
    assert confirmed["extra"]["booking"]["record"]["delivery_target"] == "user@example.com"


def test_trip_agent_repeats_invalid_passenger_question():
    agent = TravelAgent()
    session_id = "test_trip_invalid_passengers"

    agent.run("I need a trip", session_id=session_id)
    agent.run("Dallas", session_id=session_id)
    agent.run("New York", session_id=session_id)
    agent.run("June 25", session_id=session_id)

    invalid = agent.run("two", session_id=session_id)
    assert "Invalid passenger count" in invalid["answer"]
    assert "How many passengers?" in invalid["answer"]
