import re
from agents.coding_agent import CodingAgent
from agents.coding_ai_router import CodingAIRouter, route_user_query
from agents.deployment_agent import DeploymentAgent
from agents.healthcare_agent import HealthcareAgent
from agents.research_agent import ResearchAgent
from agents.resume_agent import ResumeAgent
from agents.shopping_agent import ShoppingAgent
from agents.finance_agent import FinanceAgent
from agents.fitness_agent import FitnessAgent
from agents.recipe_agent import RecipeAgent
from agents.local_discovery_agent import LocalDiscoveryAgent
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
from agents.web_agent import WebAgent
from agents.sports_agent import SportsAgent
from agents.learning_agent import LearningAgent
from agents.quiz_agent import QuizAgent
from agents.country_agent import CountryAgent
from agents.code_review_agent import CodeReviewAgent
from agents.debug_agent import DebugAgent
from agents.test_case_agent import TestCaseAgent
from agents.algorithm_agent import AlgorithmAgent
from agents.system_design_agent import SystemDesignAgent
from agents.ml_agent import MLAgent
from agents.data_science_agent import DataScienceAgent
from agents.rag_agent import RAGAgent
from agents.mlops_agent import MLOpsAgent
from agents.ai_architect_agent import AIArchitectAgent
from agents.self_correction_agent import SelfCorrectionAgent
from agents.loan_agent import LoanAgent
from agents.tensorflow_agent import TensorFlowAgent
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

SPORTS_KEYWORDS = [
    "world cup",
    "fifa",
    "ipl",
    "nba",
    "nfl",
    "premier league",
    "epl",
    "football",
    "soccer",
    "cricket",
    "basketball",
    "standings",
    "points table",
    "league table",
    "league",
]

GENERAL_AGENT_TOPICS = [
    "agentic ai",
    "retrieval-augmented generation",
    "retrieval augmented generation",
    "rag",
    "crewai",
    "autogen",
    "vector database",
    "quantum computing",
    "black holes",
    "crispr",
    "multi-agent ai",
    "multi agent ai",
    "agentic rag",
    "tree of thoughts",
    "chain of thought",
    "ai model releases",
    "autonomous ai agents",
    "ai news",
    "aws",
    "distributed systems",
    "kubernetes",
    "world wide web",
    "artificial intelligence",
    "programming languages",
]

GENERAL_AGENT_STARTERS = [
    "what is",
    "what are",
    "explain",
    "how does",
    "how do",
    "what causes",
    "summarize",
    "compare",
    "teach me",
    "find recent research papers",
    "find research papers",
    "latest trends",
    "latest developments",
    "latest ai model releases",
    "today's major",
    "history of",
    "can ai",
    "research",
]

LEARNING_KEYWORDS = [
    "teach me",
    "tutorial",
    "learn",
    "course",
    "roadmap",
]

QUIZ_KEYWORDS = [
    "multiple choice",
    "mcq",
    "quiz",
    "which of the following",
    "a)",
    "b)",
    "c)",
    "d)",
    "correct answer",
]

CODING_KEYWORDS = [
    "code", "create", "implement", "solve", "program", "c++", "cpp", "python", "java", "algorithm",
    "leetcode", "compile", "debug", "data structure",
    "microservice", "api endpoint", "rest api", "graphql",
    "fastapi", "flask", "django", "express", "spring boot",
    "git", "github", "gitlab",
    "sql", "database", "mongodb", "postgres", "redis",
    "function", "class", "variable", "loop", "recursion",
    "sorting", "linked list", "binary tree", "stack", "queue",
    "script", "bash", "shell", "powershell",
    "web crawler", "crawler", "scraper", "multithreaded",
    "threading", "requests", "beautifulsoup",
    "segment tree", "range sum", "range query", "range queries",
    "range update", "fenwick", "binary indexed tree", "bit tree",
    "heavy light decomposition", "heavy-light decomposition", "hld",
    "lca", "binary lifting", "path maximum", "path query",
    "dfs", "bfs", "dijkstra", "dynamic programming", "graph", "tree",
    "shortest path", "priority queue", "heap", "trie", "kmp",
    "disjoint set", "union find", "dsu",
    "dp", "memoization", "tabulation", "competitive programming",
    "cp algorithm",
    "lowest common ancestor", "kth ancestor", "tree queries",
    "tree query", "graph algorithm", "cpp17", "c++17",
    "mo algorithm", "mo's algorithm", "centroid decomposition",
    "dsu on tree", "small to large", "convex hull trick",
    "li chao", "divide and conquer dp", "0-1 bfs", "zero one bfs",
]

