"""
crews/generic_rag_crew.py
==========================
GenericRAGCrew — orchestrates RAG + booking/availability for all booking agents.

For Hotel queries:
  If SERPAPI_API_KEY is configured → calls real Google Hotels API via SerpApi.
  Otherwise → falls back to MockBookingAPI demo data.

For all other agent types (Flight, Train, Bus, etc.):
  Uses MockBookingAPI demo data.
"""

from tools.rag_tool             import RAGTool
from tools.mock_booking_api     import MockBookingAPI
from tools.real_hotel_provider  import RealHotelProvider


class GenericRAGCrew:

    def __init__(self):
        self.rag                = RAGTool()
        self.api                = MockBookingAPI()
        self.real_hotel_provider = RealHotelProvider()

    def run(self, query: str, agent_type: str, extracted: dict, rag_category: str) -> dict:
        steps = []

        # ── Step 1: Planner ───────────────────────────────────────────────
        missing = [k for k, v in extracted.items() if v in (None, "not provided", "")]
        steps.append({
            "thought": "Planner Agent: plan workflow.",
            "output":  {"missing_fields": missing},
        })

        # ── Step 2: RAG knowledge retrieval ───────────────────────────────
        rag_result = self.rag.search(query, rag_category)
        steps.append({
            "thought": "RAG Retrieval Agent: retrieve knowledge from knowledge base.",
            "output":  rag_result,
        })

        # ── Step 3: Hotel — real API path ─────────────────────────────────
        if agent_type.lower() == "hotel" and self.real_hotel_provider.is_configured():
            return self._run_real_hotel(query, extracted, rag_result, steps)

        # ── Step 3: All other agents — demo/mock path ─────────────────────
        return self._run_mock(query, agent_type, extracted, rag_result, rag_category, steps)

    # ── Real hotel provider path ─────────────────────────────────────────

    def _run_real_hotel(self, query: str, extracted: dict, rag_result, steps: list) -> dict:
        city      = extracted.get("city", "")
        check_in  = extracted.get("check_in", "")
        check_out = extracted.get("checkout", "")
        guests    = extracted.get("guests", 1)
        budget    = extracted.get("budget")

        steps.append({
            "thought": (
                f"Hotel Provider Agent: calling real hotel API (SerpApi Google Hotels) "
                f"for city='{city}', check_in='{check_in}', check_out='{check_out}', "
                f"guests={guests}, budget={budget}."
            ),
            "output": None,
        })

        real_result = self.real_hotel_provider.search_hotels(
            city=city,
            check_in=check_in,
            check_out=check_out,
            guests=int(guests) if guests else 1,
            budget=float(budget) if budget else None,
        )

        steps[-1]["output"] = {
            "available":  real_result["available"],
            "provider":   real_result["provider"],
            "hotel_count": len(real_result["hotels"]),
        }

        if not real_result["available"]:
            error_msg = real_result.get("error", "No hotels found.")
            steps.append({
                "thought": f"Observation: Real hotel API returned no results. Error: {error_msg}",
                "output":  "no_results",
            })
            return {
                "crew_name":      "HotelRealProviderCrew",
                "crew_steps":     steps,
                "rag":            rag_result,
                "availability":   {"available": False, "error": error_msg},
                "pricing":        {},
                "recommendation": {},
                "self_check":     {"warning": error_msg},
                "error":          error_msg,
            }

        hotels    = real_result["hotels"]
        best      = hotels[0]

        # ── Comparison Agent ──────────────────────────────────────────────
        steps.append({
            "thought": (
                f"Comparison Agent: evaluating {len(hotels)} real hotels. "
                f"Best by price = '{best['name']}' at {best['price']}."
            ),
            "output": {
                "options_count": len(hotels),
                "best_name":     best["name"],
                "best_price":    best["price"],
            },
        })

        # ── Safety Agent ──────────────────────────────────────────────────
        steps.append({
            "thought": (
                "Safety Agent: real hotel data retrieved and displayed. "
                "No booking or payment has been initiated. User must confirm to proceed."
            ),
            "output": {"safe": True},
        })

        return {
            "crew_name":  "HotelRealProviderCrew",
            "crew_steps": steps,
            "rag":        rag_result,
            "availability": {
                "available": True,
                "provider":  real_result["provider"],
                "options":   hotels,
            },
            "pricing": {
                "estimated_total": best["price"],
                "currency":        "USD",
            },
            "recommendation": {
                "best_option": best,
                "reason":      f"Lowest price available — {best['price']}/night, "
                               f"rated {best['rating']} ({best['reviews']} reviews).",
            },
            "self_check": {
                "safe":    True,
                "warning": (
                    "Real hotel data retrieved from Google Hotels via SerpApi. "
                    "No booking or payment has been confirmed."
                ),
            },
        }

    # ── Mock / demo path (all other agents) ─────────────────────────────

    def _run_mock(
        self,
        query: str,
        agent_type: str,
        extracted: dict,
        rag_result,
        rag_category: str,
        steps: list,
    ) -> dict:
        availability = self.api.search_availability(agent_type, extracted)
        steps.append({
            "thought": "Tool/API Agent: search demo availability.",
            "output":  availability,
        })

        pricing = self.api.estimate_price(agent_type, extracted)
        steps.append({
            "thought": "Pricing Agent: estimate price.",
            "output":  pricing,
        })

        policy = self.api.get_policy(agent_type)
        steps.append({
            "thought": "Policy Agent: check policy from RAG/tool.",
            "output":  policy,
        })

        options = availability.get("options", [])
        best    = options[0] if options else {}
        steps.append({
            "thought": "Action Agent: recommend best option.",
            "output":  {"best_option": best, "reason": "Best demo option by price/rating"},
        })

        steps.append({
            "thought": "Critic Agent: evaluate answer.",
            "output":  "Looks useful; real API verification still required.",
        })

        steps.append({
            "thought": "Self-Check Agent: prevent unsafe claims.",
            "output":  {"safe": True, "warning": "Demo only. No real booking/payment confirmed."},
        })

        return {
            "crew_name":      f"{agent_type}RAGCrew",
            "crew_steps":     steps,
            "rag":            rag_result,
            "availability":   availability,
            "pricing":        pricing,
            "policy":         policy,
            "recommendation": {"best_option": best, "reason": "Best demo option by price/rating"},
            "critic":         "Looks useful; real API verification still required.",
            "self_check":     {"safe": True, "warning": "Demo only. No real booking/payment confirmed."},
        }
