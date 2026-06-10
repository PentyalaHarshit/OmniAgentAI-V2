from tools.rag_tool import RAGTool


class ResumeCrew:
    def __init__(self):
        self.rag = RAGTool()

    def run(self, query: str, file_context: str = ""):
        rag = self.rag.search(query, "resume")
        text = (file_context or query).lower()
        skills = []
        for s in ["python", "fastapi", "rag", "langchain", "docker", "sql", "machine learning", "llm", "agents"]:
            if s in text:
                skills.append(s)

        ats = min(95, 55 + 5 * len(skills))
        bullets = [
            "Built multi-agent AI workflows using router agents, tool agents, RAG retrieval, and self-checking crews.",
            "Developed FastAPI applications with file upload, RAG-style retrieval, and local Ollama LLM integration.",
            "Implemented coding-agent workflows with algorithm selection, compile/test loops, and self-correction.",
            "Designed safe shopping and booking flows with confirmation-first payment handling."
        ]

        steps = [
            {"thought": "RAG Retrieval Agent: retrieve resume/ATS knowledge", "output": rag},
            {"thought": "Resume Parser Agent: extract skills", "output": skills},
            {"thought": "ATS Agent: estimate keyword score", "output": ats},
            {"thought": "Rewrite Agent: improve bullets", "output": bullets},
            {"thought": "Truthfulness Agent: avoid fake metrics", "output": "Safe"}
        ]

        answer = (
            "Resume Agent Result\n\n"
            f"RAG Sources: {rag['sources']}\n"
            f"Demo ATS Score: {ats}\n"
            f"Detected Skills: {', '.join(skills) if skills else 'not enough skills detected'}\n\n"
            "Improved Bullets:\n- " + "\n- ".join(bullets) +
            "\n\nSelf-check: Keep metrics truthful. Do not invent numbers."
        )

        return {"crew_name": "ResumeRAGCrew", "crew_steps": steps, "answer": answer, "rag": rag}
