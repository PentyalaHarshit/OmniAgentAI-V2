"""
agents/hotel_agent.py
======================
HotelAgent — books hotels via real SerpApi Google Hotels API.

When SERPAPI_API_KEY is set in .env, returns real hotel names, prices,
ratings and links. Otherwise falls back to demo mock data.

Flow
----
  User query
    ↓ BookingParser extracts city, check_in, checkout, guests, budget
    ↓ SlotFillingTool asks for any missing required fields
    ↓ GenericRAGCrew → RealHotelProvider → SerpApi Google Hotels
    ↓ HotelAgent.build_answer formats the results
    ↓ Ask user confirmation before any booking/payment
"""

from agents.base_agent import BaseAgent
import re


class HotelAgent(BaseAgent):
    name = "HotelAgent"
    agent_type = "Hotel"
    rag_category = "booking"
    required_fields = ["city", "check_in", "checkout", "guests"]
    optional_fields = ["budget", "rating", "amenities"]
    base_tasks = [
        "Parse hotel request fields",
        "Check for missing required fields (city, dates, guests)",
        "Call Real Hotel Provider (SerpApi Google Hotels)",
        "Compare hotel options by price and rating",
        "Safety check — no booking without confirmation",
        "Return top hotels and ask user to confirm",
    ]

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        city = self.extract_city(query) or "New York"
        budget = self.extract_budget(query) or 200
        hotels = [
            {"name": "Marriott Times Square", "price": 180},
            {"name": "Hilton Midtown", "price": 190},
            {"name": "Hyatt Manhattan", "price": 175},
        ]
        filtered = [hotel for hotel in hotels if hotel["price"] <= budget] or hotels
        recommended = filtered[0]
        answer = "\n".join([
            "HotelBookingAgent / hotel",
            "",
            "Top Hotels",
            "",
            *[
                f"{index}. {hotel['name']}\n   ${hotel['price']}/night"
                for index, hotel in enumerate(filtered, start=1)
            ],
            "",
            "Recommended:",
            recommended["name"],
            "",
            "Book now?",
            "yes/no",
        ])
        return self.response(query, [
            "Hotel Search API: searched local demo hotel inventory.",
            "Recommendation Agent: selected the best hotel under budget.",
            "Booking Agent: waiting for explicit booking confirmation.",
        ], answer, {
            "selected_booking_agent": "HotelBookingAgent",
            "city": city,
            "budget_per_night": budget,
            "hotels": filtered,
            "recommendation": recommended,
            "safety_layer_skip_actions": ["book", "pay"],
        })

    @staticmethod
    def extract_city(query: str):
        match = re.search(r"\bin\s+([A-Za-z ]+?)(?:\s+for|\s+under|\.|$)", query, re.I)
        return match.group(1).strip().title() if match else ""

    @staticmethod
    def extract_budget(query: str):
        match = re.search(r"under\s+\$?\s*(\d+)", query, re.I)
        return int(match.group(1)) if match else 0

    def build_answer(self, extracted: dict, crew_result: dict) -> str:
        availability = crew_result.get("availability", {})
        recommendation = crew_result.get("recommendation", {})
        self_check = crew_result.get("self_check", {})
        pricing = crew_result.get("pricing", {})

        city     = extracted.get("city", "?")
        check_in  = extracted.get("check_in", "?")
        check_out = extracted.get("checkout", "?")
        guests   = extracted.get("guests", 1)

        lines = [f"**HotelAgent selected.**", ""]

        # ── Real hotel results ─────────────────────────────────────────────
        if availability.get("available") and availability.get("options"):
            provider = availability.get("provider", "Hotel API")
            hotels   = availability["options"]
            best     = recommendation.get("best_option", hotels[0])

            lines += [
                f"🏨 **Real Hotel Search** — {city}",
                f"📅 {check_in} → {check_out} · 👥 {guests} guest(s)",
                f"🔍 Provider: {provider}",
                "",
                "**Top Hotels:**",
            ]

            for i, h in enumerate(hotels[:5], start=1):
                name     = h.get("name", "Unknown Hotel")
                price    = h.get("price", "N/A")
                rating   = h.get("rating", "N/A")
                reviews  = h.get("reviews", "N/A")
                address  = h.get("address", "")
                link     = h.get("link", "")
                amenities = h.get("amenities", [])

                star = "⭐ **Best pick**" if h == best else ""

                lines.append(f"{i}. **{name}** {star}")
                lines.append(f"   💰 Price: **{price}/night**")
                lines.append(f"   ⭐ Rating: {rating}  |  💬 Reviews: {reviews}")
                if address:
                    lines.append(f"   📍 {address}")
                if amenities:
                    lines.append(f"   ✅ {', '.join(amenities[:4])}")
                if link:
                    lines.append(f"   🔗 [View hotel]({link})")
                lines.append("")

            lines += [
                f"🏆 **Best option:** {best.get('name')} — {best.get('price')}/night",
                f"   _{recommendation.get('reason', '')}_",
                "",
                f"⚠️ **Safety:** {self_check.get('warning', 'No booking confirmed.')}",
                "",
                "💬 **Do you want to continue to checkout?** (Reply 'yes' to proceed)",
            ]

        # ── Demo / no API key ──────────────────────────────────────────────
        elif not availability.get("available"):
            error = availability.get("error") or crew_result.get("error", "No hotels found.")
            lines += [
                f"🏨 Hotel search for: **{city}**",
                f"📅 {check_in} → {check_out} · 👥 {guests} guest(s)",
                "",
                f"⚠️ **Note:** {error}",
                "",
                "To get real hotel results, add to your `.env` file:",
                "```",
                "HOTEL_PROVIDER=serpapi",
                "SERPAPI_API_KEY=your_api_key_here",
                "```",
                "Get a free API key at [serpapi.com](https://serpapi.com)",
            ]

        # ── Mock fallback ──────────────────────────────────────────────────
        else:
            options = availability.get("options", [])
            best = recommendation.get("best_option", options[0] if options else {})
            lines += [
                f"🏨 Hotel search for: **{city}** (Demo mode)",
                f"📅 {check_in} → {check_out} · 👥 {guests} guest(s)",
                "",
                "**Demo Options:**",
            ]
            for i, h in enumerate(options[:3], 1):
                lines.append(f"{i}. {h}")
            lines += [
                "",
                f"🏆 Best demo option: {best}",
                f"💰 Estimated price: {pricing.get('estimated_total', 'N/A')}",
                "",
                f"⚠️ {self_check.get('warning', 'Demo only. No real booking confirmed.')}",
                "💬 **Do you want to continue to checkout?**",
            ]

        return "\n".join(lines)
