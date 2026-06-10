class SlotFillingTool:
    def __init__(self):
        self.questions = {
            "Travel": {
                "destination": "Which place do you want to travel to?",
                "dates": "What travel dates do you prefer?",
                "travelers": "How many travelers?",
                "budget": "What is your budget?",
                "interests": "What do you like: adventure, food, nature, shopping, museums, or relaxing?"
            },
            "Hotel": {
                "city": "Which city do you want the hotel in?",
                "check_in": "What is your check-in date?",
                "checkout": "What is your checkout date?",
                "nights": "How many nights?",
                "guests": "How many guests?",
                "budget": "What is your hotel budget?",
                "amenities": "Any amenities needed, like breakfast, parking, pool, or Wi-Fi?"
            },
            "Movie": {
                "movie": "Which movie do you want to watch?",
                "city": "Which city or area?",
                "theater": "Any preferred theater?",
                "date": "Which date?",
                "time": "What showtime do you prefer?",
                "tickets": "How many tickets?",
                "seats": "Any seat preference?"
            },
            "Healthcare": {
                "hospital": "Which hospital would you like to visit?",
                "symptoms": "Please describe your symptoms.",
                "age": "What is the patient age?",
                "medical_history": "Any medical history like diabetes, blood pressure, or heart disease?"
            },
            "Flight": {
                "origin": "Which city are you flying from?",
                "destination": "Which city are you flying to?",
                "date": "What travel date?",
                "time": "What time do you prefer?",
                "passengers": "How many passengers?",
                "budget": "What is your flight budget?"
            },
            "Restaurant": {
                "cuisine": "What cuisine do you prefer?",
                "location": "Which location or city?",
                "party_size": "How many people?",
                "date": "Which date?",
                "time": "What time?",
                "budget": "What is your budget?"
            },
            "Cab": {
                "pickup": "What is your pickup location?",
                "drop": "What is your drop location?",
                "date": "Which date?",
                "time": "What pickup time?",
                "passengers": "How many passengers?"
            },
            "Shopping": {
                "product": "What product do you want to buy?",
                "budget": "What is your budget?",
                "brand": "Any preferred brand?",
                "use_case": "What will you use it for?",
                "payment_method": "Which payment method do you prefer? You can skip this for now."
            },
            "Payment": {
                "amount": "What amount should I prepare payment for?",
                "payment_method": "Which payment method do you prefer?",
                "currency": "Which currency?"
            },
            "Research": {
                "topic": "What research topic do you want to work on?",
                "goal": "What is your goal: summary, gaps, ideas, or paper writing?",
                "method": "Any method you want to use?"
            },
            "Resume": {
                "target_role": "Which role are you targeting?",
                "job_description": "Do you have a job description to match?"
            },
            "General": {
                "intent": "What do you want to do?",
                "location": "Which location?",
                "date": "Which date?",
                "budget": "What is your budget?"
            }
        }

    def missing_fields(self, fields: dict, optional_fields: list[str] | None = None):
        optional_fields = set(optional_fields or [])
        return [k for k, v in fields.items() if v == "not provided" and k not in optional_fields]

    def next_question(self, agent_type: str, missing_fields: list[str]):
        if not missing_fields:
            return ""

        field = missing_fields[0]
        return self.questions.get(agent_type, {}).get(field, f"Please provide {field}.")
