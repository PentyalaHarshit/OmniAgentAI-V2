class MockBookingAPI:
    def search_availability(self, agent_type: str, extracted: dict):
        return {
            "available": True,
            "provider": f"Demo {agent_type} Provider",
            "options": [
                {"name": f"{agent_type} Option A", "price": "$120", "rating": "4.5"},
                {"name": f"{agent_type} Option B", "price": "$150", "rating": "4.2"},
                {"name": f"{agent_type} Option C", "price": "$180", "rating": "4.7"},
            ],
            "note": "Demo only. Connect real provider API for production."
        }

    def estimate_price(self, agent_type: str, extracted: dict):
        return {"estimated_total": "$120 - $180", "taxes_and_fees": "May apply"}

    def get_policy(self, agent_type: str):
        return {"payment": "Ask user confirmation before charging.", "cancellation": "Policy depends on provider.", "safety": "Never claim real booking/order/payment in demo."}
