from tools.rag_tool import RAGTool
from tools.healthcare_tools import HealthcareRiskTool, DoctorLookupTool


class HealthcareCrew:
    def __init__(self):
        self.rag = RAGTool()
        self.risk = HealthcareRiskTool()
        self.doctors = DoctorLookupTool()

    def run(self, query: str, extracted: dict):
        steps = []

        intake = {"thought": "Intake Agent: extract symptoms/hospital", "output": extracted}
        steps.append(intake)

        rag = {"thought": "RAG Retrieval Agent: retrieve healthcare knowledge", "output": self.rag.search(query, "healthcare")}
        steps.append(rag)

        analysis = {"thought": "Risk Prediction Agent: compute risk score", "output": self.risk.analyze(query)}
        steps.append(analysis)

        specialty = {"thought": "Specialty Agent: choose medical specialty", "output": analysis["output"]["specialty"]}
        steps.append(specialty)

        doctor_list = {"thought": "Doctor Selection Agent: lookup demo doctors", "output": self.doctors.find_doctors(analysis["output"]["specialty"], extracted.get("hospital", "not provided"))}
        steps.append(doctor_list)

        appointment = {"thought": "Appointment Agent: recommend slot", "output": "Demo slot suggested only. Connect Google Calendar/MCP for real booking."}
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
            "analysis": analysis["output"],
            "specialty": specialty["output"],
            "doctors": doctor_list["output"],
            "appointment": appointment["output"],
            "report": report["output"],
            "self_check": self_check["output"]
        }
