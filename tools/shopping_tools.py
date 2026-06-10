import re


class MockShoppingAPI:
    def search_products(self, extracted: dict):
        product = extracted.get("product", "Product")
        budget_str = extracted.get("budget", "")
        # Parse budget ceiling
        ceiling = 9999
        m = re.search(r"\d+", budget_str.replace(",", ""))
        if m:
            ceiling = int(m.group())

        candidates = [
            {"name": "ASUS ProArt Studiobook 16", "price": "$1,299", "rating": "4.7",
             "reason": "RTX 4060, 32 GB RAM, excellent for AI/ML workloads"},
            {"name": "Lenovo ThinkPad X1 Extreme Gen 5", "price": "$1,449", "rating": "4.6",
             "reason": "Intel Core i7, NVIDIA RTX 3050 Ti, great build quality"},
            {"name": "Dell XPS 15 (2024)", "price": "$1,399", "rating": "4.8",
             "reason": "OLED display, RTX 4060, 32 GB RAM — top-tier for ML developers"},
            {"name": "HP Spectre x360 14", "price": "$1,199", "rating": "4.5",
             "reason": "Intel Evo, 16 GB RAM, versatile 2-in-1 for AI work"},
            {"name": "Acer Predator Helios 16", "price": "$1,099", "rating": "4.6",
             "reason": "RTX 4070, 16 GB RAM, gaming-grade GPU great for deep learning"},
        ]

        # Filter by budget
        def price_val(p):
            v = re.search(r"\d+", p["price"].replace(",", ""))
            return int(v.group()) if v else 9999

        filtered = [p for p in candidates if price_val(p) <= ceiling]
        if not filtered:
            filtered = candidates  # fallback — show all

        # Filter by brand if given
        brand = extracted.get("brand", "not provided").lower()
        if brand and brand != "not provided":
            brand_filtered = [p for p in filtered if brand in p["name"].lower()]
            if brand_filtered:
                filtered = brand_filtered

        return filtered if filtered else candidates

    def prepare_cart(self, product: dict):
        return {
            "cart_ready": True,
            "item": product,
            "checkout_status": "prepared_only_not_purchased",
            "requires_user_confirmation": True
        }

    def policy(self):
        return {
            "purchase": "Never purchase automatically.",
            "payment": "Never charge card automatically.",
            "confirmation": "User must explicitly confirm before real checkout."
        }

    def prepare_amazon_order(self, product: dict, address: dict, card: dict):
        """Simulate an Amazon order — demo only, no real API call."""
        return {
            "platform": "Amazon",
            "order_status": "DEMO_ONLY_NOT_PLACED",
            "product": product["name"],
            "delivery_address": address,
            "payment_last4": card.get("last4", "****"),
            "estimated_delivery": "3–5 business days",
            "amazon_link": f"https://www.amazon.com/s?k={product['name'].replace(' ', '+')}",
            "note": "This is a demo simulation. No real order was placed on Amazon."
        }


class PaymentTool:
    def prepare_payment_intent(self, amount: str, method: str = "not provided"):
        return {
            "payment_intent_prepared": True,
            "amount": amount,
            "method": method,
            "status": "demo_only_not_charged",
            "requires_user_confirmation": True
        }
