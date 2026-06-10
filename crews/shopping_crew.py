from tools.rag_tool import RAGTool
from tools.shopping_tools import MockShoppingAPI, PaymentTool


class ShoppingCrew:
    def __init__(self):
        self.rag = RAGTool()
        self.api = MockShoppingAPI()
        self.payment = PaymentTool()

    def run(self, query: str, extracted: dict):
        steps = []

        plan = {"thought": "Shopping Planner Agent: understand product and constraints", "output": {"missing_fields": [k for k, v in extracted.items() if v == "not provided"]}}
        steps.append(plan)

        rag = {"thought": "RAG Retrieval Agent: retrieve product/spec/policy knowledge", "output": self.rag.search(query, "shopping")}
        steps.append(rag)

        search = {"thought": "Product Search Agent: search products", "output": self.api.search_products(extracted)}
        steps.append(search)

        compare = {"thought": "Comparison Agent: rank products", "output": {"best_product": search["output"][0], "alternatives": search["output"][1:]}}
        steps.append(compare)

        policy = {"thought": "Policy Agent: safe shopping rules", "output": self.api.policy()}
        steps.append(policy)

        cart = {"thought": "Cart Agent: prepare cart without buying", "output": self.api.prepare_cart(compare["output"]["best_product"])}
        steps.append(cart)

        payment = {"thought": "Payment Agent: prepare payment intent only", "output": self.payment.prepare_payment_intent(compare["output"]["best_product"]["price"], extracted.get("payment_method", "not provided"))}
        steps.append(payment)

        self_check = {"thought": "Self-Check Agent: verify no purchase/charge occurred", "output": {"safe": True, "warning": "No purchase made. No card charged. User confirmation required."}}
        steps.append(self_check)

        return {
            "crew_name": "ShoppingRAGCrew",
            "crew_steps": steps,
            "plan": plan["output"],
            "rag": rag["output"],
            "products": search["output"],
            "comparison": compare["output"],
            "policy": policy["output"],
            "cart": cart["output"],
            "payment": payment["output"],
            "self_check": self_check["output"]
        }
