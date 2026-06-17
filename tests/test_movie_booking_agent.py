import json

from agents.movie_agent import MovieAgent
from tools.movie_data_store import MovieDataStore


def make_movie_agent(tmp_path):
    agent = MovieAgent()
    agent.movie_store = MovieDataStore(data_dir=str(tmp_path / "movie_data"))
    agent.movie_store.ensure_ready()
    return agent


def test_movie_booking_flow_starts_with_live_movies(tmp_path):
    agent = make_movie_agent(tmp_path)

    result = agent.run("Book movie ticket", session_id="movie_live_list")

    assert "Live Movies Available Today" in result["answer"]
    assert "Mission Impossible: Final Reckoning" in result["answer"]
    assert "Please enter movie name or movie number." in result["answer"]


def test_movie_booking_full_flow_saves_ticket(tmp_path):
    agent = make_movie_agent(tmp_path)
    session_id = "movie_full_flow"

    start = agent.run("Book movie ticket", session_id=session_id)
    assert "Live Movies Available Today" in start["answer"]

    theaters = agent.run("1", session_id=session_id)
    assert "Theaters Available" in theaters["answer"]
    assert "AMC Stonebriar 24" in theaters["answer"]

    showtimes = agent.run("AMC Stonebriar 24", session_id=session_id)
    assert "Available Showtimes" in showtimes["answer"]
    assert "5:00 PM" in showtimes["answer"]

    seats = agent.run("5:00 PM", session_id=session_id)
    assert "Available Seats" in seats["answer"]
    assert "A1 A2 A3 A4" in seats["answer"]

    summary = agent.run("A1 A2", session_id=session_id)
    assert "Booking Summary" in summary["answer"]
    assert "Total Price:\n$32" in summary["answer"]
    assert "Choose delivery method." in summary["answer"]

    payment = agent.run("WhatsApp", session_id=session_id)
    assert "Do you confirm payment of $32?" in payment["answer"]

    confirmed = agent.run("yes", session_id=session_id)
    assert "Payment successful. Movie e-ticket generated and sent by Whatsapp." in confirmed["answer"]
    assert "Ticket ID: MOVIE-" in confirmed["answer"]
    assert "QR Code: QR-MOVIE-" in confirmed["answer"]
    assert confirmed["extra"]["booking"]["payment_status"] == "paid"
    assert confirmed["extra"]["booking"]["delivery_method"] == "whatsapp"

    saved = json.loads((tmp_path / "movie_data" / "bookings.json").read_text(encoding="utf-8"))
    assert saved[0]["movie_name"] == "Mission Impossible: Final Reckoning"
    assert saved[0]["amount"] == 32
    assert saved[0]["ticket_status"] == "generated"
    assert saved[0]["delivery_status"] == "sent"
