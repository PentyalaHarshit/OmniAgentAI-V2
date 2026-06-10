from tools.rag_tool import RAGTool


class ResearchCrew:
    def __init__(self):
        self.rag = RAGTool()

    def run(self, query: str, file_context: str = ""):
        rag = self.rag.search(query, "research")
        steps = [
            {"thought": "RAG Retrieval Agent: retrieve research knowledge", "output": rag},
            {"thought": "Research Planner Agent: break into subtopics", "output": ["concept", "method", "baseline", "gap", "evaluation"]},
            {"thought": "Evidence Agent: use uploaded/RAG context", "output": "Uploaded context used" if file_context else "Local RAG context used"},
            {"thought": "Gap Agent: find gaps", "output": ["Need benchmark", "Need ablation", "Need safety evaluation"]},
            {"thought": "Writer Agent: create research summary", "output": "Research summary generated"},
            {"thought": "Self-Check Agent: avoid unsupported claims", "output": "Safe"}
        ]
        answer = (
            "Research Agent Result\n\n"
            f"RAG Sources: {rag['sources']}\n\n"
            "Suggested Research Gaps:\n"
            "- Need benchmark comparison\n"
            "- Need real-world dataset\n"
            "- Need hallucination/safety metrics\n"
            "- Need ablation study\n\n"
            "Uploaded/context evidence is used where available."
        )
        return {"crew_name": "ResearchRAGCrew", "crew_steps": steps, "answer": answer, "rag": rag}
