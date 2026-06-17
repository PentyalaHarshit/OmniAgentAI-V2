from agents.base_agent import BaseAgent


class EventAgent(BaseAgent):
    name = "EventAgent"
    agent_type = "Event"
    rag_category = "booking"

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        events = [
            {"name": "Dallas Summer Beats", "venue": "American Airlines Center", "price": 85},
            {"name": "Deep Ellum Live Night", "venue": "The Factory", "price": 55},
            {"name": "Plano Jazz Weekend", "venue": "Legacy Hall", "price": 40},
        ]
        answer = "\n".join([
            "EventBookingAgent / event",
            "",
            "Events Found",
            "",
            *[
                f"{index}. {event['name']}\n   Venue: {event['venue']}\n   Ticket: ${event['price']}"
                for index, event in enumerate(events, start=1)
            ],
            "",
            "Select tickets?",
            "yes/no",
        ])
        return self.response(query, [
            "Event Search Agent: found events for the requested city/time.",
            "Ticket Agent: waiting for ticket-selection confirmation.",
        ], answer, {
            "events": events,
            "safety_layer_skip_actions": ["book", "pay"],
        })
