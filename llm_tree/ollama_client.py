import requests
from config import OLLAMA_BASE_URL, USE_OLLAMA, LLM_TREE_MODEL_TIMEOUT


class OllamaClient:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, query: str) -> str:
        prompt = self.build_prompt(query)

        if not USE_OLLAMA:
            return self.mock_response(query)

        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": self.model_name, "prompt": prompt, "stream": False},
                timeout=LLM_TREE_MODEL_TIMEOUT
            )
            if response.status_code == 200:
                text = response.json().get("response", "").strip()
                if text:
                    return text
        except Exception:
            pass  # Silently fall through to mock response

        return self.mock_response(query)


    def build_prompt(self, query: str) -> str:
        return f'''
You are one local free model node in an LLM tree.

User query:
{query}

Return concise guidance:
1. Best leaf agent.
2. Required fields.
3. RAG knowledge category needed.
4. Tool/API needed.
5. Hallucination/safety risk.
6. Verification needed.

Never claim diagnosis, purchase, payment, booking, cancellation, or deployment is complete.
'''

    def mock_response(self, query: str) -> str:
        q = query.lower()

        if any(k in q for k in ["health", "hospital", "doctor", "symptom", "chest pain", "diabetes", "fever", "breathing"]):
            return "Route to Healthcare Agent. Use healthcare RAG, symptom analysis, risk score, specialty selection, doctor lookup demo, and safety self-check. Do not diagnose."

        if any(k in q for k in ["code", "c++", "python", "algorithm", "dijkstra", "leetcode", "codeforces"]):
            return "Route to Coding Agent. Use coding RAG, ToT algorithm selection, generation, compiler, tests, self-correction, and reviewer."

        if any(k in q for k in ["shop", "buy", "product", "laptop", "phone", "cart", "order"]):
            return "Route to Shopping Agent. Use shopping RAG, compare products, prepare cart only, require confirmation before purchase."

        if any(k in q for k in ["payment", "pay", "card", "checkout"]):
            return "Route to Payment Agent. Use payment policy RAG. Prepare payment intent only; do not charge."

        if any(k in q for k in ["resume", "cv", "ats", "job description"]):
            return "Route to Resume Agent. Use uploaded resume/JD and resume RAG, parse skills, rewrite truthful bullets."

        if any(k in q for k in ["research", "paper", "literature", "survey", "research gap"]):
            return "Route to Research Agent. Use uploaded file/RAG, break topic into subquestions, identify gaps, summarize."

        if any(k in q for k in ["hotel", "flight", "movie", "restaurant", "cab", "train", "bus", "event", "travel", "trip"]):
            return "Route to Booking/Travel Agent. Use booking RAG, extract fields, check demo availability, ask confirmation."

        return "Route to General Agent. Use RAG when retrieval is needed and answer safely."
