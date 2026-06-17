import re

from agents.base_agent import BaseAgent


class CabAgent(BaseAgent):
    name = "CabAgent"
    agent_type = "Cab"
    rag_category = "booking"

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        pickup, destination = self.extract_route(query)
        options = [
            {"type": "Economy", "fare": 42, "eta": "6 min", "driver": "Alex R."},
            {"type": "Comfort", "fare": 58, "eta": "8 min", "driver": "Maya S."},
            {"type": "XL", "fare": 74, "eta": "10 min", "driver": "Chris P."},
        ]
        answer = "\n".join([
            "RideBookingAgent / cab",
            "",
            f"Pickup: {pickup or 'Plano'}",
            f"Destination: {destination or 'DFW Airport'}",
            "",
            "Fare Estimate",
            *[f"{index}. {ride['type']} - ${ride['fare']} - ETA {ride['eta']}" for index, ride in enumerate(options, start=1)],
            "",
            "Recommended Driver Details",
            f"Driver: {options[0]['driver']}",
            f"Ride Type: {options[0]['type']}",
            "",
            "Confirm ride?",
            "yes/no",
        ])
        return self.response(query, [
            "Fare Estimate Agent: calculated demo ride prices.",
            "Ride Selection Agent: recommended fastest option.",
        ], answer, {
            "rides": options,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    @staticmethod
    def extract_route(query: str):
        match = re.search(r"from\s+(.+?)\s+to\s+(.+?)(?:\.|$)", query, re.I)
        if not match:
            return "", ""
        return match.group(1).strip().title(), match.group(2).strip()
