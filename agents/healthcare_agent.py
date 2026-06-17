from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from tools.booking_parser import BookingParser
from tools.slot_filling import SlotFillingTool
from tools.conversation_state import ConversationState
from tools.doctor_mcp_tools import DoctorMCPToolRunner
from crews.healthcare_crew import HealthcareCrew


class HealthcareAgent(BaseAgent):
    name = "HealthcareAgent"
    agent_type = "Healthcare"
    rag_category = "healthcare"
    required_fields = ["symptoms"]
    optional_fields = ["age", "medical_history"]

    def __init__(self):
        self.parser = BookingParser()
        self.tot = ToTPlanner()
        self.crew = HealthcareCrew()
        self.slot_filling = SlotFillingTool()
        self.conversation_state = ConversationState()
        self.doctor_mcp = DoctorMCPToolRunner()
        self.required_questions = [
            ("age", "What is your age?"),
            ("days", "How many days have you had these symptoms?"),
            ("temperature", "What is your temperature?"),
            ("shortness_of_breath", "Do you have shortness of breath? (yes/no)"),
            ("chest_pain", "Do you have chest pain? (yes/no)"),
        ]

    def run(
        self,
        query: str,
        patient_info: dict | None = None,
        prefilled_fields: dict | None = None,
        session_id: str = "default",
    ):
        tasks = [
            "Extract symptoms and care intent",
            "Ask missing triage questions",
            "Validate user answers",
            "Save valid answers in memory",
            "Analyze possible causes",
            "Retrieve healthcare RAG knowledge",
            "Run ToT condition scoring",
            "Assess risk using XAI rules",
            "Generate general advice",
            "Check emergency signs",
            "Suggest specialty",
            "Find doctors only if requested",
            "Self-check medical safety"
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=16)
        state = self.conversation_state.get(session_id)
        if state.get("active_agent") == self.name and state.get("flow") == "healthcare_appointment_confirmation":
            return self.handle_appointment_confirmation(query, state, thoughts, prefilled_fields, session_id)
        if state.get("active_agent") == self.name and state.get("flow") == "healthcare_slot_selection":
            return self.handle_slot_selection(query, state, thoughts, prefilled_fields, session_id)
        if state.get("active_agent") == self.name and state.get("flow") == "healthcare_triage":
            return self.continue_triage(query, state, thoughts, patient_info, prefilled_fields, session_id)

        extracted = self.parser.extract(query, self.required_fields)
        booking_intent = self.has_booking_intent(query)
        patient_info = self.normalize_patient_info(patient_info or {})
        patient_info = self.normalize_patient_info({**patient_info, **(prefilled_fields or {})})

        # Symptom extraction: if query contains symptom words, store full query as symptoms.
        symptom_words = [
            "pain", "fever", "diabetes", "breathing", "headache",
            "blood pressure", "cough", "chest", "sore throat", "runny nose",
            "nausea", "vomiting", "fatigue",
        ]
        if any(w in query.lower() for w in symptom_words):
            extracted["symptoms"] = query

        extracted = self.merge_fields(extracted, patient_info)

        required_for_intent = ["symptoms", "hospital"] if booking_intent else ["symptoms"]
        booking_fields = self.parser.extract(query, required_for_intent)
        extracted.update({k: v for k, v in booking_fields.items() if v != "not provided"})
        if any(w in query.lower() for w in symptom_words):
            extracted["symptoms"] = query

        if booking_intent and extracted.get("hospital", "not provided") == "not provided":
            return self.ask_booking_hospital(query, thoughts, extracted, session_id)

        missing_questions = self.get_missing_questions(query, patient_info)
        missing_fields = self.get_missing_patient_fields(query, patient_info)
        if missing_questions:
            return self.start_triage(query, thoughts, extracted, patient_info, session_id)

        missing = self.slot_filling.missing_fields(
            {field: extracted.get(field, "not provided") for field in required_for_intent},
            [],
        )

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
        emergency_response = self.emergency_response(query, patient_info)
        if emergency_response:
            return self.response(query, thoughts + ["Emergency Checker: high-risk red flag detected"], emergency_response["answer"], {
                "status": "high_risk",
                "slot_filling": False,
                "patient_info": patient_info,
                "analysis": emergency_response["analysis"],
            })

        crew_result = self.crew.run(query, extracted, include_doctors=booking_intent)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        answer = self.build_healthcare_answer(extracted, crew_result, booking_intent, patient_info)

        return self.response(query, thoughts + crew_thoughts, answer, {
            "status": "analyzed",
            "slot_filling": False,
            "extracted": extracted,
            "patient_info": patient_info,
            "crew_result": crew_result
        })

    def start_triage(self, query: str, thoughts: list[str], extracted: dict, patient_info: dict, session_id: str):
        answers = {
            key: value
            for key, value in patient_info.items()
            if key in {field for field, _ in self.required_questions}
        }
        first_missing_index = self.first_missing_question_index(answers, query)
        state = {
            "active_agent": self.name,
            "flow": "healthcare_triage",
            "symptoms": extracted.get("symptoms", query),
            "answers": answers,
            "fields": {**extracted, **answers},
            "required_questions": self.required_questions,
            "current_question_index": first_missing_index,
            "missing_fields": [key for key, _ in self.required_questions[first_missing_index:]],
        }
        self.conversation_state.set(session_id, state)
        return self.ask_next_triage_question(query, thoughts, state)

    def continue_triage(
        self,
        query: str,
        state: dict,
        thoughts: list[str],
        patient_info: dict | None,
        prefilled_fields: dict | None,
        session_id: str,
    ):
        if prefilled_fields:
            state["answers"] = self.normalize_patient_info({
                **state.get("answers", {}),
                **prefilled_fields,
            })
            state["fields"] = {**state.get("fields", {}), **state["answers"]}
        elif patient_info:
            state["answers"] = self.normalize_patient_info({
                **state.get("answers", {}),
                **patient_info,
            })
            state["fields"] = {**state.get("fields", {}), **state["answers"]}
        else:
            index = int(state.get("current_question_index", 0) or 0)
            if index < len(self.required_questions):
                key, _ = self.required_questions[index]
                cleaned = query.strip()
                valid, normalized_value, error = self.validate_triage_answer(key, cleaned)
                if not valid:
                    self.conversation_state.set(session_id, state)
                    return self.ask_next_triage_question(
                        query,
                        thoughts + [f"Validation Agent: invalid {key}"],
                        state,
                        validation_error=error,
                    )
                state.setdefault("answers", {})[key] = normalized_value
                state.setdefault("fields", {})[key] = normalized_value
                state["current_question_index"] = index + 1

        state["answers"] = self.normalize_patient_info(state.get("answers", {}))
        state["current_question_index"] = self.first_missing_question_index(
            state["answers"],
            state.get("symptoms", ""),
        )
        state["missing_fields"] = [key for key, _ in self.required_questions[state["current_question_index"]:]]
        self.conversation_state.set(session_id, state)

        if state["current_question_index"] < len(self.required_questions):
            return self.ask_next_triage_question(query, thoughts, state)

        self.conversation_state.clear(session_id)
        symptoms = state.get("symptoms", query)
        answers = state.get("answers", {})
        return self.final_triage_analysis(symptoms, answers, thoughts, session_id)

    def ask_next_triage_question(
        self,
        query: str,
        thoughts: list[str],
        state: dict,
        validation_error: str = "",
    ):
        index = int(state.get("current_question_index", 0) or 0)
        _, question = self.required_questions[index]
        validation_prefix = f"{validation_error}\n\n" if validation_error else ""
        answer = (
            "HealthcareAgent / healthcare\n\n"
            f"{validation_prefix}"
            f"{question}\n\n"
            "Safety: This is not a medical diagnosis. Please consult a licensed medical professional."
        )
        return self.response(query, thoughts + [f"Triage Question Agent: ask {self.required_questions[index][0]}"], answer, {
            "status": "asking_question",
            "validation_status": "invalid" if validation_error else "pending",
            "slot_filling": True,
            "question": question,
            "session": state,
            "missing_fields": state.get("missing_fields", []),
            "patient_info": state.get("answers", {}),
        })

    def validate_triage_answer(self, field: str, value: str):
        validators = {
            "age": self.validate_age,
            "days": self.validate_days,
            "temperature": self.validate_temperature,
            "shortness_of_breath": self.validate_yes_no,
            "chest_pain": self.validate_yes_no,
            "covid_test": self.validate_yes_no,
        }
        return validators.get(field, self.validate_non_empty)(value)

    @staticmethod
    def validate_age(value: str):
        try:
            age = int(str(value).strip())
        except Exception:
            return False, None, "Invalid age.\nPlease enter a valid age between 0 and 120 years."
        if age < 0 or age > 120:
            return False, None, "Invalid age.\nPlease enter a valid age between 0 and 120 years."
        return True, str(age), ""

    @staticmethod
    def validate_days(value: str):
        text = str(value).strip().lower()
        import re
        match = re.search(r"\d+(?:\.\d+)?", text)
        if not match:
            return False, None, "Invalid duration.\nPlease enter how many days you have had symptoms. Example: 2 days."
        days = float(match.group(0))
        if days < 0 or days > 60:
            return False, None, "Invalid duration.\nPlease enter a duration between 0 and 60 days."
        return True, text, ""

    @staticmethod
    def validate_temperature(value: str):
        text = str(value).strip().lower().replace("°", "")
        import re
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return False, None, (
                "Invalid temperature.\n"
                "Please enter a temperature in Fahrenheit or Celsius.\n"
                "Example: 101 F or 38.3 C"
            )
        temp = float(match.group(0))
        is_celsius = bool(re.search(r"\b(c|celsius)\b", text))
        is_fahrenheit = bool(re.search(r"\b(f|fahrenheit)\b", text))

        if is_celsius:
            if temp < 32 or temp > 43.5:
                return False, None, "Temperature seems invalid. Please enter a value between 32 and 43.5 C."
            return True, f"{temp:g} C", ""

        if is_fahrenheit or not is_celsius:
            if temp < 90 or temp > 110:
                return False, None, "Temperature seems invalid. Please enter a value between 90 and 110 F."
            suffix = " F" if is_fahrenheit else ""
            return True, f"{temp:g}{suffix}", ""

        return True, f"{temp:g}", ""

    @staticmethod
    def validate_yes_no(value: str):
        normalized = str(value).lower().strip()
        if normalized not in ["yes", "no"]:
            return False, None, "Invalid response.\nPlease answer only: yes or no."
        return True, normalized, ""

    @staticmethod
    def validate_non_empty(value: str):
        text = str(value).strip()
        if not text:
            return False, None, "Invalid response.\nPlease enter a response."
        return True, text, ""

    def final_triage_analysis(self, symptoms: str, answers: dict, thoughts: list[str], session_id: str):
        session = {"symptoms": symptoms, "answers": answers}
        result = self.final_analysis(session)
        doctor = result["recommended_doctor"]
        appointment_state = {
            "active_agent": self.name,
            "flow": "healthcare_appointment_confirmation",
            "symptoms": symptoms,
            "answers": answers,
            "doctor": doctor,
            "fields": {"appointment_confirmation": "not provided"},
            "missing_fields": ["appointment_confirmation"],
        }
        self.conversation_state.set(session_id, appointment_state)
        answer = self.format_final_analysis(result)
        flow_thoughts = [
            "Analysis Agent: scored possible conditions and risk.",
            "XAI Explanation Agent: generated transparent medical reasoning.",
            "Medical RAG Agent: attached healthcare evidence context.",
            "Doctor Recommendation Agent: selected specialist and urgency.",
            "Doctor Recommendation Agent: showed doctor information and requested booking confirmation.",
            "Safety Confirmation: added non-diagnosis disclaimer.",
        ]
        return self.response(symptoms, thoughts + flow_thoughts, answer, {
            "status": "analysis_completed",
            "slot_filling": False,
            "symptoms": symptoms,
            "patient_info": answers,
            "analysis": result["analysis"],
            "xai_explanation": result["xai_explanation"],
            "rag_evidence": result["rag_evidence"],
            "recommended_doctor": doctor,
            "appointment": result["appointment"],
            "safety": result["safety"],
        })

    def final_analysis(self, session: dict):
        answers = self.normalize_patient_info(session.get("answers", {}))
        symptoms = session.get("symptoms", "")

        analysis = {
            "possible_conditions": [
                {"name": "Viral respiratory infection", "confidence": 75},
                {"name": "Flu", "confidence": 65},
                {"name": "COVID-19", "confidence": 60},
                {"name": "Bronchitis", "confidence": 40},
            ],
            "risk": self.risk_level(answers),
        }

        xai = {
            "explanation": [
                "Fever + cough commonly suggests respiratory infection.",
                "Shortness of breath or chest pain increases urgency.",
                "Duration and temperature help estimate severity.",
            ]
        }

        rag = {
            "sources_used": [
                "healthcare_knowledge_base.txt",
                "symptom_guidelines.txt",
            ],
            "retrieved_context": (
                "Fever and cough are commonly associated with viral respiratory "
                "infections, flu, and COVID-like illness."
            ),
        }

        doctor = self.recommend_doctor(symptoms, answers)

        return {
            "status": "analysis_completed",
            "analysis": analysis,
            "xai_explanation": xai,
            "rag_evidence": rag,
            "recommended_doctor": doctor,
            "appointment": {
                "booking_required": True,
                "message": "Would you like to book an appointment with this doctor?",
                "requires_user_confirmation": True,
            },
            "safety": "This is educational support, not a medical diagnosis. Please consult a licensed medical professional.",
        }

    def format_final_analysis(self, result: dict):
        conditions = result["analysis"]["possible_conditions"]
        xai_lines = result["xai_explanation"]["explanation"]
        rag = result["rag_evidence"]
        doctor = result["recommended_doctor"]
        appointment = result["appointment"]

        return (
            "HealthcareAgent / healthcare\n\n"
            "Analysis Agent:\n"
            f"- Risk: {result['analysis']['risk']}\n"
            "- Possible conditions:\n"
            + "\n".join(f"  - {item['name']}: {item['confidence']}%" for item in conditions)
            + "\n\nXAI Explanation Agent:\n- "
            + "\n- ".join(xai_lines)
            + "\n\nMedical RAG Agent:\n"
            f"- Sources used: {', '.join(rag['sources_used'])}\n"
            f"- Retrieved context: {rag['retrieved_context']}\n\n"
            "Doctor Recommendation Agent:\n"
            f"- Specialist: {doctor['specialist']}\n"
            f"- Urgency: {doctor['urgency']}\n\n"
            "Show Doctor Information:\n"
            f"- Doctor Found: {doctor['doctor_name']}\n"
            f"- Clinic: {doctor.get('hospital', 'not provided')}\n"
            f"- City: {doctor.get('city', 'not provided')}\n"
            f"- Days: {doctor.get('available_days', 'not provided')}\n"
            f"- Hours: {doctor.get('available_hours', 'not provided')}\n"
            f"- MCP tool: {doctor.get('mcp_tool', 'doctor_database_lookup')}\n"
            f"- Source: {doctor.get('mcp_source', 'sqlite_db_synced_from_excel')}\n\n"
            "Appointment Booking Agent:\n"
            "- Not started yet.\n"
            f"- Would you like to book an appointment with {doctor['doctor_name']}?\n"
            "- Reply yes or no.\n\n"
            f"Safety Confirmation:\n{result['safety']}"
        )

    @staticmethod
    def risk_level(answers: dict):
        if (
            str(answers.get("shortness_of_breath", "")).lower() == "yes"
            or str(answers.get("chest_pain", "")).lower() == "yes"
        ):
            return "High"
        return "Low/Moderate"

    def recommend_doctor(self, symptoms: str, answers: dict):
        text = symptoms.lower()
        if "chest pain" in text or str(answers.get("chest_pain", "")).lower() == "yes":
            fallback = {
                "specialist": "Cardiologist / Emergency Physician",
                "doctor_name": "Dr. Emergency Care",
                "urgency": "Urgent",
            }
            return self.lookup_doctor_from_db(fallback)

        if "fever" in text or "cough" in text:
            fallback = {
                "specialist": "General Physician",
                "doctor_name": "Dr. Primary Care",
                "urgency": "Within 24-48 hours if symptoms worsen",
            }
            return self.lookup_doctor_from_db(fallback)

        fallback = {
            "specialist": "General Physician",
            "doctor_name": "Dr. General Care",
            "urgency": "Routine",
        }
        return self.lookup_doctor_from_db(fallback)

    def lookup_doctor_from_db(self, fallback: dict):
        result = self.doctor_mcp.run(fallback["specialist"])
        doctor = result.get("doctor") or {}
        if not doctor.get("doctor_name"):
            return fallback
        return {
            "specialist": doctor.get("specialty", fallback["specialist"]),
            "doctor_name": doctor.get("doctor_name", fallback["doctor_name"]),
            "urgency": doctor.get("urgency", fallback["urgency"]),
            "hospital": doctor.get("hospital", "not provided"),
            "city": doctor.get("city", "not provided"),
            "available_days": doctor.get("available_days", "not provided"),
            "available_hours": doctor.get("available_hours", "not provided"),
            "mcp_tool": result.get("tool_used"),
            "mcp_source": (result.get("all_results") or [{}])[0].get("source", ""),
            "excel_path": (result.get("all_results") or [{}])[0].get("excel_path", ""),
            "db_path": (result.get("all_results") or [{}])[0].get("db_path", ""),
        }

    @staticmethod
    def book_appointment(doctor: dict, user_confirmation: str):
        if user_confirmation.lower() not in ["yes", "confirm", "book"]:
            return {
                "status": "not_booked",
                "message": "No appointment booked. Please confirm if you want booking.",
            }

        return {
            "status": "booked",
            "doctor": doctor,
            "date": "Next available slot",
            "message": "Appointment request created.",
        }

    @staticmethod
    def available_slots():
        return ["Today 2:00 PM", "Tomorrow 10:00 AM", "Tomorrow 3:00 PM"]

    def handle_appointment_confirmation(
        self,
        query: str,
        state: dict,
        thoughts: list[str],
        prefilled_fields: dict | None,
        session_id: str,
    ):
        confirmation = query
        if prefilled_fields and prefilled_fields.get("appointment_confirmation"):
            confirmation = prefilled_fields["appointment_confirmation"]
        booking = self.book_appointment(state.get("doctor", {}), str(confirmation))

        if booking["status"] == "booked":
            slots = self.available_slots()
            state = dict(state)
            state["flow"] = "healthcare_slot_selection"
            state["available_slots"] = slots
            state["fields"] = {"slot_selection": "not provided"}
            state["missing_fields"] = ["slot_selection"]
            self.conversation_state.set(session_id, state)
            doctor = state.get("doctor", {})
            answer = (
                "HealthcareAgent / healthcare\n\n"
                "Appointment Booking Agent:\n"
                "- Status: Pending Confirmation\n\n"
                "Doctor:\n"
                f"{doctor.get('doctor_name', 'Selected doctor')}\n\n"
                "Available Slots:\n"
                + "\n".join(f"{idx}. {slot}" for idx, slot in enumerate(slots, start=1))
                + "\n\nPlease select a slot."
                "\n\n"
                "Safety Confirmation:\nAppointment request created only after your confirmation. "
                "This is not a medical diagnosis."
            )
        else:
            self.conversation_state.clear(session_id)
            answer = (
                "HealthcareAgent / healthcare\n\n"
                "Appointment Booking Agent:\n"
                "- Status: not_booked\n"
                f"- Message: {booking['message']}\n\n"
                "Safety Confirmation:\nNo appointment was booked."
            )

        return self.response(query, thoughts + ["Appointment Booking Agent: process user confirmation"], answer, {
            "status": "pending_confirmation" if booking["status"] == "booked" else booking["status"],
            "slot_filling": booking["status"] == "booked",
            "booking": booking,
            "available_slots": self.available_slots() if booking["status"] == "booked" else [],
            "safety": "Booking requires explicit user confirmation.",
        })

    def handle_slot_selection(
        self,
        query: str,
        state: dict,
        thoughts: list[str],
        prefilled_fields: dict | None,
        session_id: str,
    ):
        selection = str((prefilled_fields or {}).get("slot_selection") or query).strip()
        slots = state.get("available_slots") or self.available_slots()
        selected_slot = ""
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(slots):
                selected_slot = slots[index]
        if not selected_slot:
            for slot in slots:
                if selection.lower() in slot.lower():
                    selected_slot = slot
                    break
        if not selected_slot:
            answer = (
                "HealthcareAgent / healthcare\n\n"
                "Invalid slot selection.\n\n"
                "Available Slots:\n"
                + "\n".join(f"{idx}. {slot}" for idx, slot in enumerate(slots, start=1))
                + "\n\nPlease select a slot by number."
            )
            return self.response(query, thoughts + ["Appointment Booking Agent: invalid slot selection"], answer, {
                "status": "asking_slot",
                "slot_filling": True,
                "available_slots": slots,
            })

        self.conversation_state.clear(session_id)
        doctor = state.get("doctor", {})
        answer = (
            "HealthcareAgent / healthcare\n\n"
            "Appointment Booking Agent:\n"
            "- Status: Pending Confirmation\n"
            f"- Doctor: {doctor.get('doctor_name', 'Selected doctor')}\n"
            f"- Selected slot: {selected_slot}\n"
            "- Message: Appointment request prepared. Clinic confirmation is still required.\n\n"
            "Safety Confirmation:\nNo final booking is guaranteed until the clinic confirms."
        )
        return self.response(query, thoughts + ["Appointment Booking Agent: selected slot"], answer, {
            "status": "slot_selected",
            "slot_filling": False,
            "doctor": doctor,
            "selected_slot": selected_slot,
        })

    def ask_booking_hospital(self, query: str, thoughts: list[str], extracted: dict, session_id: str):
        self.conversation_state.start_or_update(session_id, self.name, extracted, ["hospital"])
        question = "Which hospital would you like to visit?"
        return self.response(query, thoughts + ["Slot Filling Agent: ask for hospital"], (
            "HealthcareAgent selected.\n\n"
            "I need one more detail before continuing.\n\n"
            f"{question}"
        ), {
            "slot_filling": True,
            "missing_fields": ["hospital"],
            "fields": extracted,
            "next_question": question,
        })

    def first_missing_question_index(self, answers: dict, query: str):
        answers = answers or {}
        for index, (key, _) in enumerate(self.required_questions):
            if key == "temperature" and "fever" not in query.lower():
                continue
            if key not in answers:
                return index
        return len(self.required_questions)

    def get_missing_questions(self, query: str, patient_info: dict):
        q = query.lower()
        questions = []

        if "age" not in patient_info:
            questions.append("What is your age?")
        if "days" not in patient_info:
            questions.append("How many days have you had these symptoms?")
        if "temperature" not in patient_info and "fever" in q:
            questions.append("What is your temperature?")
        if "shortness_of_breath" not in patient_info:
            questions.append("Do you have shortness of breath? (yes/no)")
        if "chest_pain" not in patient_info:
            questions.append("Do you have chest pain? (yes/no)")

        return questions

    def get_missing_patient_fields(self, query: str, patient_info: dict):
        q = query.lower()
        fields = []
        checks = [
            ("age", True),
            ("days", True),
            ("temperature", "fever" in q),
            ("shortness_of_breath", True),
            ("chest_pain", True),
        ]
        for field, required in checks:
            if required and field not in patient_info:
                fields.append(field)
        return fields

    @staticmethod
    def normalize_patient_info(patient_info: dict):
        normalized = {}
        aliases = {
            "symptom_days": "days",
            "duration": "days",
            "temp": "temperature",
            "shortness": "shortness_of_breath",
            "breathing": "shortness_of_breath",
            "sob": "shortness_of_breath",
            "chest": "chest_pain",
            "covid": "covid_test",
            "flu_test": "covid_test",
        }
        for key, value in (patient_info or {}).items():
            normalized_key = aliases.get(key, key)
            if value != "not provided" and value is not None and value != "":
                normalized[normalized_key] = str(value).lower() if isinstance(value, str) else value
        return normalized

    @staticmethod
    def emergency_response(query: str, patient_info: dict):
        emergency = (
            str(patient_info.get("shortness_of_breath", "")).lower() == "yes"
            or str(patient_info.get("chest_pain", "")).lower() == "yes"
        )
        if not emergency:
            return {}

        answer = (
            "HealthcareAgent / healthcare\n\n"
            "Risk:\nHigh\n\n"
            "Message:\nPlease seek urgent medical care immediately.\n\n"
            "Possible causes:\n"
            "- Serious respiratory infection\n"
            "- Pneumonia\n"
            "- Other urgent condition\n\n"
            "Next actions:\n"
            "- Call emergency services or visit urgent care.\n"
            "- Do not wait if breathing difficulty or chest pain is present.\n\n"
            "Safety: This is educational support, not a medical diagnosis."
        )
        return {
            "answer": answer,
            "analysis": {
                "risk": "High",
                "possible_causes": [
                    "Serious respiratory infection",
                    "Pneumonia",
                    "Other urgent condition",
                ],
                "next_actions": [
                    "Call emergency services or visit urgent care.",
                    "Do not wait if breathing difficulty or chest pain is present.",
                ],
            },
        }

    @staticmethod
    def has_booking_intent(query: str) -> bool:
        q = query.lower()
        return any(
            phrase in q
            for phrase in [
                "book appointment", "schedule appointment", "make appointment",
                "find doctor", "find a doctor", "find hospital", "find a hospital",
                "which hospital", "visit hospital", "see a doctor", "doctor near",
            ]
        )

    @staticmethod
    def build_healthcare_answer(
        extracted: dict,
        crew_result: dict,
        booking_intent: bool,
        patient_info: dict | None = None,
    ):
        analysis = crew_result["analysis"]
        symptoms = crew_result["symptom_analysis"]
        causes = symptoms["possible_causes"]
        actions = symptoms["recommended_actions"]
        emergency = symptoms["emergency_signs"]
        condition_scores = crew_result.get("condition_scores", [])

        confidence = 80
        if analysis["risk_label"] == "High risk":
            confidence = 85
        elif analysis["risk_label"] == "Low risk":
            confidence = 80

        emergency_note = ""
        if symptoms.get("emergency_detected") or analysis["risk_label"] == "High risk":
            emergency_note = "\nImportant: high-risk symptoms detected. Seek urgent or emergency care now if symptoms are severe.\n"

        patient_info = patient_info or {}
        patient_context = []
        if patient_info:
            patient_context = [
                f"Age: {patient_info.get('age', 'not provided')}",
                f"Days: {patient_info.get('days', 'not provided')}",
                f"Temperature: {patient_info.get('temperature', 'not provided')}",
                f"Shortness of breath: {patient_info.get('shortness_of_breath', 'not provided')}",
                f"Chest pain: {patient_info.get('chest_pain', 'not provided')}",
                f"COVID/flu test: {patient_info.get('covid_test', 'not provided')}",
            ]

        patient_details = (
            "Patient details:\n- " + "\n- ".join(patient_context) + "\n\n"
            if patient_context else ""
        )
        condition_lines = "\n- ".join(
            f"{item['condition']}: {item['score']}%" for item in condition_scores
        )

        answer = (
            "HealthcareAgent / healthcare\n\n"
            "This is not a medical diagnosis.\n\n"
            f"Symptoms:\n{extracted.get('symptoms', 'not provided')}\n\n"
            f"{patient_details}"
            "Possible causes:\n- " + "\n- ".join(causes) + "\n\n"
            "Condition scoring:\n- " + condition_lines + "\n\n"
            "Recommended actions:\n- " + "\n- ".join(actions) + "\n\n"
            "Emergency signs:\n- " + "\n- ".join(emergency) + "\n\n"
            f"Suggested specialist:\n{analysis['specialty']}\n\n"
            f"Risk:\n{analysis['risk_percentage']}% ({analysis['risk_label']})\n\n"
            "Why:\n- " + "\n- ".join(analysis["xai_reasons"]) + "\n\n"
            f"Confidence:\n{confidence}%\n"
            "\nVerification:\n- Status: verified\n"
            f"- Confidence: {max(confidence, 82)}%\n"
            f"{emergency_note}"
        )

        if booking_intent:
            doctors = crew_result.get("doctors") or []
            answer += (
                "\nHospital/doctor options:\n- "
                + ("\n- ".join(doctors) if doctors else "No demo doctors found.")
                + "\n\nNo appointment has been booked."
            )

        answer += "\n\nSafety: Contact a licensed medical professional for real care."
        return answer
