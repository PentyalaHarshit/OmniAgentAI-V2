import requests

from config import (
    VLLM_API_KEY,
    VLLM_TEMPERATURE,
    VLLM_MAX_TOKENS,
    LLM_TREE_MODEL_TIMEOUT,
)


class VLLMClient:
    """
    vLLM OpenAI-compatible client.

    Start a vLLM server like:

    python -m vllm.entrypoints.openai.api_server \
        --model Qwen/Qwen2.5-Coder-7B-Instruct \
        --host 0.0.0.0 \
        --port 8001

    Then this client calls:
    http://localhost:8001/v1/chat/completions
    """

    def __init__(self, model_name: str, base_url: str, display_name: str):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.display_name = display_name

    def generate(self, query: str) -> str:
        prompt = self.build_prompt(query)

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {VLLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are one model node inside OmniAgentAI's vLLM tree. "
                                "Return concise routing and safety guidance."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": VLLM_TEMPERATURE,
                    "max_tokens": VLLM_MAX_TOKENS,
                },
                timeout=LLM_TREE_MODEL_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

            return f"vLLM {self.display_name} error {response.status_code}: {response.text}\n{self.mock_response(query)}"

        except Exception as e:
            return f"vLLM {self.display_name} unavailable. Fallback used. Error: {e}\n{self.mock_response(query)}"

    def build_prompt(self, query: str) -> str:
        return f"""
User query:
{query}

Return:
1. Best leaf agent.
2. Required fields.
3. RAG category.
4. Tool/API needed.
5. Safety/hallucination risk.
6. Verification needed.

Never claim diagnosis, purchase, payment, booking, cancellation, or deployment is complete.
"""

    def mock_response(self, query: str) -> str:
        q = query.lower()

        if any(k in q for k in ["health", "hospital", "doctor", "symptom", "chest pain", "diabetes", "fever", "breathing"]):
            return "Route to Healthcare Agent. Use healthcare RAG, risk scoring, XAI explanation, doctor lookup demo, and medical safety self-check. Do not diagnose."

        if any(k in q for k in ["code", "c++", "python", "algorithm", "dijkstra", "leetcode"]):
            return "Route to Coding Agent. Use coding RAG, ToT algorithm selection, generation, compiler, tests, self-correction, and reviewer."

        if any(k in q for k in ["shop", "buy", "product", "laptop", "phone", "cart", "order"]):
            return "Route to Shopping Agent. Use shopping RAG, compare products, prepare cart only, require user confirmation before purchase."

        if any(k in q for k in ["payment", "pay", "card", "checkout"]):
            return "Route to Payment Agent. Prepare payment intent only; do not charge."

        if any(k in q for k in ["resume", "cv", "ats", "job description"]):
            return "Route to Resume Agent. Use uploaded resume/JD and resume RAG, parse skills, rewrite truthful bullets."

        if any(k in q for k in ["research", "paper", "literature", "survey", "research gap"]):
            return "Route to Research Agent. Use uploaded file/RAG, break topic into subquestions, identify gaps, summarize."

        if any(k in q for k in ["hotel", "flight", "movie", "restaurant", "cab", "train", "bus", "event", "travel", "trip"]):
            return "Route to Booking/Travel Agent. Use booking RAG, extract fields, check demo availability, ask confirmation."

        return "Route to General Agent. Use RAG if retrieval is needed and answer safely."
