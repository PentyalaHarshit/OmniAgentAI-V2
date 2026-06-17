import re

from agents.base_agent import BaseAgent
from tools.travel_data_store import TravelDataStore


class TravelAgent(BaseAgent):
    name = "TravelAgent"
    agent_type = "Travel"
    rag_category = "booking"
    required_fields = ["origin", "destination", "date", "passengers", "budget"]
    optional_fields = []

    trip_questions = [
        ("origin", "What is your departure city?"),
        ("destination", "What is your destination city?"),
        ("date", "What date would you like to travel?"),
        ("passengers", "How many passengers?"),
        ("budget", "What is your budget?"),
    ]

    available_seats = ["12A", "12B", "14C", "15D"]

    def __init__(self):
        super().__init__()
        self.travel_store = TravelDataStore()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        state = self.conversation_state.get(session_id)
        if (
            state.get("active_agent") == self.name
            and str(state.get("flow", "")).startswith("trip_")
            and self.is_new_trip_request(query)
        ):
            state = {}

        if state.get("active_agent") == self.name and state.get("flow") == "trip_questions":
            return self.handle_question_answer(query, state, session_id)

        if state.get("active_agent") == self.name and state.get("flow") == "trip_booking_confirmation":
            return self.handle_booking_confirmation(query, state, session_id)

        if state.get("active_agent") == self.name and state.get("flow") == "trip_seat_selection":
            return self.handle_seat_selection(query, state, session_id)

        if state.get("active_agent") == self.name and state.get("flow") == "trip_delivery_method":
            return self.handle_delivery_method(query, state, session_id)

        if state.get("active_agent") == self.name and state.get("flow") == "trip_delivery_target":
            return self.handle_delivery_target(query, state, session_id)

        if state.get("active_agent") == self.name and state.get("flow") == "trip_payment_confirmation":
            return self.handle_payment_confirmation(query, state, session_id)

        state = {
            "active_agent": self.name,
            "flow": "trip_questions",
            "original_query": query,
            "fields": {},
            "current_question_index": 0,
            "missing_fields": [key for key, _ in self.trip_questions],
        }
        self.conversation_state.set(session_id, state)
        return self.ask_current_question(query, state)

    def handle_question_answer(self, query: str, state: dict, session_id: str):
        index = int(state.get("current_question_index", 0) or 0)
        key, _ = self.trip_questions[index]
        valid, value, message = self.validate_answer(key, query)

        if not valid:
            return self.ask_current_question(query, state, validation_error=message)

        fields = state.get("fields", {})
        fields[key] = value
        index += 1
        state["fields"] = fields
        state["current_question_index"] = index
        state["missing_fields"] = [field for field, _ in self.trip_questions[index:]]
        self.conversation_state.set(session_id, state)

        if index < len(self.trip_questions):
            return self.ask_current_question(query, state)

        return self.trip_analysis(query, state, session_id)

    def ask_current_question(self, query: str, state: dict, validation_error: str = ""):
        index = int(state.get("current_question_index", 0) or 0)
        _, question = self.trip_questions[index]
        thoughts = [
            "TripAgent: started one-by-one trip intake.",
            "Question Agent: asking the next required travel detail.",
        ]

        lines = ["TripAgent / travel", ""]
        if validation_error:
            thoughts.append("Validation Agent: rejected the previous answer and repeated the same question.")
            lines.extend([validation_error, ""])
        lines.append(question)

        return self.response(query, thoughts, "\n".join(lines), {
            "slot_filling": True,
            "flow": "trip_questions",
            "fields": state.get("fields", {}),
            "missing_fields": state.get("missing_fields", []),
            "next_question": question,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def trip_analysis(self, query: str, state: dict, session_id: str):
        fields = state.get("fields", {})
        trips = self.search_travel_options(fields)
        if not trips:
            self.conversation_state.clear(session_id)
            return self.response(query, [
                "Travel Search Agent: searched rail and flight JSON databases.",
                "Recommendation Agent: no matching trip was found.",
            ], "\n".join([
                "TripAgent / travel",
                "",
                "No matching trips found in the local travel database.",
                "Try another route or date after refreshing live travel data.",
            ]), {
                "slot_filling": False,
                "trip": fields,
                "available_trips": [],
                "safety_layer_skip_actions": ["book", "pay"],
            })

        recommendation = self.recommend_trip(trips)
        fields["recommended_trip"] = recommendation
        fields["available_trips"] = trips

        state["flow"] = "trip_booking_confirmation"
        state["fields"] = fields
        state["missing_fields"] = ["booking_confirmation"]
        self.conversation_state.set(session_id, state)

        thoughts = [
            "Travel Search Agent: searched live flight and rail JSON databases.",
            "Price Comparison Agent: compared price and duration across normalized trips.",
            "Recommendation Agent: selected the best option from rail and flight data.",
            "Verification Agent: booking is not created until the user confirms.",
        ]

        answer = "\n".join([
            "TripAgent / travel",
            "",
            "Trip Analysis",
            "",
            f"From: {fields['origin']}",
            f"To: {fields['destination']}",
            f"Date: {fields['date']}",
            f"Passengers: {fields['passengers']}",
            "",
            "Available Trips:",
            "",
            self.format_trip_options(trips),
            "",
            "Recommended:",
            recommendation["provider"],
            "Best price and shortest duration from the local travel data.",
            "",
            f"Would you like to book this trip with {recommendation['provider']}?",
            "(yes/no)",
        ])

        return self.response(query, thoughts, answer, {
            "slot_filling": False,
            "flow": "trip_booking_confirmation",
            "trip": fields,
            "available_trips": trips,
            "recommendation": recommendation,
            "booking": {
                "status": "awaiting_user_confirmation",
                "requires_user_confirmation": True,
            },
            "data_sources": self.travel_store.ensure_ready(),
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_booking_confirmation(self, query: str, state: dict, session_id: str):
        valid, value, message = self.validate_yes_no(query)
        if not valid:
            return self.ask_booking_confirmation_again(query, state, message)

        if value == "no":
            self.conversation_state.clear(session_id)
            return self.response(query, ["Booking Agent: user declined booking."], "\n".join([
                "TripAgent / travel",
                "",
                "No trip booked.",
                "You can restart whenever you want a new recommendation.",
            ]), {
                "status": "not_booked",
                "safety_layer_skip_actions": ["book", "pay"],
            })

        state["flow"] = "trip_seat_selection"
        state["missing_fields"] = ["seat_selection"]
        self.conversation_state.set(session_id, state)

        fields = state.get("fields", {})
        seats = fields.get("recommended_trip", {}).get("available_seats") or self.available_seats
        answer = "\n".join([
            "Booking Agent",
            "",
            "Available Seats:",
            "\n".join(seats),
            "",
            f"Select {fields.get('passengers', 1)} seat(s).",
        ])
        return self.response(query, [
            "Booking Agent: user confirmed intent to book.",
            "Seat Selection Agent: showing available seats.",
        ], answer, {
            "flow": "trip_seat_selection",
            "available_seats": seats,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def ask_booking_confirmation_again(self, query: str, state: dict, message: str):
        fields = state.get("fields", {})
        recommendation = fields.get("recommended_trip", {})
        answer = "\n".join([
            "TripAgent / travel",
            "",
            message,
            "Please answer only: yes or no.",
            "",
            f"Would you like to book this trip with {recommendation.get('provider', 'the recommended provider')}?",
            "(yes/no)",
        ])
        return self.response(query, [
            "Validation Agent: booking confirmation answer was invalid.",
        ], answer, {
            "flow": "trip_booking_confirmation",
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_seat_selection(self, query: str, state: dict, session_id: str):
        fields = state.get("fields", {})
        passengers = int(fields.get("passengers", 1))
        available_seats = fields.get("recommended_trip", {}).get("available_seats") or self.available_seats
        selected = self.parse_seats(query)

        if len(selected) != passengers:
            return self.ask_seat_selection_again(
                query,
                f"Invalid seat selection. Please select exactly {passengers} seat(s).",
            )

        invalid = [seat for seat in selected if seat not in available_seats]
        if invalid:
            return self.ask_seat_selection_again(
                query,
                "Invalid seat selection. Please choose only from the available seats.",
                available_seats,
            )

        fields["selected_seats"] = selected
        recommendation = fields["recommended_trip"]
        total = passengers * int(recommendation["price"])
        fields["total_price"] = total
        state["fields"] = fields
        state["flow"] = "trip_delivery_method"
        state["missing_fields"] = ["delivery_method"]
        self.conversation_state.set(session_id, state)

        answer = "\n".join([
            "Payment Agent",
            "",
            "Passenger: Harshit P.",
            f"Trip: {recommendation['provider']} ({recommendation['type'].title()})",
            f"Date: {fields['date']}",
            f"Seats: {', '.join(selected)}",
            f"Total Price: ${total}",
            "",
            f"Total price is ${total}.",
            "How would you like to receive your ticket?",
            "",
            "1. Email",
            "2. SMS",
            "3. WhatsApp",
        ])
        return self.response(query, [
            "Seat Selection Agent: seats validated and reserved for review.",
            "Payment Agent: calculated payable amount.",
            "TicketAgent: waiting for delivery method before ticket generation.",
        ], answer, {
            "flow": "trip_delivery_method",
            "booking_summary": {
                "passenger": "Harshit P.",
                "trip": recommendation,
                "date": fields["date"],
                "seats": selected,
                "total_price": total,
                "requires_payment_confirmation": True,
            },
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def ask_seat_selection_again(self, query: str, message: str, available_seats: list[str] | None = None):
        seats = available_seats or self.available_seats
        answer = "\n".join([
            "Seat Selection Agent",
            "",
            message,
            "",
            "Available Seats:",
            "\n".join(seats),
        ])
        return self.response(query, [
            "Validation Agent: seat selection answer was invalid.",
        ], answer, {
            "flow": "trip_seat_selection",
            "available_seats": seats,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_delivery_method(self, query: str, state: dict, session_id: str):
        valid, method, message = self.validate_delivery_method(query)
        if not valid:
            return self.ask_delivery_method_again(query, message)

        fields = state.get("fields", {})
        fields["delivery_method"] = method
        state["fields"] = fields
        state["flow"] = "trip_delivery_target"
        state["missing_fields"] = ["delivery_target"]
        self.conversation_state.set(session_id, state)

        prompt = {
            "email": "Please enter your email address.",
            "sms": "Please enter your mobile number for SMS delivery.",
            "whatsapp": "Please enter your WhatsApp number.",
        }[method]
        return self.response(query, [
            "NotificationAgent: delivery method selected.",
        ], "\n".join([
            "NotificationAgent",
            "",
            prompt,
        ]), {
            "flow": "trip_delivery_target",
            "delivery_method": method,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def ask_delivery_method_again(self, query: str, message: str):
        return self.response(query, [
            "Validation Agent: delivery method answer was invalid.",
        ], "\n".join([
            "NotificationAgent",
            "",
            message,
            "",
            "How would you like to receive your ticket?",
            "1. Email",
            "2. SMS",
            "3. WhatsApp",
        ]), {
            "flow": "trip_delivery_method",
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_delivery_target(self, query: str, state: dict, session_id: str):
        fields = state.get("fields", {})
        method = fields.get("delivery_method", "")
        valid, target, message = self.validate_delivery_target(method, query)
        if not valid:
            return self.ask_delivery_target_again(query, method, message)

        fields["delivery_target"] = target
        state["fields"] = fields
        state["flow"] = "trip_payment_confirmation"
        state["missing_fields"] = ["payment_confirmation"]
        self.conversation_state.set(session_id, state)

        amount = int(fields.get("total_price", 0))
        answer = "\n".join([
            "Payment Agent",
            "",
            f"Payment required: ${amount}",
            f"Do you confirm payment of ${amount}?",
            "yes/no",
        ])
        return self.response(query, [
            "NotificationAgent: delivery target saved.",
            "Payment Agent: requesting explicit payment confirmation.",
        ], answer, {
            "flow": "trip_payment_confirmation",
            "amount": amount,
            "delivery_method": method,
            "delivery_target": target,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def ask_delivery_target_again(self, query: str, method: str, message: str):
        prompt = {
            "email": "Please enter your email address.",
            "sms": "Please enter your mobile number for SMS delivery.",
            "whatsapp": "Please enter your WhatsApp number.",
        }.get(method, "Please enter the delivery target.")
        return self.response(query, [
            "Validation Agent: delivery target answer was invalid.",
        ], "\n".join([
            "NotificationAgent",
            "",
            message,
            prompt,
        ]), {
            "flow": "trip_delivery_target",
            "delivery_method": method,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def handle_payment_confirmation(self, query: str, state: dict, session_id: str):
        valid, value, message = self.validate_yes_no(query)
        if not valid:
            return self.ask_payment_confirmation_again(query, state, message)

        if value == "no":
            self.conversation_state.clear(session_id)
            return self.response(query, ["Payment Agent: user declined payment confirmation."], "\n".join([
                "TripAgent / travel",
                "",
                "Payment cancelled.",
                "No ticket generated.",
                "No payment has been charged.",
            ]), {
                "status": "payment_cancelled",
                "safety_layer_skip_actions": ["book", "pay", "cancel"],
            })

        fields = state.get("fields", {})
        booking = self.travel_store.create_booking(
            fields.get("recommended_trip", {}),
            fields.get("selected_seats", []),
            passenger="Harshit P.",
            amount=int(fields.get("total_price", 0)),
            payment_status="paid",
            ticket_status="generated",
            delivery_method=fields.get("delivery_method", ""),
            delivery_target=fields.get("delivery_target", ""),
        )
        booking_id = booking["booking_id"]
        self.conversation_state.clear(session_id)

        answer = "\n".join([
            "Payment Status: Success",
            "",
            f"Booking ID: {booking_id}",
            "",
            "E-ticket generated.",
            "",
            f"Ticket ID: {booking_id}",
            f"Delivery Method: {fields.get('delivery_method', '').title()}",
            "Status: Sent",
        ])
        return self.response(query, [
            "PaymentAgent: explicit payment confirmation received.",
            "TicketAgent: e-ticket generated.",
            "NotificationAgent: ticket sent to selected delivery target.",
            "Verification Agent: booking record stored in travel database.",
        ], answer, {
            "status": "confirmed",
            "booking_id": booking_id,
            "ticket_id": booking_id,
            "booking": {
                "user_confirmed": True,
                "payment_confirmed": True,
                "record": booking,
                "trip": fields,
            },
            "data_sources": self.travel_store.ensure_ready(),
            "confirmed_actions": ["book", "pay"],
        })

    def ask_payment_confirmation_again(self, query: str, state: dict, message: str):
        amount = int(state.get("fields", {}).get("total_price", 0))
        answer = "\n".join([
            "Payment Agent",
            "",
            message,
            "Please answer only: yes or no.",
            "",
            f"Do you confirm payment of ${amount}?",
            "yes/no",
        ])
        return self.response(query, [
            "Validation Agent: payment confirmation answer was invalid.",
        ], answer, {
            "flow": "trip_payment_confirmation",
            "safety_layer_skip_actions": ["book", "pay"],
        })

    def validate_answer(self, key: str, value: str):
        cleaned = re.sub(r"\s+", " ", value.strip())
        if key in {"origin", "destination"}:
            if not re.search(r"[A-Za-z]", cleaned):
                return False, None, "Invalid city. Please enter a valid city name."
            return True, cleaned.title(), ""

        if key == "date":
            if len(cleaned) < 3:
                return False, None, "Invalid date. Please enter a travel date, for example: June 25."
            return True, cleaned, ""

        if key == "passengers":
            try:
                passengers = int(cleaned)
            except ValueError:
                return False, None, "Invalid passenger count. Please enter a number."
            if passengers < 1 or passengers > 9:
                return False, None, "Invalid passenger count. Please enter between 1 and 9 passengers."
            return True, passengers, ""

        if key == "budget":
            amount = re.search(r"\d+(?:\.\d+)?", cleaned)
            if not amount:
                return False, None, "Invalid budget. Please enter an amount, for example: $500."
            budget = float(amount.group(0))
            if budget <= 0:
                return False, None, "Invalid budget. Please enter an amount greater than 0."
            if budget.is_integer():
                return True, f"${int(budget)}", ""
            return True, f"${budget:.2f}", ""

        return True, cleaned, ""

    def is_new_trip_request(self, query: str):
        q = query.lower().strip()
        if q in {"yes", "no"}:
            return False
        return any(phrase in q for phrase in [
            "i need trip",
            "need a trip",
            "want to travel",
            "i want to travel",
            "plan a trip",
            "book a trip",
        ])

    def validate_yes_no(self, value: str):
        cleaned = value.lower().strip()
        if cleaned not in {"yes", "no"}:
            return False, None, "Invalid response."
        return True, cleaned, ""

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

    def validate_delivery_target(self, method: str, value: str):
        cleaned = value.strip()
        if method == "email":
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cleaned):
                return False, None, "Invalid email address."
            return True, cleaned, ""

        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 10 or len(digits) > 15:
            return False, None, "Invalid phone number. Please enter 10 to 15 digits."
        return True, cleaned, ""

    def parse_seats(self, value: str):
        return [seat.upper() for seat in re.findall(r"\b\d{1,2}[A-Z]\b", value.upper())]

    def search_travel_options(self, fields: dict):
        return self.travel_store.search(
            fields.get("origin", ""),
            fields.get("destination", ""),
            fields.get("date", ""),
        )

    def recommend_trip(self, trips: list[dict]):
        return self.travel_store.best_trip(trips)

    def format_trip_options(self, trips: list[dict]):
        return "\n\n".join(self.format_trip(index, trip) for index, trip in enumerate(trips, start=1))

    def format_trip(self, number: int, trip: dict):
        label = "Airline" if trip["type"] == "flight" else "Train"
        return "\n".join([
            f"{number}. {trip['provider']} ({trip['type'].title()})",
            f"   {label}: {trip['provider']}",
            f"   Departure: {trip['departure_time']}",
            f"   Arrival: {trip['arrival_time']}",
            f"   Price: ${trip['price']}",
        ])
