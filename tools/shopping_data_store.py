import json
import re
from datetime import datetime
from pathlib import Path


DEFAULT_PRODUCTS = [
    {
        "product_id": "LAP-001",
        "category": "laptop",
        "name": "Lenovo Legion 5",
        "price": 1199,
        "ram": "32GB",
        "storage": "1TB SSD",
        "gpu": "RTX 4060",
        "brand": "Lenovo",
        "use_cases": ["AI/ML", "Gaming", "Programming"],
        "reason": "Best GPU performance for AI workloads under $1200.",
    },
    {
        "product_id": "LAP-002",
        "category": "laptop",
        "name": "ASUS TUF A15",
        "price": 1149,
        "ram": "32GB",
        "storage": "1TB SSD",
        "gpu": "RTX 4050",
        "brand": "ASUS",
        "use_cases": ["AI/ML", "Gaming", "Programming"],
        "reason": "Strong price-to-performance with enough RAM for local ML work.",
    },
    {
        "product_id": "LAP-003",
        "category": "laptop",
        "name": "Acer Predator Helios Neo",
        "price": 1189,
        "ram": "32GB",
        "storage": "1TB SSD",
        "gpu": "RTX 4060",
        "brand": "Acer",
        "use_cases": ["AI/ML", "Gaming"],
        "reason": "RTX 4060 and 32GB RAM make it a strong AI development option.",
    },
    {
        "product_id": "LAP-004",
        "category": "laptop",
        "name": "Dell XPS 13",
        "price": 999,
        "ram": "16GB",
        "storage": "512GB SSD",
        "gpu": "Integrated",
        "brand": "Dell",
        "use_cases": ["Programming", "Office Work"],
        "reason": "Portable programming laptop, but not ideal for GPU-heavy AI work.",
    },
    {
        "product_id": "PHONE-001",
        "category": "phone",
        "name": "Samsung Galaxy S25",
        "price": 799,
        "ram": "12GB",
        "storage": "256GB",
        "gpu": "Mobile GPU",
        "brand": "Samsung",
        "use_cases": ["Camera", "General"],
        "reason": "Latest Samsung option under $800 with strong camera features.",
    },
]


class ShoppingDataStore:
    def __init__(self, data_dir: str = "shopping_data"):
        self.data_dir = Path(data_dir)
        self.products_path = self.data_dir / "products.json"
        self.orders_path = self.data_dir / "orders.json"

    def ensure_ready(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.products_path.exists():
            self.write_json(self.products_path, DEFAULT_PRODUCTS)
        if not self.orders_path.exists():
            self.write_json(self.orders_path, [])
        return {
            "products_json": str(self.products_path),
            "orders_json": str(self.orders_path),
        }

    def search_products(self, fields: dict):
        self.ensure_ready()
        products = self.load_json(self.products_path)
        category = self.clean(fields.get("product", ""))
        budget = self.parse_budget(fields.get("budget", ""))
        ram = self.clean(fields.get("ram", ""))
        brand = self.clean(fields.get("brand", ""))
        use_case = self.clean(fields.get("use_case", ""))

        matches = []
        for product in products:
            if category and category not in self.clean(product.get("category", "")):
                continue
            if budget and int(product.get("price", 0)) > budget:
                continue
            if ram and ram != "any" and ram not in self.clean(product.get("ram", "")):
                continue
            if brand and brand != "any" and brand != self.clean(product.get("brand", "")):
                continue
            product = product.copy()
            product["score"] = self.score_product(product, use_case, ram)
            matches.append(product)

        return sorted(matches, key=lambda item: (-item["score"], item["price"]))[:5]

    def create_order(self, product: dict, payment_method: str = "demo_payment"):
        self.ensure_ready()
        orders = self.load_json(self.orders_path)
        order_id = f"SHOP-{datetime.now().strftime('%Y%m%d')}-{len(orders) + 1:03d}"
        order = {
            "order_id": order_id,
            "product_id": product.get("product_id", ""),
            "product_name": product.get("name", ""),
            "amount": int(product.get("price", 0)),
            "payment_status": "paid",
            "order_status": "confirmed",
            "payment_method": payment_method,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        orders.append(order)
        self.write_json(self.orders_path, orders)
        return order

    def score_product(self, product: dict, use_case: str, ram: str):
        score = 50
        use_cases = [self.clean(item) for item in product.get("use_cases", [])]
        if use_case and any(use_case in item for item in use_cases):
            score += 25
        if "ai" in use_case or "ml" in use_case or "machine learning" in use_case:
            if "rtx 4060" in self.clean(product.get("gpu", "")):
                score += 20
            elif "rtx 4050" in self.clean(product.get("gpu", "")):
                score += 14
            if "32gb" in self.clean(product.get("ram", "")):
                score += 10
        if ram and ram != "any" and ram in self.clean(product.get("ram", "")):
            score += 10
        if ("ai" in use_case or "ml" in use_case or "machine learning" in use_case) and product.get("product_id") == "LAP-001":
            score += 5
        return score

    def load_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def write_json(self, path: Path, rows: list[dict]):
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    @staticmethod
    def parse_budget(value: str):
        match = re.search(r"\d[\d,]*", str(value or ""))
        return int(match.group(0).replace(",", "")) if match else 0

    @staticmethod
    def clean(value: str):
        return re.sub(r"\s+", " ", str(value or "").strip().lower())
