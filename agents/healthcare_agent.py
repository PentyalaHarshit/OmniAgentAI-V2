from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from tools.booking_parser import BookingParser
from tools.slot_filling import SlotFillingTool
from tools.conversation_state import ConversationState
from crews.healthcare_crew import HealthcareCrew


class HealthcareAgent(BaseAgent):
    name = "HealthcareAgent"
    agent_type = "Healthcare"
    rag_category = "healthcare"
    required_fields = ["hospital", "symptoms", "age", "medical_history"]
    optional_fields = ["age", "medical_history"]

    def __init__(self):
        self.parser = BookingParser()
        self.tot = ToTPlanner()
        self.crew = HealthcareCrew()
        self.slot_filling = SlotFillingTool()
        self.conversation_state = ConversationState()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        tasks = [
            "Extract hospital and symptoms",
            "Ask missing hospital/symptom details",
            "Retrieve healthcare RAG knowledge",
            "Analyze risk using XAI rules",
            "Select specialty",
            "Find demo doctors",
            "Recommend appointment or urgent care",
            "Self-check medical safety"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=16)
        extracted = self.parser.extract(query, self.required_fields)

        # Symptom extraction: if query contains symptom words, store full query as symptoms.
        symptom_words = ["pain", "fever", "diabetes", "breathing", "headache", "blood pressure", "cough", "chest"]
        if any(w in query.lower() for w in symptom_words):
            extracted["symptoms"] = query

        extracted = self.merge_fields(extracted, prefilled_fields)

        missing = self.slot_filling.missing_fields(extracted, self.optional_fields)

        if missing:
            question = self.slot_filling.next_question(self.agent_type, missing)
            self.conversation_state.start_or_update(session_id, self.name, extracted, missing)
            answer = (
                "HealthcareAgent selected.\n\n"
                "I need one more detail before continuing.\n\n"
                f"{question}"
            )
            return self.response(query, thoughts + [f"Slot Filling Agent: ask for {missing[0]}"], answer, {
                "slot_filling": True,
                "missing_fields": missing,
                "fields": extracted,
                "next_question": question
            })

        self.conversation_state.clear(session_id)
        crew_result = self.crew.run(query, extracted)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        a = crew_result["analysis"]

        urgent = ""
        if a["risk_label"] == "High risk":
            urgent = "Important: high-risk symptoms detected. If symptoms are severe, seek emergency care immediately."

        answer = (
            "Healthcare Agent selected.\n\n"
            "This is not a medical diagnosis.\n\n"
            f"Hospital: {extracted.get('hospital', 'not provided')}\n"
            f"Symptoms: {extracted.get('symptoms', 'not provided')}\n"
            f"Specialty: {a['specialty']}\n"
            f"Priority: {a['priority']}\n"
            f"Risk: {a['risk_percentage']}% ({a['risk_label']})\n\n"
            "XAI Explanation:\n- " + "\n- ".join(a["xai_reasons"]) + "\n\n"
            f"RAG Sources: {crew_result['rag']['sources']}\n\n"
            "Available Demo Doctors:\n- " + "\n- ".join(crew_result["doctors"]) + "\n\n"
            f"{urgent}\n\n"
            "Safety: Contact a licensed medical professional for real care."
        )

        return self.response(query, thoughts + crew_thoughts, answer, {
            "slot_filling": False,
            "extracted": extracted,
            "crew_result": crew_result
        })
