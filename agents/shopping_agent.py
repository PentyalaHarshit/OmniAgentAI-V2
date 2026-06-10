import re
from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from tools.slot_filling import SlotFillingTool
from tools.conversation_state import ConversationState
from crews.shopping_crew import ShoppingCrew


class ShoppingAgent(BaseAgent):
    name = "ShoppingAgent"
    agent_type = "Shopping"
    rag_category = "shopping"
    required_fields = ["product", "budget", "brand", "use_case", "payment_method"]
    optional_fields = ["brand", "use_case", "payment_method"]

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = ShoppingCrew()
        self.slot_filling = SlotFillingTool()
        self.conversation_state = ConversationState()

    def extract_shopping(self, query: str):
        q = query.lower()
        data = {k: "not provided" for k in self.required_fields}

        products = ["laptop", "phone", "headphones", "monitor", "keyboard", "mouse", "tablet", "camera"]
        for p in products:
            if p in q:
                data["product"] = p.title()

        money = re.search(r"\$\s?\d[\d,]*|\bunder\s+\$?\d[\d,]*|\bbelow\s+\$?\d[\d,]*", q)
        if money:
            data["budget"] = money.group(0)

        if "ai" in q or "machine learning" in q or "programming" in q or "coding" in q or "ml" in q:
            data["use_case"] = "AI/programming"

        for brand in ["apple", "dell", "hp", "lenovo", "asus", "acer", "samsung"]:
            if brand in q:
                data["brand"] = brand.title()

        if "card" in q or "credit" in q or "debit" in q or "visa" in q or "mastercard" in q:
            data["payment_method"] = "card"

        return data

    def _build_checkout_html(self, best: dict, amazon: dict) -> str:
        """Render an inline checkout card with address, card fields, and confirm button."""
        return (
            "\n\n---CHECKOUT_FORM---\n"
            f"PRODUCT_NAME:{best['name']}\n"
            f"PRODUCT_PRICE:{best['price']}\n"
            f"PRODUCT_RATING:{best['rating']}\n"
            f"AMAZON_LINK:{amazon['amazon_link']}\n"
            f"ESTIMATED_DELIVERY:{amazon['estimated_delivery']}\n"
            "---END_CHECKOUT_FORM---"
        )

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        tasks = [
            "Understand product request",
            "Generate product-search strategies",
            "Retrieve shopping RAG",
            "Ask missing product/budget",
            "Search products",
            "Compare products",
            "Collect delivery address",
            "Collect card details",
            "Prepare cart safely",
            "Prepare payment intent safely",
            "Simulate Amazon delivery",
            "Self-check no real purchase occurred"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=16)
        extracted = self.extract_shopping(query)
        extracted = self.merge_fields(extracted, prefilled_fields)

        missing = self.slot_filling.missing_fields(extracted, self.optional_fields)

        if missing:
            question = self.slot_filling.next_question(self.agent_type, missing)
            self.conversation_state.start_or_update(session_id, self.name, extracted, missing)
            answer = f"ShoppingAgent selected.\n\nI need one more detail before continuing.\n\n{question}"
            return self.response(query, thoughts + [f"Slot Filling Agent: ask for {missing[0]}"], answer, {
                "slot_filling": True,
                "missing_fields": missing,
                "fields": extracted,
                "next_question": question
            })

        self.conversation_state.clear(session_id)
        crew_result = self.crew.run(query, extracted)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        best = crew_result["comparison"]["best_product"]

        # Simulate Amazon order info
        amazon = self.crew.api.prepare_amazon_order(
            best,
            address={"street": "", "city": "", "state": "", "zip": "", "country": ""},
            card={"last4": ""}
        )

        checkout_block = self._build_checkout_html(best, amazon)

        answer = (
            "**Shopping Agent** — AI/ML Laptop Recommendation\n\n"
            f"RAG Sources: {crew_result['rag']['sources']}\n\n"
            "**Collected Fields:**\n"
            + "\n".join(f"- {k}: {v}" for k, v in extracted.items())
            + "\n\n**Best Product Recommendation:**\n"
            f"- **Name:** {best['name']}\n"
            f"- **Price:** {best['price']}\n"
            f"- **Rating:** {best['rating']} ⭐\n"
            f"- **Why:** {best['reason']}\n\n"
            "**Other Options:**\n"
            + "\n".join(
                f"- {p['name']} — {p['price']} ({p['rating']}⭐) — {p['reason']}"
                for p in crew_result["comparison"].get("alternatives", [])[:2]
            )
            + "\n\n> 🛡️ **Safety:** No product was purchased and no payment was charged. "
            "Explicit confirmation required.\n"
            + checkout_block
        )

        return self.response(query, thoughts + crew_thoughts, answer, {
            "slot_filling": False,
            "extracted": extracted,
            "crew_result": crew_result,
            "checkout": {
                "product": best,
                "amazon": amazon,
                "show_checkout_form": True
            }
        })
