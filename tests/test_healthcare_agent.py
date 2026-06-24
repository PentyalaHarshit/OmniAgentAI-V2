from agents.agent_router import AgentRouter
from agents.healthcare_agent import HealthcareAgent


def test_symptom_query_asks_first_triage_question_without_hospital_first():
    agent = HealthcareAgent()
    session_id = "healthcare_triage_first"
    agent.conversation_state.clear(session_id)

    result = agent.run("I have fever and cough. What should I do?", session_id=session_id)
    answer = result["answer"]

    assert result["extra"]["status"] == "asking_question"
    assert result["extra"]["slot_filling"] is True
    assert "observation_guided_tot_react" in result["extra"]
    assert any("Observation-Guided ToT-ReAct" in thought for thought in result["thoughts"])
    assert "Which hospital would you like to visit?" not in answer
    assert "What is your age?" in answer
    assert result["extra"]["question"] == "What is your age?"
    agent.conversation_state.clear(session_id)


def test_healthcare_triage_conversation_asks_one_question_at_a_time():
    agent = HealthcareAgent()
    session_id = "healthcare_triage_sequence"
    agent.conversation_state.clear(session_id)

    prompts = [
        ("I have fever and cough", "What is your age?"),
        ("25", "How many days have you had these symptoms?"),
        ("2 days", "What is your temperature?"),
        ("101", "Do you have shortness of breath? (yes/no)"),
        ("no", "Do you have chest pain? (yes/no)"),
    ]

    for message, expected_question in prompts:
        result = agent.run(message, session_id=session_id)
        assert result["extra"]["status"] == "asking_question"
        assert expected_question in result["answer"]

    result = agent.run("no", session_id=session_id)

    assert result["extra"]["status"] == "analysis_completed"
    assert result["extra"]["analysis"]["risk"] == "Low/Moderate"
    assert result["extra"]["patient_info"]["age"] == "25"
    assert result["extra"]["patient_info"]["days"] == "2 days"
    assert result["extra"]["patient_info"]["temperature"] == "101"
    assert "Analysis Agent:" in result["answer"]
    assert "XAI Explanation Agent:" in result["answer"]
    assert "Medical RAG Agent:" in result["answer"]
    assert "Doctor Recommendation Agent:" in result["answer"]
    assert "Show Doctor Information:" in result["answer"]
    assert "Would you like to book an appointment with Dr. Sarah Johnson?" in result["answer"]
    assert "Safety Confirmation:" in result["answer"]
    assert result["extra"]["recommended_doctor"]["specialist"] == "General Physician"
    assert result["extra"]["recommended_doctor"]["doctor_name"] == "Dr. Sarah Johnson"
    assert result["extra"]["recommended_doctor"]["hospital"] == "CityCare Clinic"
    assert result["extra"]["recommended_doctor"]["city"] == "Dallas"
    assert result["extra"]["recommended_doctor"]["mcp_tool"] == "doctor_database_lookup"
    assert result["extra"]["recommended_doctor"]["mcp_source"] == "sqlite_db_synced_from_excel"
    assert result["extra"]["appointment"]["requires_user_confirmation"] is True
    agent.conversation_state.clear(session_id)


def test_healthcare_appointment_booking_requires_confirmation():
    agent = HealthcareAgent()
    session_id = "healthcare_booking_confirmation"
    agent.conversation_state.clear(session_id)

    for message in ["I have fever and cough", "25", "2 days", "101", "no", "no"]:
        result = agent.run(message, session_id=session_id)

    assert result["extra"]["status"] == "analysis_completed"

    declined = agent.run("no", session_id=session_id)
    assert declined["extra"]["status"] == "not_booked"
    assert "No appointment booked" in declined["answer"]

    for message in ["I have fever and cough", "25", "2 days", "101", "no", "no"]:
        result = agent.run(message, session_id=session_id)

    confirmed = agent.run("yes", session_id=session_id)
    assert confirmed["extra"]["status"] == "pending_confirmation"
    assert confirmed["extra"]["booking"]["doctor"]["doctor_name"] == "Dr. Sarah Johnson"
    assert "Available Slots:" in confirmed["answer"]
    assert "Today 2:00 PM" in confirmed["answer"]
    assert "Please select a slot." in confirmed["answer"]

    selected = agent.run("2", session_id=session_id)
    assert selected["extra"]["status"] == "slot_selected"
    assert selected["extra"]["selected_slot"] == "Tomorrow 10:00 AM"
    assert "Clinic confirmation is still required" in selected["answer"]
    agent.conversation_state.clear(session_id)


