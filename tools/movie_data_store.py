import json
from datetime import datetime
from pathlib import Path


DEFAULT_MOVIES = [
    {
        "movie_id": 1,
        "movie_name": "Mission Impossible: Final Reckoning",
        "theater": "AMC Stonebriar 24",
        "city": "Frisco",
        "showtime": "5:00 PM",
        "price": 16,
        "available_seats": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4"],
    },
    {
        "movie_id": 1,
        "movie_name": "Mission Impossible: Final Reckoning",
        "theater": "Cinemark Frisco Square",
        "city": "Frisco",
        "showtime": "8:30 PM",
        "price": 16,
        "available_seats": ["A1", "A2", "B1", "B2"],
    },
    {
        "movie_id": 2,
        "movie_name": "Superman",
        "theater": "Regal Dallas",
        "city": "Dallas",
        "showtime": "6:00 PM",
        "price": 18,
        "available_seats": ["A1", "A2", "A3", "B1", "B2", "B3"],
    },
    {
        "movie_id": 3,
        "movie_name": "Jurassic World Rebirth",
        "theater": "AMC Dallas",
        "city": "Dallas",
        "showtime": "7:15 PM",
        "price": 17,
        "available_seats": ["A1", "A2", "A3", "A4", "B1", "B2"],
    },
    {
        "movie_id": 4,
        "movie_name": "F1 The Movie",
        "theater": "Cinemark Plano",
        "city": "Plano",
        "showtime": "8:30 PM",
        "price": 16,
        "available_seats": ["A1", "A2", "B1", "B2"],
    },
    {
        "movie_id": 5,
        "movie_name": "How to Train Your Dragon",
        "theater": "AMC Stonebriar 24",
        "city": "Frisco",
        "showtime": "1:45 PM",
        "price": 14,
        "available_seats": ["A1", "A2", "A3", "B1", "B2", "B3"],
    },
]


class MovieDataStore:
    def __init__(self, data_dir: str = "movie_data"):
        self.data_dir = Path(data_dir)
        self.movies_path = self.data_dir / "live_movies.json"
        self.bookings_path = self.data_dir / "bookings.json"

    def ensure_ready(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.movies_path.exists():
            self.write_json(self.movies_path, DEFAULT_MOVIES)
        if not self.bookings_path.exists():
            self.write_json(self.bookings_path, [])
        return {
            "movies_json": str(self.movies_path),
            "bookings_json": str(self.bookings_path),
        }

    def list_movies(self):
        self.ensure_ready()
        seen = {}
        for show in self.load_json(self.movies_path):
            seen.setdefault(str(show["movie_id"]), show["movie_name"])
        return [{"movie_id": int(movie_id), "movie_name": name} for movie_id, name in seen.items()]

    def select_movie(self, user_value: str):
        movies = self.list_movies()
        text = user_value.strip().lower()
        for movie in movies:
            if text == str(movie["movie_id"]) or text == movie["movie_name"].lower():
                return movie
        for movie in movies:
            if text in movie["movie_name"].lower():
                return movie
        return None

    def theaters_for_movie(self, movie_name: str):
        shows = [show for show in self.load_json(self.movies_path) if show["movie_name"].lower() == movie_name.lower()]
        theaters = []
        seen = set()
        for show in shows:
            key = (show["theater"], show["city"])
            if key not in seen:
                seen.add(key)
                theaters.append({"theater": show["theater"], "city": show["city"]})
        return theaters

    def select_theater(self, movie_name: str, user_value: str):
        theaters = self.theaters_for_movie(movie_name)
        text = user_value.strip().lower()
        for index, theater in enumerate(theaters, start=1):
            if text == str(index) or text == theater["theater"].lower():
                return theater
        for theater in theaters:
            if text in theater["theater"].lower():
                return theater
        return None

    def showtimes_for_theater(self, movie_name: str, theater_name: str):
        return [
            show
            for show in self.load_json(self.movies_path)
            if show["movie_name"].lower() == movie_name.lower()
            and show["theater"].lower() == theater_name.lower()
        ]

    def select_showtime(self, movie_name: str, theater_name: str, user_value: str):
        showtimes = self.showtimes_for_theater(movie_name, theater_name)
        text = user_value.strip().lower()
        for index, show in enumerate(showtimes, start=1):
            if text == str(index) or text == show["showtime"].lower():
                return show
        return None

    def create_booking(self, show: dict, seats: list[str], delivery_method: str):
        self.ensure_ready()
        bookings = self.load_json(self.bookings_path)
        ticket_id = f"MOVIE-{datetime.now().strftime('%Y%m%d')}-{len(bookings) + 1:03d}"
        amount = int(show["price"]) * len(seats)
        booking = {
            "booking_id": ticket_id,
            "ticket_id": ticket_id,
            "movie_name": show["movie_name"],
            "theater": show["theater"],
            "city": show["city"],
            "showtime": show["showtime"],
            "seats": seats,
            "seat": ", ".join(seats),
            "amount": amount,
            "payment_status": "paid",
            "ticket_status": "generated",
            "delivery_method": delivery_method,
            "delivery_status": "sent",
            "qr_code": f"QR-{ticket_id}",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        bookings.append(booking)
        self.write_json(self.bookings_path, bookings)
        return booking

    def load_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def write_json(self, path: Path, rows: list[dict]):
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
