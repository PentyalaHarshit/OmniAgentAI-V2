from tools.booking_parser import BookingParser
from tools.tot_planner import ToTPlanner
from tools.slot_filling import SlotFillingTool
from tools.conversation_state import ConversationState
from crews.generic_rag_crew import GenericRAGCrew


class BaseAgent:
    name = "BaseAgent"
    agent_type = "General"
    rag_category = "booking"
    required_fields = []
    optional_fields = []
    base_tasks = ["Understand query", "Generate N thoughts", "Retrieve RAG", "Use crew", "Verify", "Answer"]

    def __init__(self):
        self.parser = BookingParser()
        self.tot = ToTPlanner()
        self.crew = GenericRAGCrew()
        self.slot_filling = SlotFillingTool()
        self.conversation_state = ConversationState()

    def response(self, query, thoughts, answer, extra=None):
        return {
            "agent": self.name,
            "query": query,
            "thought_count": len(thoughts),
            "thoughts": thoughts,
            "answer": answer,
            "extra": extra or {}
        }

    def merge_fields(self, extracted: dict, prefilled_fields: dict | None):
        if not prefilled_fields:
            return extracted
        merged = extracted.copy()
        for k, v in prefilled_fields.items():
            if v != "not provided":
                merged[k] = v
        return merged

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        thoughts = self.tot.create_thoughts(self.agent_type, query, self.base_tasks)
        extracted = self.parser.extract(query, self.required_fields)
        extracted = self.merge_fields(extracted, prefilled_fields)

        missing = self.slot_filling.missing_fields(extracted, self.optional_fields)

        # Ask one question at a time, like ChatGPT/assistant flow.
        if missing:
            question = self.slot_filling.next_question(self.agent_type, missing)
            self.conversation_state.start_or_update(session_id, self.name, extracted, missing)

            answer = (
                f"{self.name} selected.\n\n"
                f"I need one more detail before continuing.\n\n"
                f"{question}"
            )
            return self.response(query, thoughts + [f"Slot Filling Agent: ask for {missing[0]}"], answer, {
                "slot_filling": True,
                "missing_fields": missing,
                "fields": extracted,
                "next_question": question
            })

        # All required fields collected, clear state and execute crew.
        self.conversation_state.clear(session_id)

        crew_result = self.crew.run(query, self.agent_type, extracted, self.rag_category)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_answer(extracted, crew_result)
        return self.response(query, thoughts + crew_thoughts, answer, {
            "slot_filling": False,
            "extracted": extracted,
            "crew_result": crew_result
        })

    def build_answer(self, extracted, crew_result):
        lines = [f"{self.name} selected.", "", "Collected Fields:"]
        for k, v in extracted.items():
            lines.append(f"- {k}: {v}")

        lines += [
            "",
            "RAG Retrieval:",
            f"- Category: {crew_result['rag']['category']}",
            f"- Sources: {crew_result['rag']['sources']}",
            "",
            "CrewAI-style Result:",
            f"- Crew: {crew_result['crew_name']}",
            f"- Availability: {crew_result['availability']['available']}",
            f"- Estimated price: {crew_result['pricing']['estimated_total']}",
            f"- Best option: {crew_result['recommendation']['best_option']}",
            f"- Safety: {crew_result['self_check']['warning']}",
            "",
            "Next step: connect real APIs and ask user confirmation before booking/payment.",
        ]
        return "\n".join(lines)
