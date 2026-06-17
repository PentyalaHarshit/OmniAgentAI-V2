from agents.base_agent import BaseAgent


class RestaurantAgent(BaseAgent):
    name = "RestaurantAgent"
    agent_type = "Restaurant"
    rag_category = "booking"

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        restaurants = ["Spice Grill", "Hyderabad House", "Bawarchi"]
        slots = ["7:00 PM", "7:30 PM", "8:00 PM"]
        answer = "\n".join([
            "RestaurantAgent / restaurant",
            "",
            "Top Restaurants",
            "",
            *[f"{index}. {name}" for index, name in enumerate(restaurants, start=1)],
            "",
            "Available Table:",
            *slots,
            "",
            "Reserve table?",
            "yes/no",
        ])
        return self.response(query, [
            "Restaurant Search Agent: searched local restaurant inventory.",
            "Reservation Agent: found available table slots.",
        ], answer, {
            "restaurants": restaurants,
            "available_slots": slots,
            "safety_layer_skip_actions": ["book"],
        })
