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

        score = min(score, 95)

        if "chest pain" in q or "breathing" in q:
            specialty = "Cardiology"
            priority = "High"
        elif "diabetes" in q:
            specialty = "Endocrinology"
            priority = "Medium"
        elif "headache" in q:
            specialty = "Neurology"
            priority = "Medium"
        else:
            specialty = "General Medicine"
            priority = "Low"

        label = "High risk" if score >= 70 else "Medium risk" if score >= 40 else "Low risk"

        return {
            "risk_percentage": score,
            "risk_label": label,
            "priority": priority,
            "specialty": specialty,
            "xai_reasons": reasons or ["No major emergency keyword detected"]
        }


class DoctorLookupTool:
    def __init__(self):
        self.doctors = {
            "Cardiology": ["Dr. Sarah Johnson - Cardiologist - 9:00 AM", "Dr. Michael Lee - Cardiologist - 2:30 PM"],
            "Endocrinology": ["Dr. Anita Rao - Endocrinologist - 11:00 AM"],
            "Neurology": ["Dr. Emily Chen - Neurologist - 10:30 AM"],
            "General Medicine": ["Dr. James Smith - General Medicine - 1:00 PM"]
        }

    def find_doctors(self, specialty: str, hospital: str):
        return self.doctors.get(specialty, self.doctors["General Medicine"])
