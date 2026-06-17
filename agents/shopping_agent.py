import re

from agents.base_agent import BaseAgent
from tools.shopping_data_store import ShoppingDataStore


class ShoppingAgent(BaseAgent):
    name = "ShoppingAgent"
    agent_type = "Shopping"
    rag_category = "shopping"

    use_case_options = ["AI/ML", "Gaming", "Programming", "Office Work"]

    def __init__(self):
        super().__init__()
        self.shopping_store = ShoppingDataStore()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        state = self.conversation_state.get(session_id)
        if (
            state.get("active_agent") == self.name
            and str(state.get("flow", "")).startswith("shopping_")
            and self.is_new_shopping_request(query)
        ):
            state = {}
        flow = state.get("flow")
        if state.get("active_agent") == self.name and flow == "shopping_requirements":
            return self.handle_requirement_answer(query, state, session_id)
        if state.get("active_agent") == self.name and flow == "shopping_cart_confirmation":
            return self.handle_cart_confirmation(query, state, session_id)
        if state.get("active_agent") == self.name and flow == "shopping_payment_confirmation":
            return self.handle_payment_confirmation(query, state, session_id)

        fields = self.extract_fields(query)
        missing = self.next_missing_field(fields)
        if missing:
            state = {
                "active_agent": self.name,
                "flow": "shopping_requirements",
                "fields": fields,
                "current_field": missing,
                "missing_fields": [missing],
            }
            self.conversation_state.set(session_id, state)
            return self.ask_requirement(query, state)
        return self.show_recommendations(query, fields, session_id)

    def handle_requirement_answer(self, query: str, state: dict, session_id: str):
        fields = state.get("fields", {})
        field = state.get("current_field", "")
        valid, value, message = self.validate_field(field, query)
        if not valid:
            return self.ask_requirement(query, state, validation_error=message)

        fields[field] = value
        missing = self.next_missing_field(fields)
        if missing:
            state["fields"] = fields
            state["current_field"] = missing
            state["missing_fields"] = [missing]
            self.conversation_state.set(session_id, state)
            return self.ask_requirement(query, state)

        return self.show_recommendations(query, fields, session_id)

    def ask_requirement(self, query: str, state: dict, validation_error: str = ""):
        field = state.get("current_field")
        questions = {
            "product": "What product do you want to buy?",
            "budget": "What is your budget?",
            "use_case": "What will you use it for?\n\n1. AI/ML\n2. Gaming\n3. Programming\n4. Office Work",
            "ram": "Preferred RAM?",
            "brand": "Preferred Brand?",
        }
        lines = ["ShoppingAgent / shopping", ""]
        if validation_error:
            lines.extend([validation_error, ""])
        lines.append(questions[field])
        return self.response(query, [
            "Question Agent: asking missing shopping requirement.",
        ], "\n".join(lines), {
            "flow": "shopping_requirements",
            "fields": state.get("fields", {}),
            "missing_fields": [field],
            "next_question": questions[field],
            "safety_layer_skip_actions": ["buy", "pay"],
        })

    def show_recommendations(self, query: str, fields: dict, session_id: str):
        products = self.shopping_store.search_products(fields)
        if not products:
            self.conversation_state.clear(session_id)
            return self.response(query, [
                "Product Search Agent: no matching products found.",
            ], "No matching products found in the local shopping database.", {
                "fields": fields,
                "products": [],
                "safety_layer_skip_actions": ["buy", "pay"],
            })

        best = products[0]
        state = {
            "active_agent": self.name,
            "flow": "shopping_cart_confirmation",
            "fields": fields,
            "products": products,
            "recommended_product": best,
            "missing_fields": ["cart_confirmation"],
        }
        self.conversation_state.set(session_id, state)

        answer = "\n".join([
            "Top Recommendations",
            "",
            self.format_products(products),
            "",
            "Recommended:",
            best["name"],
            "Reason:",
            best["reason"],
            "",
            f"Add {best['name']} to cart?",
            "yes/no",
        ])
        return self.response(query, [
            "Product Search Agent: searched product DB.",
            "Comparison Agent: ranked products by budget, use case, RAM, GPU, and price.",
            "Recommendation Agent: selected best fit.",
            "Cart Agent: waiting for add-to-cart confirmation.",
        ], answer, {
            "flow": "shopping_cart_confirmation",
            "fields": fields,
            "products": products,
            "recommended_product": best,
            "safety_layer_skip_actions": ["buy", "pay"],
        })

    def handle_cart_confirmation(self, query: str, state: dict, session_id: str):
        valid, value, message = self.validate_yes_no(query)
        if not valid:
            return self.response(query, [
                "Validation Agent: cart confirmation invalid.",
            ], "\n".join([
                message,
                "Please answer only: yes or no.",
            ]), {"flow": "shopping_cart_confirmation", "safety_layer_skip_actions": ["buy", "pay"]})

        if value == "no":
            self.conversation_state.clear(session_id)
            return self.response(query, ["Cart Agent: user declined cart."], "No item added to cart.", {
                "status": "not_added",
                "safety_layer_skip_actions": ["buy", "pay"],
            })

        product = state["recommended_product"]
        state["flow"] = "shopping_payment_confirmation"
        state["missing_fields"] = ["payment_confirmation"]
        self.conversation_state.set(session_id, state)
        return self.response(query, [
            "Cart Agent: item prepared in cart.",
            "Payment Agent: asking explicit payment confirmation.",
        ], "\n".join([
            "Cart Agent",
            "",
            f"Product: {product['name']}",
            f"Total price: ${product['price']}",
            "",
            f"Do you confirm payment of ${product['price']}?",
            "yes/no",
        ]), {
            "flow": "shopping_payment_confirmation",
            "cart": {"product": product, "status": "prepared"},
            "safety_layer_skip_actions": ["buy", "pay"],
        })

    def handle_payment_confirmation(self, query: str, state: dict, session_id: str):
        valid, value, message = self.validate_yes_no(query)
        product = state["recommended_product"]
        if not valid:
            return self.response(query, [
                "Validation Agent: payment confirmation invalid.",
            ], "\n".join([
                message,
                "Please answer only: yes or no.",
                "",
                f"Do you confirm payment of ${product['price']}?",
                "yes/no",
            ]), {"flow": "shopping_payment_confirmation", "safety_layer_skip_actions": ["buy", "pay"]})

        if value == "no":
            self.conversation_state.clear(session_id)
            return self.response(query, ["Payment Agent: user declined payment."], "Payment cancelled. No order placed.", {
                "status": "payment_cancelled",
                "safety_layer_skip_actions": ["buy", "pay"],
            })

        order = self.shopping_store.create_order(product)
        self.conversation_state.clear(session_id)
        return self.response(query, [
            "Payment Agent: explicit payment confirmation received.",
            "Order Confirmation Agent: order record generated.",
        ], "\n".join([
            "Payment Status: Success",
            "",
            "Order Confirmation",
            f"Order ID: {order['order_id']}",
            f"Product: {order['product_name']}",
            f"Total Paid: ${order['amount']}",
            "Status: Confirmed",
        ]), {
            "status": "confirmed",
            "order": order,
            "confirmed_actions": ["buy", "pay"],
        })

    def extract_fields(self, query: str):
        q = query.lower()
        fields = {
            "product": "not provided",
            "budget": "not provided",
            "use_case": "not provided",
            "ram": "not provided",
            "brand": "not provided",
        }
        for product in ["laptop", "phone", "shoes", "shirt", "groceries", "headphones", "monitor"]:
            if product in q:
                fields["product"] = product
                break
        budget = re.search(r"(?:under|below|budget:?)?\s*\$?\s*(\d[\d,]*)", q)
        if budget and ("$" in budget.group(0) or "under" in budget.group(0) or "below" in budget.group(0) or "budget" in budget.group(0)):
            fields["budget"] = f"${budget.group(1).replace(',', '')}"
        if any(term in q for term in ["ai", "ml", "machine learning"]):
            fields["use_case"] = "AI/ML"
        elif "gaming" in q:
            fields["use_case"] = "Gaming"
        elif "programming" in q or "coding" in q:
            fields["use_case"] = "Programming"
        ram = re.search(r"\b(8|16|32|64)\s*gb\b", q)
        if ram:
            fields["ram"] = f"{ram.group(1)}GB"
        for brand in ["lenovo", "asus", "acer", "dell", "apple", "samsung", "nike"]:
            if brand in q:
                fields["brand"] = brand.title()
        if "any" in q:
            fields["brand"] = "Any"
        return fields

    def next_missing_field(self, fields: dict):
        for field in ["product", "budget", "use_case", "ram", "brand"]:
            if fields.get(field) == "not provided":
                if field == "ram" and fields.get("product") != "laptop":
                    continue
                return field
        return None

    def validate_field(self, field: str, value: str):
        cleaned = value.strip()
        if field == "use_case":
            mapping = {"1": "AI/ML", "2": "Gaming", "3": "Programming", "4": "Office Work"}
            return True, mapping.get(cleaned, cleaned), ""
        if field == "budget":
            match = re.search(r"\d[\d,]*", cleaned)
            if not match:
                return False, None, "Invalid budget. Please enter an amount like $1200."
            return True, f"${match.group(0).replace(',', '')}", ""
        if field == "ram":
            match = re.search(r"(8|16|32|64)\s*gb", cleaned, re.I)
            if not match:
                return False, None, "Invalid RAM. Please enter a value like 32GB."
            return True, f"{match.group(1)}GB", ""
        if field == "brand":
            return True, cleaned.title() if cleaned.lower() != "any" else "Any", ""
        if not cleaned:
            return False, None, "Please enter a value."
        return True, cleaned.lower(), ""

    def validate_yes_no(self, value: str):
        cleaned = value.lower().strip()
        if cleaned not in {"yes", "no"}:
            return False, None, "Invalid response."
        return True, cleaned, ""

    def is_new_shopping_request(self, query: str):
        q = query.lower().strip()
        if q in {"yes", "no", "any"}:
            return False
        return any(phrase in q for phrase in [
            "i want",
            "show me",
            "find",
            "recommend",
            "compare",
            "order",
            "buy",
        ])

    def format_products(self, products: list[dict]):
        lines = []
        for index, product in enumerate(products, start=1):
            lines.extend([
                f"{index}. {product['name']}",
                f"   Price: ${product['price']}",
                f"   RAM: {product.get('ram', 'N/A')}",
                f"   GPU: {product.get('gpu', 'N/A')}",
                "",
            ])
        return "\n".join(lines).rstrip()