def test_healthcare_triage_repeats_invalid_age_question():
    agent = HealthcareAgent()
    session_id = "healthcare_invalid_age"
    agent.conversation_state.clear(session_id)

    agent.run("I have fever and cough", session_id=session_id)
    invalid = agent.run("abc", session_id=session_id)

    assert invalid["extra"]["validation_status"] == "invalid"
    assert invalid["extra"]["question"] == "What is your age?"
    assert "Invalid age." in invalid["answer"]
    assert "Please enter a valid age between 0 and 120 years." in invalid["answer"]

    valid = agent.run("25", session_id=session_id)
    assert valid["extra"]["validation_status"] == "pending"
    assert valid["extra"]["question"] == "How many days have you had these symptoms?"
    agent.conversation_state.clear(session_id)


def test_healthcare_triage_repeats_invalid_temperature_question():
    agent = HealthcareAgent()
    session_id = "healthcare_invalid_temperature"
    agent.conversation_state.clear(session_id)

    for message in ["I have fever and cough", "25", "2 days"]:
        agent.run(message, session_id=session_id)

    invalid = agent.run("hello", session_id=session_id)

    assert invalid["extra"]["validation_status"] == "invalid"
    assert invalid["extra"]["question"] == "What is your temperature?"
    assert "Invalid temperature." in invalid["answer"]
    assert "Example: 101 F or 38.3 C" in invalid["answer"]

    valid = agent.run("101", session_id=session_id)
    assert valid["extra"]["question"] == "Do you have shortness of breath? (yes/no)"
    agent.conversation_state.clear(session_id)


def test_healthcare_triage_repeats_invalid_yes_no_question():
    agent = HealthcareAgent()
    session_id = "healthcare_invalid_yes_no"
    agent.conversation_state.clear(session_id)

    for message in ["I have fever and cough", "25", "2 days", "101"]:
        agent.run(message, session_id=session_id)

    invalid = agent.run("maybe", session_id=session_id)

    assert invalid["extra"]["validation_status"] == "invalid"
    assert invalid["extra"]["question"] == "Do you have shortness of breath? (yes/no)"
    assert "Invalid response." in invalid["answer"]
    assert "Please answer only: yes or no." in invalid["answer"]

    valid = agent.run("no", session_id=session_id)
    assert valid["extra"]["question"] == "Do you have chest pain? (yes/no)"
    agent.conversation_state.clear(session_id)


def test_symptom_query_with_patient_info_returns_advice():
    agent = HealthcareAgent()
    patient_info = {
        "age": 25,
        "days": 2,
        "temperature": 101,
        "shortness_of_breath": "no",
        "chest_pain": "no",
    }

    result = agent.run("I have fever and cough. What should I do?", patient_info=patient_info)
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert result["extra"]["status"] == "analyzed"
    assert result["extra"]["slot_filling"] is False
    assert "Possible causes:" in answer
    assert "Common cold" in answer
    assert "Influenza (flu)" in answer
    assert "COVID-19" in answer
    assert "Recommended actions:" in answer
    assert "Rest" in answer
    assert "Drink fluids" in answer
    assert "Consider COVID/flu testing" in answer
    assert "Emergency signs:" in answer
    assert "Difficulty breathing" in answer
    assert "Suggested specialist:" in answer
    assert "General Physician" in answer
    assert "Verification:" in answer
    assert "Confidence:" in answer
    assert crew["condition_scores"][0]["condition"] == "Influenza (flu)"


def test_healthcare_booking_intent_can_ask_for_hospital():
    agent = HealthcareAgent()

    result = agent.run("Book appointment for fever and cough")

    assert result["extra"]["slot_filling"] is True
    assert "hospital" in result["extra"]["missing_fields"]
    assert "Which hospital would you like to visit?" in result["answer"]


def test_emergency_patient_info_returns_high_risk_message():
    agent = HealthcareAgent()
    patient_info = {
        "age": 25,
        "days": 2,
        "temperature": 101,
        "shortness_of_breath": "yes",
        "chest_pain": "no",
    }

    result = agent.run("I have fever and cough. What should I do?", patient_info=patient_info)

    assert result["extra"]["status"] == "high_risk"
    assert "Risk:\nHigh" in result["answer"]
    assert "Please seek urgent medical care immediately." in result["answer"]


def test_router_sends_symptom_query_to_healthcare():
    route, agent = AgentRouter().route("I have fever and cough. What should I do?")

    assert route == "healthcare"
    assert agent.name == "HealthcareAgent"
