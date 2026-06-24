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
        observation_loop = self.tot.create_observation_guided_loop(
            self.agent_type,
            query,
            "Search restaurants, observe slots, and wait for reservation confirmation.",
            [
                {
                    "action": "Search local restaurant inventory",
                    "observation": f"{len(restaurants)} restaurants found",
                },
                {
                    "action": "Find available table slots",
                    "observation": ", ".join(slots),
                },
                {
                    "action": "Run reservation safety check",
                    "observation": "No reservation without explicit confirmation.",
                },
            ],
            verified=True,
        )
        return self.response(query, [
            "Restaurant Search Agent: searched local restaurant inventory.",
            "Reservation Agent: found available table slots.",
            *self.tot.format_observation_loop(observation_loop),
        ], answer, {
            "restaurants": restaurants,
            "available_slots": slots,
            "safety_layer_skip_actions": ["book"],
            "observation_guided_tot_react": observation_loop,
        })
