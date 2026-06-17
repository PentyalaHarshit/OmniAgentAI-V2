from tools.doctor_mcp_tools import DoctorMCPToolRunner


class HealthcareRiskTool:
    def analyze(self, query: str):
        q = query.lower()
        score = 10
        reasons = []

        if "chest pain" in q:
            score += 40
            reasons.append("Chest pain detected: +40 risk")
        if "breathing" in q or "shortness of breath" in q:
            score += 30
            reasons.append("Breathing difficulty detected: +30 risk")
        if "diabetes" in q:
            score += 20
            reasons.append("Diabetes history detected: +20 risk")
        if "blood pressure" in q or "hypertension" in q:
            score += 15
            reasons.append("Blood pressure issue detected: +15 risk")
        if "headache" in q:
            score += 20
            reasons.append("Headache detected: +20 risk")
        if "fever" in q:
            score += 10
            reasons.append("Fever detected: +10 risk")
        if "cough" in q:
            score += 10
            reasons.append("Cough detected: +10 risk")

        score = min(score, 95)

        if "chest pain" in q or "breathing" in q or "shortness of breath" in q:
            specialty = "Cardiology"
            priority = "High"
        elif "diabetes" in q:
            specialty = "Endocrinology"
            priority = "Medium"
        elif "headache" in q:
            specialty = "Neurology"
            priority = "Medium"
        else:
            specialty = "General Physician"
            priority = "Low"

        label = "High risk" if score >= 70 else "Medium risk" if score >= 40 else "Low risk"

        return {
            "risk_percentage": score,
            "risk_label": label,
            "priority": priority,
            "specialty": specialty,
            "xai_reasons": reasons or ["No major emergency keyword detected"]
        }


class SymptomAnalysisTool:
    EMERGENCY_SIGNS = [
        "Difficulty breathing",
        "Chest pain",
        "Confusion",
        "Persistent high fever",
        "Blue lips or face",
        "Severe dehydration",
    ]

    def analyze(self, query: str):
        q = query.lower()
        possible_causes = []
        advice = [
            "Rest",
            "Drink fluids",
            "Monitor temperature",
        ]

        if "fever" in q and "cough" in q:
            possible_causes.extend([
                "Common cold",
                "Influenza (flu)",
                "COVID-19",
                "Other respiratory infection",
            ])
            advice.append("Consider COVID/flu testing")
            advice.append("Seek medical care if symptoms worsen")
        elif "fever" in q:
            possible_causes.extend([
                "Viral infection",
                "Influenza (flu)",
                "Other infection",
            ])
            advice.append("Seek medical care if fever is high or persistent")
        elif "cough" in q:
            possible_causes.extend([
                "Common cold",
                "Allergies or irritation",
                "Respiratory infection",
            ])
            advice.append("Avoid smoke and other airway irritants")
        else:
            possible_causes.append("Cause unclear from the provided symptoms")
            advice.append("Share more symptom details or contact a clinician")

        emergency_detected = any(
            phrase in q
            for phrase in ["difficulty breathing", "shortness of breath", "chest pain", "confusion", "blue lips"]
        )

        return {
            "possible_causes": possible_causes,
            "recommended_actions": advice,
            "emergency_signs": self.EMERGENCY_SIGNS[:4],
            "emergency_detected": emergency_detected,
        }


class DoctorLookupTool:
    def __init__(self):
        self.mcp = DoctorMCPToolRunner()
        self.doctors = {
            "Cardiology": ["Dr. Sarah Johnson - Cardiologist - 9:00 AM", "Dr. Michael Lee - Cardiologist - 2:30 PM"],
            "Endocrinology": ["Dr. Anita Rao - Endocrinologist - 11:00 AM"],
            "Neurology": ["Dr. Emily Chen - Neurologist - 10:30 AM"],
            "General Physician": ["Dr. James Smith - General Physician - 1:00 PM"],
            "General Medicine": ["Dr. James Smith - General Physician - 1:00 PM"],
        }

    def find_doctors(self, specialty: str, hospital: str):
        result = self.mcp.run(specialty)
        doctor = result.get("doctor") or {}
        if doctor.get("doctor_name"):
            return [
                (
                    f"{doctor['doctor_name']} - {doctor.get('specialty', specialty)} - "
                    f"{doctor.get('urgency', 'Next available')} - {doctor.get('hospital', hospital)}"
                )
            ]
        return self.doctors.get(specialty, self.doctors["General Medicine"])