STRONG_CODING_PATTERNS = [
    r"\b(?:solve|implement|create|generate|write|debug|compile)\b.*\b(?:algorithm|cpp|c\+\+|python|java|graph|tree|dp|segment tree|lca|hld)\b",
    r"\b(?:segment tree|fenwick|binary indexed tree|lca|lowest common ancestor|hld|heavy light decomposition)\b",
    r"\b(?:dijkstra|bellman ford|0-1 bfs|zero one bfs|dfs|bfs|dsu|union find|dynamic programming|dp)\b",
]


class AgentRouter:
    name = "AgentRouter"

    def __init__(self):
        self.query_corrector = QueryCorrector()
        self.coding_ai_router = CodingAIRouter()
        self.coding_agent = CodingAgent()
        self.deployment_agent = DeploymentAgent()
        self.healthcare_agent = HealthcareAgent()
        self.research_agent = ResearchAgent()
        self.resume_agent = ResumeAgent()
        self.shopping_agent = ShoppingAgent()
        self.finance_agent = FinanceAgent()
        self.fitness_agent = FitnessAgent()
        self.recipe_agent = RecipeAgent()
        self.local_discovery_agent = LocalDiscoveryAgent()
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
        self.web_agent = WebAgent()
        self.sports_agent = SportsAgent()
        self.learning_agent = LearningAgent()
        self.quiz_agent = QuizAgent()
        self.country_agent = CountryAgent()
        self.code_review_agent = CodeReviewAgent()
        self.debug_agent = DebugAgent()
        self.test_case_agent = TestCaseAgent()
        self.algorithm_agent = AlgorithmAgent()
        self.system_design_agent = SystemDesignAgent()
        self.ml_agent = MLAgent()
        self.data_science_agent = DataScienceAgent()
        self.rag_agent = RAGAgent()
        self.mlops_agent = MLOpsAgent()
        self.ai_architect_agent = AIArchitectAgent()
        self.self_correction_agent = SelfCorrectionAgent()
        self.loan_agent = LoanAgent()
        self.tensorflow_agent = TensorFlowAgent()
        self.safety_layer = SafetyLayer()
        self.active_conversations = {}  # Store active conversation states by session_id

    def route(self, query: str):
        q = query.lower()

        # Priority: Calculator -> Loan -> Healthcare -> Shopping
        # -> Booking/Travel -> Coding/AI -> General.
        if self.is_math_query(query):
            return "calculator", self.calculator_agent

        if self.is_sports_query(q):
            return "sports", self.sports_agent

        if self.is_loan_query(q):
            return "loan", self.loan_agent

        if self.is_quiz_query(query):
            return "quiz", self.quiz_agent

        if self.is_learning_query(q):
            return "learning", self.learning_agent

        if any(k in q for k in ["tourist attractions", "top tourist", "top places", "attractions in", "places to visit"]):
            return "local_discovery", self.local_discovery_agent

        if self.is_general_agent_query(q):
            if self._is_country_query(q):
                return "country", self.country_agent
            return "general", self.general_agent

        if "tensorflow" in q:
            return "tensorflow", self.tensorflow_agent

        if self.is_debug_query(q):
            return "debug", self.debug_agent

        if self.is_test_case_query(q):
            return "test_case", self.test_case_agent

        if self.is_explicit_coding_query(q):
            return "coding", self.coding_agent

        if self.is_algorithm_query(q):
            return "algorithm", self.algorithm_agent

        if self.is_ai_architect_query(q):
            return "ai_architect", self.ai_architect_agent

        if self.is_system_design_query(q):
            return "system_design", self.system_design_agent

        if self.is_mlops_query(q):
            return "mlops", self.mlops_agent

        if self.is_ml_query(q):
            return "ml", self.ml_agent

        if self.is_data_science_query(q):
            return "data_science", self.data_science_agent

        if self.is_tensorflow_query(q):
            return "tensorflow", self.tensorflow_agent

        if self.is_rag_query(q):
            return "rag", self.rag_agent

        if self.has_positive_deployment_intent(q):
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

        if any(k in q for k in ["payment", "pay", "card", "checkout", "wallet"]):
            return "payment", self.payment_agent
        if any(k in q for k in ["cab", "taxi", "uber", "lyft", "ride"]):
            return "cab", self.cab_agent
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
        if any(k in q for k in ["event", "concert", "game", "festival", "conference"]):
            return "event", self.event_agent
        if any(k in q for k in ["vacation", "package", "trip package", "holiday", "plan a 5-day vacation"]):
            return "vacation_package", self.vacation_package_agent
        if any(k in q for k in ["travel", "trip", "itinerary", "tour", "destination"]):
            return "travel", self.travel_agent

        if any(k in q for k in ["tourist attractions", "top tourist", "top places", "attractions in", "places to visit"]):
            return "local_discovery", self.local_discovery_agent

        if self.is_web_query(q):
            return "web", self.web_agent

        if self.is_general_factual_question(q):
            if self._is_country_query(q):
                return "country", self.country_agent
            return "general", self.general_agent

        # Use new CodingAIRouter for coding/AI routing
        coding_route = self.coding_ai_router.route(q)
        if coding_route == "deployment":
            if self.has_positive_deployment_intent(q):
                return "deployment", self.deployment_agent
        elif coding_route == "code_review":
            return "code_review", self.code_review_agent
        elif coding_route == "software_engineering":
            return "coding", self.coding_agent
        elif coding_route == "ai_architect":
            return "ai_architect", self.ai_architect_agent
        elif coding_route == "coding":
            if self.is_explicit_coding_query(q):
                return "coding", self.coding_agent

        if self.is_explicit_coding_query(q):
            return "coding", self.coding_agent

        # Other domain routing
        if any(k in q for k in [
            "health", "hospital", "doctor", "symptom", "pain", "diabetes",
            "chest pain", "medical", "fever", "breathing", "blood pressure",
        ]):
            return "healthcare", self.healthcare_agent

        if self.is_research_query(q):
            return "research", self.research_agent

        if self.is_finance_query(q):
            return "finance", self.finance_agent

        if any(k in q for k in ["workout", "fitness", "muscle gain", "exercise plan", "gym plan"]):
            return "fitness", self.fitness_agent

        if any(k in q for k in ["recipe", "meal", "meals", "high-protein", "high protein", "vegetarian"]):
            return "recipe", self.recipe_agent

        if any(k in q for k in ["tourist attractions", "top tourist", "top places", "attractions in", "places to visit"]):
            return "local_discovery", self.local_discovery_agent

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

        # Booking and travel routes
        if any(k in q for k in ["payment", "pay", "card", "checkout", "wallet"]):
            return "payment", self.payment_agent
        if any(k in q for k in ["cab", "taxi", "uber", "lyft", "ride"]):
            return "cab", self.cab_agent
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
        if any(k in q for k in ["event", "concert", "game", "festival", "conference"]):
            return "event", self.event_agent
        if any(k in q for k in ["vacation", "package", "trip package", "holiday", "plan a 5-day vacation"]):
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

        if self.is_web_query(q):
            return "web", self.web_agent

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

    def is_app_code_query(self, q: str) -> bool:
        """Return True for framework/database application code generation requests."""
        build_terms = ["build", "create", "generate", "scaffold", "implement"]
        app_terms = ["fastapi", "crud", "mysql", "sqlalchemy"]
        return has_any_word(q, build_terms) and has_any_phrase(q, app_terms)

    def has_positive_deployment_intent(self, q: str) -> bool:
        """Return True when deployment/containerization is explicitly requested."""
        if re.search(r"\b(do not|don't|without)\b[^.]*\b(docker|dockerfile|deploy|deployment|kubernetes|ci/cd)\b", q):
            return False
        return any(kw in q for kw in [
            "deploy", "deployment", "dockerize", "containerize",
            "docker compose", "docker-compose", "kubernetes", "k8s", "ci/cd",
        ])

    def is_research_query(self, q: str) -> bool:
        phrases = [
            "research", "paper", "literature review", "research gap",
            "gap analysis", "research roadmap", "possible experiments",
            "evaluation metrics", "attention is all you need",
            "gpt-4 technical report", "latest ai news", "open-source ai",
            "open source ai", "multimodal ai", "compare gpt", "compare models",
            "claude", "gemini", "deepseek", "qwen", "benchmark",
            "can ai invent", "invent new algorithms", "self-improving agentic rag",
        ]
        return any(phrase in q for phrase in phrases)

    def is_finance_query(self, q: str) -> bool:
        phrases = [
            "monthly expenses", "expense", "expenses", "budget", "income",
            "earn $", "spend $", "save $", "savings", "loan", "student loan",
            "federal tax", "tax", "etf", "s&p 500", "nasdaq", "stock",
            "analyze aapl", "crypto", "bitcoin", "ethereum", "investment",
            "financial report",
        ]
        return any(phrase in q for phrase in phrases)

    def is_sports_query(self, q: str) -> bool:
        return any(re.search(rf"\b{re.escape(keyword)}\b", q) for keyword in SPORTS_KEYWORDS)

    def is_general_agent_query(self, q: str) -> bool:
        if self.is_sports_query(q):
            return False
        if (
            has_any_word(q, ["buy", "purchase", "recommend", "price", "deal", "discount", "best"])
            or re.search(r"\bunder\s+\$?\d+", q)
        ) and has_any_word(
            q,
            [
                "phone", "laptop", "headphones", "monitor", "keyboard", "mouse",
                "tablet", "camera", "gpu", "iphone", "samsung", "apple", "pixel",
            ],
        ):
            return False
        if q.startswith("compare") and has_any_word(
            q,
            ["phone", "laptop", "iphone", "samsung", "apple", "pixel", "gpu", "camera"],
        ):
            return False
        if has_any_word(q, ["symptom", "pain", "diabetes", "fever", "medical", "doctor", "hospital"]):
            return False
        if has_any_word(q, ["deploy", "deployment", "dockerize", "containerize"]):
            return False
        if has_any_phrase(q, GENERAL_AGENT_STARTERS):
            return True
        return has_any_phrase(q, GENERAL_AGENT_TOPICS) and has_any_word(
            q,
            [
                "what", "explain", "how", "why", "compare", "summarize",
                "teach", "find", "latest", "recent", "history", "evolution",
            ],
        )

    def is_learning_query(self, q: str) -> bool:
        return any(re.search(rf"\b{re.escape(keyword)}\b", q) for keyword in LEARNING_KEYWORDS)

    def is_quiz_query(self, query: str) -> bool:
        q = query.lower()
        if any(keyword in q for keyword in QUIZ_KEYWORDS):
            return True
        option_count = len(re.findall(r"(?im)^\s*[a-d]\)\s+\S+", query))
        return option_count >= 2

    def is_web_query(self, q: str) -> bool:
        phrases = [
            "latest", "current", "today", "now", "recent", "breaking",
            "news", "live", "web search", "search web", "search online",
            "look up", "lookup", "find online", "google",
        ]
        return any(phrase in q for phrase in phrases)

    def is_strong_coding_query(self, q: str) -> bool:
        return any(re.search(pattern, q, re.I) for pattern in STRONG_CODING_PATTERNS)

    def is_explicit_coding_query(self, q: str) -> bool:
        if self.is_general_factual_question(q):
            return False
        if any(k in q for k in [
            "book", "booking", "hotel", "room", "flight", "ticket",
            "travel", "trip", "restaurant", "reservation", "cab", "taxi",
            "train", "bus", "movie", "event",
        ]):
            return False
        if self.is_strong_coding_query(q) or self.is_app_code_query(q):
            return True
        coding_actions = [
            "write", "generate", "create", "implement", "build",
            "code", "program", "script", "function", "class",
        ]
        coding_targets = [
            "c++", "cpp", "python", "java", "javascript", "typescript",
            "algorithm", "api", "app", "project", "crawler", "scraper",
            "function", "class", "database", "sql", "backend", "frontend",
        ]
        return has_any_word(q, coding_actions) and has_any_phrase(q, coding_targets)

    def is_general_factual_question(self, q: str) -> bool:
        """Return True for fact-seeking questions that may mention coding terms."""
        factual_starts = (
            "who invented", "who discovered", "who created", "who won",
            "who defeated", "who founded", "who is", "what is", "when was",
            "when did", "where is", "why is", "why did", "why was",
            "why were", "how does", "how long",
        )
        if q.startswith(factual_starts):
            coding_actions = (
                "write", "generate", "create code", "implement", "build",
                "debug", "fix", "compile", "run", "solve", "leetcode",
                "deploy", "deployment", "docker", "kubernetes", "api",
                "fastapi", "crud",
            )
            if has_any_phrase(q, ["laptop", "phone", "iphone", "samsung", "under $"]):
                return False
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

    def is_code_review_query(self, q: str) -> bool:
        """Return True if the query is about code review."""
        keywords = [
            "review", "code review", "optimize", "optimization",
            "security check", "code quality", "tle", "time limit exceeded",
            "bottleneck",
        ]
        return any(kw in q for kw in keywords)

    def is_debug_query(self, q: str) -> bool:
        """Return True if the query is about debugging."""
        keywords = ["debug", "fix", "error", "bug", "segmentation fault", "memory limit", "runtime error"]
        return any(kw in q for kw in keywords)

    def is_test_case_query(self, q: str) -> bool:
        """Return True if the query is about test cases."""
        keywords = ["test case", "edge case", "stress test", "generate test", "test cases"]
        return any(kw in q for kw in keywords)

    def is_algorithm_query(self, q: str) -> bool:
        """Return True if the query is about algorithm selection."""
        keywords = ["algorithm", "best algorithm", "solve range query", "pattern detection", "algorithm ranking"]
        return any(kw in q for kw in keywords)

    def is_system_design_query(self, q: str) -> bool:
        """Return True if the query is about system design."""
        keywords = ["design", "architecture", "youtube", "whatsapp", "system", "scalable"]
        return any(kw in q for kw in keywords)

    def is_ml_query(self, q: str) -> bool:
        """Return True if the query is about machine learning."""
        if re.search(r"^\s*(what is|what's|define|meaning of)\s+(machine learning|ml)\b", q):
            return False
        keywords = ["train", "model", "prediction", "classification", "regression", "machine learning", "ml"]
        return any(kw in q for kw in keywords)

    def is_data_science_query(self, q: str) -> bool:
        """Return True if the query is about data science."""
        keywords = ["data science", "eda", "analysis", "churn", "dataset", "visualization"]
        return any(kw in q for kw in keywords)

    def is_rag_query(self, q: str) -> bool:
        """Return True if the query is about RAG systems."""
        keywords = ["rag", "retrieval", "vector database", "embedding", "document retrieval"]
        return any(kw in q for kw in keywords)

    def is_mlops_query(self, q: str) -> bool:
        """Return True if the query is about MLOps."""
        keywords = ["mlops", "ml pipeline", "model deployment", "model registry", "monitoring"]
        return any(kw in q for kw in keywords)

    def is_ai_architect_query(self, q: str) -> bool:
        """Return True if the query is about AI architecture."""
        keywords = ["ai architect", "agentic system", "agentic rag", "agent architecture", "multi-agent", "autonomous"]
        return any(kw in q for kw in keywords)

    def is_self_correction_query(self, q: str) -> bool:
        """Return True if the query is about self-correction."""
        keywords = ["self-correct", "improve", "retry", "fix code", "correct"]
        return any(kw in q for kw in keywords)

    def is_loan_query(self, q: str) -> bool:
        """Return True if the query is about loans."""
        keywords = ["loan", "student loan", "pay off loan", "loan payoff", "debt payoff", "pay off debt", "loan balance", "interest rate", "monthly payment"]
        return any(kw in q for kw in keywords)

    def is_tensorflow_query(self, q: str) -> bool:
        """Return True if the query is about TensorFlow/deep learning predictions."""
        keywords = [
            "predict", "classify", "detect", "forecast", "inference",
            "tensorflow", "deep learning", "neural network", "cnn", "rnn", "lstm",
            "image classification", "object detection", "sentiment analysis",
            "time series", "churn prediction", "ml model", "model prediction"
        ]
        return any(kw in q for kw in keywords)

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
        # Check if there's an active conversation for this session
        active_conv = self.active_conversations.get(session_id)
        
        if active_conv:
            agent_name = active_conv["agent_name"]
            requested_route, requested_agent = self.route(original_query or query)
            interruptible_routes = {
                "coding", "deployment", "healthcare", "research", "resume",
                "shopping", "finance", "fitness", "recipe", "local_discovery",
                "travel", "flight", "hotel", "movie", "restaurant", "train",
                "bus", "cab", "event", "vacation_package", "payment", "coupon",
                "review", "cancellation", "notification", "support", "country",
                "web", "code_review", "debug", "test_case", "algorithm", "system_design",
                "ml", "data_science", "rag", "mlops", "ai_architect",
                "self_correction", "loan", "sports", "learning", "quiz",
            }
            is_new_domain = (
                requested_route in interruptible_routes
                and requested_agent.name != agent_name
            )

            if is_new_domain:
                del self.active_conversations[session_id]
                active_conv = None
            else:
                # Continue the active conversation
                conversation_state = active_conv["state"]
                agent = self.get_agent_by_name(agent_name)
                
                try:
                    result = agent.run(query, session_id=session_id, conversation_state=conversation_state)
                except TypeError:
                    result = agent.run(query, conversation_state=conversation_state)
                
                active_route = agent.agent_type.lower() if hasattr(agent, "agent_type") else agent_name.lower()
                result["router"] = {
                    "root": "User",
                    "router_agent": "AgentRouter",
                    "selected_leaf_agent": agent.name,
                    "route": active_route,
                }

                # Update or clear conversation state based on response
                if "conversation_state" in result:
                    if result["conversation_state"].get("complete"):
                        # Conversation complete, remove from active conversations
                        del self.active_conversations[session_id]
                    else:
                        # Update conversation state
                        self.active_conversations[session_id]["state"] = result["conversation_state"]
        if not active_conv:
            # Start a new conversation
            route_name, agent = self.route(original_query or query)
            run_query = original_query or query
            try:
                result = agent.run(run_query, session_id=session_id)
            except TypeError:
                result = agent.run(run_query)
            
            # Check if this agent started a conversation
            if "conversation_state" in result and not result["conversation_state"].get("complete"):
                self.active_conversations[session_id] = {
                    "agent_name": agent.name,
                    "state": result["conversation_state"]
                }
            
            result["router"] = {
                "root": "User",
                "router_agent": "AgentRouter",
                "selected_leaf_agent": agent.name,
                "route": route_name
            }
        
        # Add router info if not already present
        if "router" not in result:
            route_name, agent = self.route(original_query or query)
            result["router"] = {
                "root": "User",
                "router_agent": "AgentRouter",
                "selected_leaf_agent": agent.name,
                "route": route_name
            }
        
        return self.safety_layer.enforce(result, query=query, route=result["router"]["route"])
