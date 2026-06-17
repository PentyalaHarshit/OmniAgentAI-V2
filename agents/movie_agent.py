import re

from agents.base_agent import BaseAgent
from tools.movie_data_store import MovieDataStore


class MovieAgent(BaseAgent):
    name = "MovieAgent"
    agent_type = "Movie"
    rag_category = "booking"

    def __init__(self):
        super().__init__()
        self.movie_store = MovieDataStore()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        state = self.conversation_state.get(session_id)
        flow = state.get("flow")

        if state.get("active_agent") == self.name and flow == "movie_select_movie":
            return self.handle_movie_selection(query, state, session_id)
        if state.get("active_agent") == self.name and flow == "movie_select_theater":
            return self.handle_theater_selection(query, state, session_id)
        if state.get("active_agent") == self.name and flow == "movie_select_showtime":
            return self.handle_showtime_selection(query, state, session_id)
        if state.get("active_agent") == self.name and flow == "movie_select_seats":
            return self.handle_seat_selection(query, state, session_id)
        if state.get("active_agent") == self.name and flow == "movie_delivery_method":
            return self.handle_delivery_method(query, state, session_id)
        if state.get("active_agent") == self.name and flow == "movie_payment_confirmation":
            return self.handle_payment_confirmation(query, state, session_id)

        return self.start_movie_flow(query, session_id)

    def start_movie_flow(self, query: str, session_id: str):
        movies = self.movie_store.list_movies()
        state = {
            "active_agent": self.name,
            "flow": "movie_select_movie",
            "fields": {},
            "missing_fields": ["movie"],
        }
        self.conversation_state.set(session_id, state)
        answer = "\n".join([
            "MovieBookingAgent / movie",
            "",
            "Live Movies Available Today",
            "",
            self.format_movies(movies),
            "",
            "Please enter movie name or movie number.",
        ])
        return self.response(query, [
            "MovieSearchAgent: loaded live movies from local movie database.",
            "Question Agent: asking user to select a movie first.",
        ], answer, {
            "flow": "movie_select_movie",
            "movies": movies,
            "data_sources": self.movie_store.ensure_ready(),
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_movie_selection(self, query: str, state: dict, session_id: str):
        movie = self.movie_store.select_movie(query)
        if not movie:
            return self.repeat_movie_selection(query)

        fields = state.get("fields", {})
        fields["movie"] = movie
        state["fields"] = fields
        state["flow"] = "movie_select_theater"
        state["missing_fields"] = ["theater"]
        self.conversation_state.set(session_id, state)

        theaters = self.movie_store.theaters_for_movie(movie["movie_name"])
        answer = "\n".join([
            "Theaters Available",
            "",
            self.format_theaters(theaters),
            "",
            "Select theater.",
        ])
        return self.response(query, [
            "MovieSearchAgent: selected movie and retrieved theaters.",
        ], answer, {
            "flow": "movie_select_theater",
            "movie": movie,
            "theaters": theaters,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def repeat_movie_selection(self, query: str):
        movies = self.movie_store.list_movies()
        return self.response(query, [
            "Validation Agent: movie selection was invalid.",
        ], "\n".join([
            "Invalid movie selection.",
            "",
            "Live Movies Available Today",
            "",
            self.format_movies(movies),
            "",
            "Please enter movie name or movie number.",
        ]), {
            "flow": "movie_select_movie",
            "movies": movies,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_theater_selection(self, query: str, state: dict, session_id: str):
        fields = state.get("fields", {})
        movie = fields["movie"]
        theater = self.movie_store.select_theater(movie["movie_name"], query)
        if not theater:
            theaters = self.movie_store.theaters_for_movie(movie["movie_name"])
            return self.response(query, [
                "Validation Agent: theater selection was invalid.",
            ], "\n".join([
                "Invalid theater selection.",
                "",
                "Theaters Available",
                "",
                self.format_theaters(theaters),
                "",
                "Select theater.",
            ]), {
                "flow": "movie_select_theater",
                "theaters": theaters,
                "safety_layer_skip_actions": ["book", "pay"],
            })

        fields["theater"] = theater
        state["fields"] = fields
        state["flow"] = "movie_select_showtime"
        state["missing_fields"] = ["showtime"]
        self.conversation_state.set(session_id, state)

        showtimes = self.movie_store.showtimes_for_theater(movie["movie_name"], theater["theater"])
        answer = "\n".join([
            "Available Showtimes",
            "",
            self.format_showtimes(showtimes),
            "",
            "Select showtime.",
        ])
        return self.response(query, [
            "Theater Agent: selected theater and retrieved showtimes.",
        ], answer, {
            "flow": "movie_select_showtime",
            "showtimes": showtimes,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_showtime_selection(self, query: str, state: dict, session_id: str):
        fields = state.get("fields", {})
        movie = fields["movie"]
        theater = fields["theater"]
        show = self.movie_store.select_showtime(movie["movie_name"], theater["theater"], query)
        if not show:
            showtimes = self.movie_store.showtimes_for_theater(movie["movie_name"], theater["theater"])
            return self.response(query, [
                "Validation Agent: showtime selection was invalid.",
            ], "\n".join([
                "Invalid showtime selection.",
                "",
                "Available Showtimes",
                "",
                self.format_showtimes(showtimes),
                "",
                "Select showtime.",
            ]), {
                "flow": "movie_select_showtime",
                "showtimes": showtimes,
                "safety_layer_skip_actions": ["book", "pay"],
            })

        fields["show"] = show
        state["fields"] = fields
        state["flow"] = "movie_select_seats"
        state["missing_fields"] = ["seats"]
        self.conversation_state.set(session_id, state)
        answer = "\n".join([
            "Available Seats",
            "",
            self.format_seats(show["available_seats"]),
            "",
            "Select seats.",
        ])
        return self.response(query, [
            "Showtime Agent: selected showtime and displayed seats.",
        ], answer, {
            "flow": "movie_select_seats",
            "show": show,
            "available_seats": show["available_seats"],
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_seat_selection(self, query: str, state: dict, session_id: str):
        fields = state.get("fields", {})
        show = fields["show"]
        seats = self.parse_seats(query)
        if not seats:
            return self.repeat_seat_selection(query, show, "Invalid seat selection. Please select at least one seat.")

        invalid = [seat for seat in seats if seat not in show["available_seats"]]
        if invalid:
            return self.repeat_seat_selection(query, show, "Invalid seat selection. Please choose only available seats.")

        fields["seats"] = seats
        fields["amount"] = int(show["price"]) * len(seats)
        state["fields"] = fields
        state["flow"] = "movie_delivery_method"
        state["missing_fields"] = ["delivery_method"]
        self.conversation_state.set(session_id, state)

        answer = "\n".join([
            "Booking Summary",
            "",
            "Movie:",
            show["movie_name"],
            "",
            "Theater:",
            show["theater"],
            "",
            "Showtime:",
            show["showtime"],
            "",
            "Seats:",
            ", ".join(seats),
            "",
            "Total Price:",
            f"${fields['amount']}",
            "",
            "Delivery Options:",
            "1. Email",
            "2. SMS",
            "3. WhatsApp",
            "",
            "Choose delivery method.",
        ])
        return self.response(query, [
            "Seat Selection Agent: seats selected.",
            "PaymentAgent: calculated ticket total.",
            "NotificationAgent: asking delivery method before payment.",
        ], answer, {
            "flow": "movie_delivery_method",
            "booking_summary": fields,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def repeat_seat_selection(self, query: str, show: dict, message: str):
        return self.response(query, [
            "Validation Agent: seat selection was invalid.",
        ], "\n".join([
            "Available Seats",
            "",
            message,
            "",
            self.format_seats(show["available_seats"]),
            "",
            "Select seats.",
        ]), {
            "flow": "movie_select_seats",
            "available_seats": show["available_seats"],
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_delivery_method(self, query: str, state: dict, session_id: str):
        valid, method, message = self.validate_delivery_method(query)
        if not valid:
            return self.response(query, [
                "Validation Agent: delivery method was invalid.",
            ], "\n".join([
                message,
                "",
                "Delivery Options:",
                "1. Email",
                "2. SMS",
                "3. WhatsApp",
                "",
                "Choose delivery method.",
            ]), {
                "flow": "movie_delivery_method",
                "safety_layer_skip_actions": ["book", "pay"],
            })

        fields = state.get("fields", {})
        fields["delivery_method"] = method
        state["fields"] = fields
        state["flow"] = "movie_payment_confirmation"
        state["missing_fields"] = ["payment_confirmation"]
        self.conversation_state.set(session_id, state)

        amount = int(fields["amount"])
        answer = "\n".join([
            "Payment Agent",
            "",
            f"Do you confirm payment of ${amount}?",
            "yes/no",
        ])
        return self.response(query, [
            "NotificationAgent: delivery method saved.",
            "PaymentAgent: explicit payment confirmation required.",
        ], answer, {
            "flow": "movie_payment_confirmation",
            "amount": amount,
            "delivery_method": method,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_payment_confirmation(self, query: str, state: dict, session_id: str):
        valid, value, message = self.validate_yes_no(query)
        if not valid:
            amount = int(state.get("fields", {}).get("amount", 0))
            return self.response(query, [
                "Validation Agent: payment confirmation was invalid.",
            ], "\n".join([
                message,
                "Please answer only: yes or no.",
                "",
                f"Do you confirm payment of ${amount}?",
                "yes/no",
            ]), {
                "flow": "movie_payment_confirmation",
                "safety_layer_skip_actions": ["book", "pay"],
            })

        if value == "no":
            self.conversation_state.clear(session_id)
            return self.response(query, [
                "PaymentAgent: user declined payment.",
            ], "\n".join([
                "Payment cancelled.",
                "No movie ticket generated.",
            ]), {
                "status": "payment_cancelled",
                "safety_layer_skip_actions": ["book", "pay"],
            })

        fields = state.get("fields", {})
        booking = self.movie_store.create_booking(
            fields["show"],
            fields["seats"],
            fields["delivery_method"],
        )
        self.conversation_state.clear(session_id)
        answer = "\n".join([
            f"Payment successful. Movie e-ticket generated and sent by {fields['delivery_method'].title()}.",
            "",
            f"Ticket ID: {booking['ticket_id']}",
            f"QR Code: {booking['qr_code']}",
        ])
        return self.response(query, [
            "PaymentAgent: payment confirmed by user.",
            "TicketAgent: generated QR e-ticket.",
            "NotificationAgent: sent ticket by selected delivery method.",
        ], answer, {
            "status": "confirmed",
            "booking": booking,
            "confirmed_actions": ["book", "pay"],
        })

    def format_movies(self, movies: list[dict]):
        return "\n".join(f"{movie['movie_id']}. {movie['movie_name']}" for movie in movies)

    def format_theaters(self, theaters: list[dict]):
        return "\n".join(f"{index}. {item['theater']}" for index, item in enumerate(theaters, start=1))

    def format_showtimes(self, shows: list[dict]):
        return "\n".join(f"{index}. {show['showtime']}" for index, show in enumerate(shows, start=1))

    def format_seats(self, seats: list[str]):
        rows = {}
        for seat in seats:
            rows.setdefault(seat[0], []).append(seat)
        return "\n".join(" ".join(values) for values in rows.values())

    def parse_seats(self, query: str):
        return [seat.upper() for seat in re.findall(r"\b[A-Z]\d{1,2}\b", query.upper())]

    def validate_delivery_method(self, value: str):
        cleaned = value.lower().strip()
        mapping = {
            "1": "email",
            "email": "email",
            "2": "sms",
            "sms": "sms",
            "text": "sms",
            "3": "whatsapp",
            "whatsapp": "whatsapp",
            "whats app": "whatsapp",
        }
        if cleaned not in mapping:
            return False, None, "Invalid delivery method. Please choose Email, SMS, or WhatsApp."
        return True, mapping[cleaned], ""

    def validate_yes_no(self, value: str):
        cleaned = value.lower().strip()
        if cleaned not in {"yes", "no"}:
            return False, None, "Invalid response."
        return True, cleaned, ""
