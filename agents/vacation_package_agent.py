from agents.base_agent import BaseAgent


class VacationPackageAgent(BaseAgent):
    name = "VacationPackageAgent"
    agent_type = "VacationPackage"
    rag_category = "booking"

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        answer = "\n".join([
            "VacationPlannerAgent / vacation_package",
            "",
            "5-Day Japan Vacation Plan",
            "",
            "Day 1:",
            "Tokyo - arrival, hotel check-in, evening food walk.",
            "",
            "Day 2:",
            "Shibuya and Akihabara.",
            "",
            "Day 3:",
            "Mt. Fuji day trip.",
            "",
            "Day 4:",
            "Kyoto temples, Gion, and local dinner.",
            "",
            "Day 5:",
            "Osaka food tour and departure.",
            "",
            "Planning Stack:",
            "- Flights: estimate after dates and budget",
            "- Hotels: Tokyo/Kyoto split",
            "- Attractions: city + nature balance",
            "- Restaurants: ramen, sushi, vegetarian-friendly options",
        ])
        return self.response(query, [
            "VacationPlannerAgent: generated itinerary across flights, hotels, attractions, and food.",
        ], answer, {
            "destination": "Japan",
            "days": 5,
            "safety_layer_skip_actions": ["book", "pay"],
        })
