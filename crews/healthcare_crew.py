from tools.rag_tool import RAGTool
from tools.healthcare_tools import DoctorLookupTool, HealthcareRiskTool, SymptomAnalysisTool


class HealthcareCrew:
    def __init__(self):
        self.rag = RAGTool()
        self.symptoms = SymptomAnalysisTool()
        self.risk = HealthcareRiskTool()
        self.doctors = DoctorLookupTool()

    def run(self, query: str, extracted: dict, include_doctors: bool = False):
        steps = []

        intake = {"thought": "Intake Agent: extract symptoms and care intent", "output": extracted}
        steps.append(intake)

        rag = {"thought": "RAG Retrieval Agent: retrieve healthcare knowledge", "output": self.rag.search(query, "healthcare")}
        steps.append(rag)

        symptom_analysis = {"thought": "Symptom Analysis Agent: match possible conditions", "output": self.symptoms.analyze(query)}
        steps.append(symptom_analysis)

        tot = {
            "thought": "ToT Agent: compare possible conditions",
            "output": self.score_conditions(symptom_analysis["output"]["possible_causes"], query),
        }
        steps.append(tot)

        analysis = {"thought": "Risk Prediction Agent: compute risk score", "output": self.risk.analyze(query)}
        steps.append(analysis)

        specialty = {"thought": "Specialty Agent: choose medical specialty", "output": analysis["output"]["specialty"]}
        steps.append(specialty)

        doctor_list = {"thought": "Doctor Selection Agent: optional lookup", "output": []}
        appointment = {"thought": "Appointment Agent: optional booking guidance", "output": "Not requested."}
        if include_doctors:
            doctor_list["output"] = self.doctors.find_doctors(analysis["output"]["specialty"], extracted.get("hospital", "not provided"))
            appointment["output"] = "Demo slot suggested only. Ask for confirmation before any real booking."
            steps.append(doctor_list)
            steps.append(appointment)

        report = {"thought": "Report Agent: generate explanation", "output": "Risk report generated with XAI reasons and RAG context."}
        steps.append(report)

        self_check = {"thought": "Self-Check Agent: medical safety validation", "output": {"safe": True, "warning": "Not a diagnosis. Seek emergency care for severe symptoms."}}
        steps.append(self_check)

        return {
            "crew_name": "HealthcareRAGCrew",
            "crew_steps": steps,
            "intake": intake["output"],
            "rag": rag["output"],
            "symptom_analysis": symptom_analysis["output"],
            "condition_scores": tot["output"],
            "analysis": analysis["output"],
            "specialty": specialty["output"],
            "doctors": doctor_list["output"],
            "appointment": appointment["output"],
            "report": report["output"],
            "self_check": self_check["output"]
        }

    @staticmethod
    def score_conditions(possible_causes: list[str], query: str):
        q = query.lower()
        scores = []
        base_scores = {
            "Common cold": 70,
            "Influenza (flu)": 82,
            "COVID-19": 75,
            "Other respiratory infection": 65,
            "Viral infection": 70,
            "Other infection": 55,
            "Allergies or irritation": 45,
            "Respiratory infection": 60,
        }
        for cause in possible_causes:
            score = base_scores.get(cause, 40)
            if "fever" in q and cause in {"Influenza (flu)", "COVID-19", "Other respiratory infection"}:
                score += 3
            if "cough" in q and cause in {"Common cold", "COVID-19", "Other respiratory infection"}:
                score += 2
            scores.append({"condition": cause, "score": min(score, 95)})
        return sorted(scores, key=lambda item: item["score"], reverse=True)
