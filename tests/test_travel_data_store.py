import json

from tools.travel_data_store import TravelDataStore


def test_travel_data_store_creates_json_and_excel(tmp_path):
    store = TravelDataStore(data_dir=str(tmp_path / "travel_data"))

    paths = store.ensure_ready()

    assert paths["flight_json"].endswith("live_flights.json")
    assert paths["rail_json"].endswith("live_rail.json")
    assert paths["bookings_json"].endswith("bookings.json")
    assert paths["excel_path"].endswith("travel_live_data.xlsx")
    assert (tmp_path / "travel_data" / "live_flights.json").exists()
    assert (tmp_path / "travel_data" / "live_rail.json").exists()
    assert (tmp_path / "travel_data" / "bookings.json").exists()
    assert (tmp_path / "travel_data" / "travel_live_data.xlsx").exists()
    assert store.read_excel_sheet_names() == ["Flights", "Rail", "Bookings"]


def test_travel_data_store_searches_flights_and_creates_booking(tmp_path):
    store = TravelDataStore(data_dir=str(tmp_path / "travel_data"))
    store.ensure_ready()

    trips = store.search("Dallas", "New York", "July 10")
    best = store.best_trip(trips)
    booking = store.create_booking(
        best,
        ["12A", "12B"],
        amount=440,
        delivery_method="email",
        delivery_target="user@example.com",
    )

    assert best["trip_id"] == "FLT-001"
    assert best["provider"] == "American Airlines"
    assert booking["booking_id"].startswith("TRIP-")
    assert booking["total_price"] == 440
    assert booking["passenger_name"] == "Harshit P."
    assert booking["trip_type"] == "flight"
    assert booking["from"] == "Dallas"
    assert booking["to"] == "New York"
    assert booking["seat"] == "12A, 12B"
    assert booking["amount"] == 440
    assert booking["payment_status"] == "paid"
    assert booking["ticket_status"] == "generated"
    assert booking["delivery_method"] == "email"
    assert booking["delivery_target"] == "user@example.com"

    saved = json.loads((tmp_path / "travel_data" / "bookings.json").read_text(encoding="utf-8"))
    assert saved[0]["booking_id"] == booking["booking_id"]
