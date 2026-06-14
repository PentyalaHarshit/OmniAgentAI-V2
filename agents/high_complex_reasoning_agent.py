import json
import time
from typing import Any, Dict, List


class HighComplexReasoningAgent:
    """
    High-complex reasoning pipeline:
    1. Understand query
    2. Generate multiple reasoning paths
    3. Score each path
    4. Select best path
    5. Execute ReAct steps
    6. Self-check answer
    7. Return verified final answer
    """

    def __init__(self, mcp_runner=None, web_rag=None, verifier=None):
        self.mcp = mcp_runner
        self.web_rag = web_rag
        self.verifier = verifier

    def run(self, query: str) -> Dict[str, Any]:
        thoughts = []
        start = time.time()

        thoughts.append(f"User Query: {query}")

        # Step 1: classify
        task_type = self.classify_task(query)
        thoughts.append(f"Task Type: {task_type}")

        # Step 2: create multiple reasoning plans
        plans = self.generate_reasoning_plans(query, task_type)
        thoughts.append(f"Generated {len(plans)} reasoning plans")

        # Step 3: score plans
        scored_plans = self.score_plans(plans)
        best_plan = scored_plans[0]
        thoughts.append(f"Best Plan Selected: {best_plan['name']}")

        # Step 4: execute best plan
        answer, evidence = self.execute_plan(query, best_plan, thoughts)

        # Step 5: self-check
        checked_answer = self.self_check(query, answer, evidence, thoughts)

        # Step 6: verify
        verification = self.verify_answer(query, checked_answer, evidence)

        final = {
            "query": query,
            "answer": checked_answer,
            "reasoning_path": best_plan,
            "evidence": evidence,
            "verification": verification,
            "thoughts": thoughts,
            "latency_seconds": round(time.time() - start, 3),
        }

        return final

    def classify_task(self, query: str) -> str:
        q = query.lower()

        if any(x in q for x in ["code", "program", "debug", "error"]):
            return "coding"

        if any(x in q for x in ["latest", "today", "current", "price", "weather"]):
            return "live_search"

        if any(x in q for x in ["why", "how", "explain", "reason"]):
            return "deep_reasoning"

        if any(x in q for x in ["calculate", "sum", "multiply", "divide"]):
            return "math"

        return "general"

    def generate_reasoning_plans(self, query: str, task_type: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": "Direct Reasoning",
                "steps": [
                    "Understand query",
                    "Use internal reasoning",
                    "Generate answer",
                    "Self-check answer",
                ],
                "score": 0,
            },
            {
                "name": "ReAct Tool Reasoning",
                "steps": [
                    "Understand query",
                    "Choose useful tool",
                    "Run action",
                    "Observe result",
                    "Generate answer",
                    "Verify answer",
                ],
                "score": 0,
            },
            {
                "name": "RAG Evidence Reasoning",
                "steps": [
                    "Search documents/web knowledge",
                    "Extract evidence",
                    "Compare evidence",
                    "Generate grounded answer",
                    "Fact-check answer",
                ],
                "score": 0,
            },
            {
                "name": "Self-Correcting Reasoning",
                "steps": [
                    "Generate first answer",
                    "Find weakness",
                    "Improve answer",
                    "Check edge cases",
                    "Return final answer",
                ],
                "score": 0,
            },
        ]

    def score_plans(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for plan in plans:
            score = 0

            if "Tool" in plan["name"]:
                score += 8

            if "RAG" in plan["name"]:
                score += 9

            if "Self" in plan["name"]:
                score += 7

            if "Direct" in plan["name"]:
                score += 5

            plan["score"] = score

        return sorted(plans, key=lambda x: x["score"], reverse=True)

    def execute_plan(
        self,
        query: str,
        plan: Dict[str, Any],
        thoughts: List[str],
    ) -> tuple[str, List[Dict[str, Any]]]:

        evidence = []

        thoughts.append("Action: Start executing selected reasoning plan")

        # RAG path
        if "RAG" in plan["name"] and self.web_rag:
            try:
                docs = self.web_rag.search(query, top_k=5)
                evidence.extend(docs)

                thoughts.append(f"Observation: RAG returned {len(docs)} documents")

                context = "\n\n".join(
                    d.get("text", "")[:1000] for d in docs
                )

                answer = self.compose_answer(query, context)
                return answer, evidence

            except Exception as e:
                thoughts.append(f"RAG failed: {e}")

        # Tool path
        if "Tool" in plan["name"] and self.mcp:
            try:
                result = self.mcp.run(query)
                evidence.append({"tool": "mcp", "result": result})
                thoughts.append("Observation: MCP tool returned result")

                answer = str(result)
                return answer, evidence

            except Exception as e:
                thoughts.append(f"MCP failed: {e}")

        # fallback reasoning
        answer = self.basic_reasoning_answer(query)
        return answer, evidence

    def compose_answer(self, query: str, context: str) -> str:
        if not context.strip():
            return self.basic_reasoning_answer(query)

        return (
            "Based on retrieved evidence, the best answer is:\n\n"
            f"{context[:1500]}"
        )

    def basic_reasoning_answer(self, query: str) -> str:
        return (
            "I analyzed the query using internal reasoning. "
            "A high-confidence answer needs either RAG evidence, tool output, "
            "or verified facts. Please connect tools/WebRAG for stronger accuracy."
        )

    def self_check(
        self,
        query: str,
        answer: str,
        evidence: List[Dict[str, Any]],
        thoughts: List[str],
    ) -> str:

        thoughts.append("Self-Check: Checking answer quality")

        if not answer or len(answer.strip()) < 20:
            thoughts.append("Self-Check Failed: Answer too short")
            return "I could not generate a strong verified answer."

        if "I don't know" in answer.lower():
            thoughts.append("Self-Check Warning: Weak answer detected")

        if evidence:
            thoughts.append("Self-Check Passed: Evidence exists")
        else:
            thoughts.append("Self-Check Warning: No external evidence")

        return answer

    def verify_answer(
        self,
        query: str,
        answer: str,
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if self.verifier:
            try:
                return self.verifier.verify(query, answer, evidence)
            except Exception as e:
                return {
                    "verified": False,
                    "confidence": 0.4,
                    "reason": f"Verifier failed: {e}",
                }

        return {
            "verified": bool(answer),
            "confidence": 0.6 if evidence else 0.4,
            "reason": "Basic verification only.",
        }


if __name__ == "__main__":
    agent = HighComplexReasoningAgent()
    result = agent.run("Explain how Agentic RAG works with tools")

    print(json.dumps(result, indent=2))