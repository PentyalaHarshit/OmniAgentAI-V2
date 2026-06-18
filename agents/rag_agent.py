from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.rag_crew import RAGCrew


class RAGAgent(BaseAgent):
    name = "RAGAgent"
    agent_type = "RAG"
    rag_category = "coding"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = RAGCrew()

    def run(self, query: str):
        tasks = [
            "Detect RAG system type",
            "Identify document type",
            "Estimate system scale",
            "Design chunking strategy",
            "Select embedding model",
            "Choose vector database",
            "Design retriever",
            "Add reranking layer",
            "Plan LLM integration",
            "Provide comprehensive RAG architecture"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        crew_result = self.crew.run(query)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_rag_answer(crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {"crew_result": crew_result})

    def build_rag_answer(self, crew_result: dict):
        chunking = crew_result.get("chunking_strategy", {})
        embedding = crew_result.get("embedding_model", {})
        vector_db = crew_result.get("vector_database", {})
        retriever = crew_result.get("retriever", {})
        reranker = crew_result.get("reranker", {})
        llm = crew_result.get("llm_integration", {})
        scale = crew_result.get("scale", {})
        
        return (
            "RAG Agent selected.\n\n"
            f"RAG Type: {crew_result.get('rag_type', 'Unknown')}\n"
            f"Document Type: {crew_result.get('document_type', 'Unknown')}\n\n"
            "Scale Estimation:\n"
            f"- Documents: {scale.get('documents', 'Unknown')}\n"
            f"- Queries/Second: {scale.get('queries_per_second', 'Unknown')}\n"
            f"- Storage: {scale.get('storage', 'Unknown')}\n\n"
            "Chunking Strategy:\n"
            f"- Method: {chunking.get('method', 'Unknown')}\n"
            f"- Chunk Size: {chunking.get('chunk_size', 'Unknown')}\n"
            f"- Overlap: {chunking.get('overlap', 'Unknown')}\n"
            f"- Technique: {chunking.get('technique', 'Unknown')}\n\n"
            "Embedding Model:\n"
            f"- Model: {embedding.get('model', 'Unknown')}\n"
            f"- Dimensions: {embedding.get('dimensions', 'Unknown')}\n"
            f"- Reason: {embedding.get('reason', 'Unknown')}\n\n"
            "Vector Database:\n"
            f"- Database: {vector_db.get('database', 'Unknown')}\n"
            f"- Reason: {vector_db.get('reason', 'Unknown')}\n"
            f"- Features: {', '.join(vector_db.get('features', []))}\n\n"
            "Retriever:\n"
            f"- Search Type: {retriever.get('search_type', 'Unknown')}\n"
            f"- Top K: {retriever.get('top_k', 'Unknown')}\n"
            f"- Similarity Threshold: {retriever.get('similarity_threshold', 'Unknown')}\n\n"
            "Reranker:\n"
            f"- Enabled: {reranker.get('enabled', 'Unknown')}\n"
            f"- Model: {reranker.get('model', 'Not specified')}\n"
            f"- Reason: {reranker.get('reason', 'Unknown')}\n\n"
            "LLM Integration:\n"
            f"- Model: {llm.get('model', 'Unknown')}\n"
            f"- Context Window: {llm.get('context_window', 'Unknown')}\n"
            f"- Citation: {llm.get('citation', 'Unknown')}"
        )
