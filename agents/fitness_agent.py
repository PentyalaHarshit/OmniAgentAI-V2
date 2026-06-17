from agents.base_agent import BaseAgent


class FitnessAgent(BaseAgent):
    name = "FitnessAgent"
    agent_type = "Fitness"
    rag_category = "fitness"

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        answer = "\n".join([
            "FitnessAgent / fitness",
            "",
            "Workout Plan for Muscle Gain",
            "",
            "Day 1: Chest",
            "- Bench press, incline dumbbell press, cable fly, triceps dips",
            "",
            "Day 2: Back",
            "- Pull-ups, barbell row, lat pulldown, face pulls",
            "",
            "Day 3: Legs",
            "- Squat, Romanian deadlift, leg press, calf raises",
            "",
            "Day 4: Shoulders",
            "- Overhead press, lateral raise, rear delt fly",
            "",
            "Day 5: Arms + Core",
            "- Curls, triceps extensions, planks, hanging knee raises",
            "",
            "Recovery",
            "- Sleep 7-9 hours, eat enough protein, progress weights slowly.",
            "",
            "Safety: consult a qualified trainer or clinician if you have injuries or medical conditions.",
        ])
        return self.response(query, ["Plan Generator: created a muscle-gain split."], answer, {})
