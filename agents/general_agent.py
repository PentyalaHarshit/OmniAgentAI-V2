import logging
from agents.base_agent import BaseAgent
from tools.chat_memory import ChatMemory
from tools.mcp_web_tools import MCPToolRunner
from tools.general_query_tools import BuiltInFacts, clean_original_query, validate_query, normalize_query, classify_question
from tools.answer_extractor import AnswerExtractor
from tools.web_rag_tool import WebRAGTool
from tools.calculator_tool import CalculatorTool
from crews.react_general_crew import ReActGeneralCrew

logger = logging.getLogger(__name__)

GUIDANCE_MARKERS = [
    "route to", "use rag", "use healthcare rag", "use coding rag",
    "use booking", "use shopping rag", "use payment policy rag",
    "use uploaded", "leaf agent", "hallucination",
]


def is_routing_guidance(text: str) -> bool:
    t = text.lower()
    return any(marker in t for marker in GUIDANCE_MARKERS)


class GeneralAgent(BaseAgent):
    name = "GeneralAgent"
    agent_type = "General"
    rag_category = "general"
    required_fields = []
    optional_fields = []
    base_tasks = [
        "Query Validator",
        "Memory Agent",
        "Query Normalizer",
        "ReActGeneralCrew",
        "WebRAG Similarity Fallback",
        "Answer Extraction",
        "Final Answer",
    ]

    def __init__(self):
        super().__init__()
        self.mcp = MCPToolRunner()
        self.memory = ChatMemory()
        self.react_crew = ReActGeneralCrew(self.mcp)
        self.web_rag = WebRAGTool()
        self.extractor = AnswerExtractor()
        self.facts = BuiltInFacts()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        thoughts = self.tot.create_thoughts(self.agent_type, query, self.base_tasks)
        original_query = clean_original_query(query)
        normalized_query = normalize_query(original_query)

        thoughts.append(f"Thought: Original query = {original_query}")
        thoughts.append(f"Thought: Normalized query = {normalized_query}")

        valid, validation_message = validate_query(normalized_query)
        if not valid:
            return self.response(original_query, thoughts, validation_message, {"source_stage": "query_validation", "slot_filling": False})

        history = self.memory.get(session_id)
        if self.is_followup(normalized_query) and history:
            last_entity = self.find_last_entity(history)
            if last_entity:
                normalized_query = f"{normalized_query} of {last_entity}"
                thoughts.append(f"Memory Agent: follow-up resolved to '{normalized_query}'")

        question_type = classify_question(normalized_query)
        thoughts.append(f"Thought: Question type = {question_type}")

        thoughts.append("Action: Run ReActGeneralCrew.")
        crew = self.react_crew.run(normalized_query)

        for step in crew.get("crew_steps", []):
            thoughts.append(f"[{step['agent']}] {step['thought']}")

        answer = crew.get("answer", "")
        source_stage = f"react:{crew.get('tool_used', '')}"
        all_results = crew.get("all_results", [])

        if not answer:
            thoughts.append("Action: ReAct returned no answer. Run WebRAG similarity search.")
            try:
                docs = self.web_rag.search(normalized_query, top_k=5)
                for i, doc in enumerate(docs, start=1):
                    thoughts.append(f"Observation: WebRAG Rank {i}: {doc.get('title')} | score={doc.get('similarity_score')}")
                if docs:
                    context = self.web_rag.build_context(docs)
                    answer = self.extractor.extract(normalized_query, context)
                    if answer:
                        source_stage = "web_rag_similarity"
                        all_results = [{"tool": "web_rag", "result": d} for d in docs]
            except Exception as e:
                logger.warning("WebRAG failed: %s", e)
                thoughts.append(f"Observation: WebRAG failed: {e}")

        if not answer:
            answer = self.facts.lookup(normalized_query)
            if answer:
                source_stage = "built_in_facts"

        llm_guidance = ""
        if "[Free LLM Tree Guidance]" in query:
            llm_guidance = query.split("[Free LLM Tree Guidance]", 1)[1].strip()
            if "[Uploaded File Context]" in llm_guidance:
                llm_guidance = llm_guidance.split("[Uploaded File Context]", 1)[0].strip()

        if not answer and llm_guidance and not is_routing_guidance(llm_guidance):
            answer = llm_guidance
            source_stage = "llm_tree"

        if not answer:
            answer = f"I could not find a verified answer for: **{original_query}**. Try rephrasing or enable web/Ollama services."
            source_stage = "offline_fallback"

        return self.response(original_query, thoughts, answer, {"slot_filling": False, "source_stage": source_stage, "mcp_tools": all_results})

    def is_followup(self, query: str) -> bool:
        q = query.lower()
        return q.startswith(("and ", "also ", "what about ")) or q in ["population", "gdp", "capital"] or q.startswith(("what is its", "what is their"))

    def find_last_entity(self, history: list[dict]) -> str:
        text = " ".join(m.get("content", "") for m in history[-6:])
        low = text.lower()
        known = ["france", "paris", "italy", "spain", "japan", "china", "india", "germany", "united states", "canada", "australia", "brazil"]
        for entity in known:
            if entity in low:
                return entity
        return ""
