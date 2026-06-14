import re
from agents.coding_agent import CodingAgent
from agents.deployment_agent import DeploymentAgent
from agents.healthcare_agent import HealthcareAgent
from agents.research_agent import ResearchAgent
from agents.resume_agent import ResumeAgent
from agents.shopping_agent import ShoppingAgent
from agents.travel_agent import TravelAgent
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.movie_agent import MovieAgent
from agents.restaurant_agent import RestaurantAgent
from agents.train_agent import TrainAgent
from agents.bus_agent import BusAgent
from agents.cab_agent import CabAgent
from agents.event_agent import EventAgent
from agents.calculator_agent import CalculatorAgent
from agents.vacation_package_agent import VacationPackageAgent
from agents.payment_agent import PaymentAgent
from agents.coupon_agent import CouponAgent
from agents.review_agent import ReviewAgent
from agents.cancellation_agent import CancellationAgent
from agents.notification_agent import NotificationAgent
from agents.support_agent import SupportAgent
from agents.general_agent import GeneralAgent
from agents.country_agent import CountryAgent
from tools.query_corrector import QueryCorrector
from tools.safety_layer import SafetyLayer


def has_any_phrase(q: str, phrases: list[str]) -> bool:
    return any(p in q for p in phrases)


def has_any_word(q: str, words: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", q) for w in words)


DEPLOYMENT_KEYWORDS = [
    "deploy", "deployment", "containerize", "dockerize",
    "docker", "dockerfile", "docker compose", "docker-compose",
    "kubernetes", "k8s", "kubectl", "helm", "pod", "ingress",
    "aws", "ec2", "ecs", "fargate", "elastic beanstalk",
    "azure", "azure container",
    "gcp", "cloud run", "google cloud",
    "railway", "render", "fly.io", "heroku", "vercel",
    "nginx", "gunicorn", "uvicorn",
    "ci/cd", "github actions", "gitlab ci", "jenkins", "circleci",
    "terraform", "ansible", "infrastructure as code",
    "self-host", "self host", "vps", "server setup",
]


class AgentRouter:
    name = "AgentRouter"

    def __init__(self):
        self.query_corrector = QueryCorrector()
        self.coding_agent = CodingAgent()
        self.deployment_agent = DeploymentAgent()
        self.healthcare_agent = HealthcareAgent()
        self.research_agent = ResearchAgent()
        self.resume_agent = ResumeAgent()
        self.shopping_agent = ShoppingAgent()
        self.travel_agent = TravelAgent()
        self.flight_agent = FlightAgent()
        self.calculator_agent = CalculatorAgent()
        self.hotel_agent = HotelAgent()
        self.movie_agent = MovieAgent()
        self.restaurant_agent = RestaurantAgent()
        self.train_agent = TrainAgent()
        self.bus_agent = BusAgent()
        self.cab_agent = CabAgent()
        self.event_agent = EventAgent()
        self.vacation_package_agent = VacationPackageAgent()
        self.payment_agent = PaymentAgent()
        self.coupon_agent = CouponAgent()
        self.review_agent = ReviewAgent()
        self.cancellation_agent = CancellationAgent()
        self.notification_agent = NotificationAgent()
        self.support_agent = SupportAgent()
        self.general_agent = GeneralAgent()
        self.country_agent = CountryAgent()
        self.safety_layer = SafetyLayer()

    def route(self, query: str):
        q = query.lower()

        # Priority: Calculator -> Deployment -> Healthcare -> Shopping
        # -> Booking/Travel -> Coding -> General.
        if self.is_math_query(query):
            return "calculator", self.calculator_agent

        if self.is_deployment_query(q):
            return "deployment", self.deployment_agent

        if any(k in q for k in [
            "health", "hospital", "doctor", "symptom", "pain", "diabetes",
            "chest pain", "medical", "fever", "breathing", "blood pressure",
        ]):
            return "healthcare", self.healthcare_agent

        shopping_intent_phrases = [
            "i want to buy", "buy", "purchase", "shopping", "recommend",
            "best", "compare", "price of", "under $", "deal", "discount",
            "add to cart",
        ]
        shopping_products = [
            "phone", "laptop", "headphones", "monitor", "keyboard", "mouse",
            "tablet", "camera", "gpu", "iphone", "samsung", "apple", "pixel",
        ]
        if has_any_phrase(q, shopping_intent_phrases) and has_any_word(q, shopping_products):
            return "shopping", self.shopping_agent

        # Booking and travel routes stay ahead of coding so transactional intent
        # wins even when the user mentions an app, script, API, or code.
        if any(k in q for k in ["payment", "pay", "card", "checkout", "wallet"]):
            return "payment", self.payment_agent
        if any(k in q for k in ["flight", "plane", "airport", "airline"]):
            return "flight", self.flight_agent
        if any(k in q for k in ["hotel", "room", "stay", "check-in", "checkout", "resort"]):
            return "hotel", self.hotel_agent
        if any(k in q for k in ["movie", "cinema", "theater", "showtime", "ticket"]):
            return "movie", self.movie_agent
        if any(k in q for k in ["restaurant", "dinner", "lunch", "table", "reservation", "food"]):
            return "restaurant", self.restaurant_agent
        if any(k in q for k in ["train", "railway", "rail"]):
            return "train", self.train_agent
        if any(k in q for k in ["bus", "coach"]):
            return "bus", self.bus_agent
        if any(k in q for k in ["cab", "taxi", "uber", "lyft", "ride"]):
            return "cab", self.cab_agent
        if any(k in q for k in ["event", "concert", "game", "festival", "conference"]):
            return "event", self.event_agent
        if any(k in q for k in ["vacation", "package", "trip package", "holiday"]):
            return "vacation_package", self.vacation_package_agent
        if any(k in q for k in ["travel", "trip", "itinerary", "tour", "destination"]):
            return "travel", self.travel_agent
        if any(k in q for k in ["coupon", "promo", "discount", "offer"]):
            return "coupon", self.coupon_agent
        if any(k in q for k in ["review", "rating", "feedback"]):
            return "review", self.review_agent
        if any(k in q for k in ["cancel", "cancellation", "reschedule", "change booking"]):
            return "cancellation", self.cancellation_agent
        if any(k in q for k in ["notify", "notification", "reminder", "alert"]):
            return "notification", self.notification_agent
        if any(k in q for k in [
            "customer support", "live agent", "contact support",
            "raise ticket", "complaint", "helpdesk",
        ]):
            return "support", self.support_agent

        if self.is_general_factual_question(q):
            # Country-specific queries get a dedicated agent
            if self._is_country_query(q):
                return "country", self.country_agent
            return "general", self.general_agent

        if any(k in q for k in [
            "code", "program", "c++", "cpp", "python", "java", "algorithm",
            "leetcode", "codeforces", "dijkstra", "compile", "debug",
            "microservice", "api endpoint", "rest api", "graphql",
            "fastapi", "flask", "django", "express", "spring boot",
            "git", "github", "gitlab",
            "sql", "database", "mongodb", "postgres", "redis",
            "function", "class", "variable", "loop", "recursion",
            "sorting", "linked list", "binary tree", "stack", "queue",
            "script", "bash", "shell", "powershell",
        ]):
            return "coding", self.coding_agent

        if any(k in q for k in ["research", "paper", "literature", "survey", "research gap", "methodology"]):
            return "research", self.research_agent
        if any(k in q for k in ["resume", "cv", "ats", "job description", "linkedin", "experience bullet"]):
            return "resume", self.resume_agent

        general_question_phrases = [
            "who invented", "who discovered", "who created", "who won",
            "who defeated", "who founded", "who is", "what is", "when was",
            "when did", "where is", "why is", "how does", "how long",
            "capital of", "population of", "gdp of",
        ]
        if has_any_phrase(q, general_question_phrases):
            if self._is_country_query(q):
                return "country", self.country_agent
            return "general", self.general_agent

        return "general", self.general_agent

    def get_agent_by_name(self, agent_name: str):
        for value in self.__dict__.values():
            if hasattr(value, "name") and value.name == agent_name:
                return value
        return self.general_agent

    def run_with_agent_name(self, agent_name: str, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        agent = self.get_agent_by_name(agent_name)
        try:
            result = agent.run(query, prefilled_fields=prefilled_fields, session_id=session_id)
        except TypeError:
            result = agent.run(query)

        result["router"] = {
            "root": "User",
            "router_agent": "AgentRouter",
            "selected_leaf_agent": agent.name,
            "route": agent.agent_type.lower()
        }
        return self.safety_layer.enforce(result, query=query, route=result["router"]["route"])

    def is_deployment_query(self, q: str) -> bool:
        """Return True if the query is about deploying/containerising an application."""
        return any(kw in q for kw in DEPLOYMENT_KEYWORDS)

    def is_general_factual_question(self, q: str) -> bool:
        """Return True for fact-seeking questions that may mention coding terms."""
        factual_starts = (
            "who invented", "who discovered", "who created", "who won",
            "who defeated", "who founded", "who is", "what is", "when was",
            "when did", "where is", "why is", "how does", "how long",
        )
        if q.startswith(factual_starts):
            coding_actions = (
                "write", "generate", "create code", "implement", "build",
                "debug", "fix", "compile", "run", "solve", "leetcode",
            )
            return not has_any_word(q, list(coding_actions))
        return has_any_phrase(q, ["capital of", "population of", "gdp of"])

    @staticmethod
    def _is_country_query(q: str) -> bool:
        """Return True if the query is asking about a country attribute."""
        return bool(re.search(
            r"\b(capital|population|currency|currenc|language|continent|area|gdp|gross domestic product)\s+"
            r"(?:city\s+)?of\b"
            r"|\bwhat\s+continent\s+is\b"
            r"|\bofficial\s+language",
            q, re.I
        ))

    def is_math_query(self, query: str) -> bool:
        """
        Returns True only for genuine arithmetic expressions.

        Rules:
        1. If the query contains 3+ consecutive English letters forming a word
           beyond known math function names, it is not math.
        2. Math function names (sqrt, sin, cos, tan, log, abs, round) trigger True.
        3. Pure expressions like "43 * 23", "(5+3)/2", "2**10" trigger True.
        """
        import re as _re

        q = query
        if "[Free LLM Tree Guidance]" in q:
            q = q.split("[Free LLM Tree Guidance]", 1)[0]
        if "[Uploaded File Context]" in q:
            q = q.split("[Uploaded File Context]", 1)[0]
        q = q.strip()

        q_clean = q.replace("x", "*").replace("^", "**")
        q_clean = _re.sub(
            r"^\s*(calculate|solve|compute|evaluate|what\s+is|what's)\s*",
            "", q_clean, flags=_re.I
        ).strip()

        math_words = {"sqrt", "sin", "cos", "tan", "log", "log10", "abs", "round", "pi"}
        words_in_query = _re.findall(r"[a-zA-Z]+", q_clean)
        non_math_words = [w.lower() for w in words_in_query if w.lower() not in math_words]
        if non_math_words:
            return False

        if any(w in q_clean.lower() for w in math_words - {"pi"}):
            return True

        has_digit = bool(_re.search(r"\d", q_clean))
        has_operator = bool(_re.search(r"\d\s*[\+\-\*\/\%\^]\s*\d", q_clean))
        only_math = bool(_re.fullmatch(r"[\d\s\.\+\-\*\/\(\)\%\^]+", q_clean))

        return has_digit and has_operator and only_math

    def run(self, query: str, session_id: str = "default", original_query: str = ""):
        route_name, agent = self.route(original_query or query)
        try:
            result = agent.run(query, session_id=session_id)
        except TypeError:
            result = agent.run(query)

        result["router"] = {
            "root": "User",
            "router_agent": "AgentRouter",
            "selected_leaf_agent": agent.name,
            "route": route_name
        }
        return self.safety_layer.enforce(result, query=query, route=route_name)
