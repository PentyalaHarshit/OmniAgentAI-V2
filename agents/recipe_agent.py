from agents.base_agent import BaseAgent


class RecipeAgent(BaseAgent):
    name = "RecipeAgent"
    agent_type = "Recipe"
    rag_category = "recipe"

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        answer = "\n".join([
            "RecipeAgent / recipe",
            "",
            "High-Protein Vegetarian Meals",
            "",
            "Breakfast:",
            "Paneer Omelette",
            "",
            "Lunch:",
            "Dal + Rice",
            "",
            "Dinner:",
            "Tofu Stir Fry",
            "",
            "Snack:",
            "Greek yogurt with nuts",
        ])
        return self.response(query, ["RecipeAgent: generated vegetarian high-protein meal ideas."], answer, {})
