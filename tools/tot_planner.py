class ToTPlanner:
    def create_thoughts(self, agent_type: str, query: str, base_tasks: list[str], max_thoughts: int = 14):
        thoughts = [f"ToT root for {agent_type}: understand user goal"]

        for i, task in enumerate(base_tasks, start=1):
            thoughts.append(f"Thought branch {i}: {task}")

        thoughts.extend([
            "Alternative branch: identify missing information",
            "RAG branch: retrieve relevant knowledge before action",
            "Tool branch: select API/tool/compiler/payment/mock service",
            "Critic branch: evaluate correctness and risk",
            "Pruning branch: remove unsafe or weak options",
            "Best path branch: choose safest useful plan",
        ])

        return thoughts[:max_thoughts]

    def create_observation_guided_loop(
        self,
        agent_type: str,
        query: str,
        strategy: str,
        actions: list[dict],
        verified: bool = False,
        max_steps: int = 12,
    ):
        loop = [
            {
                "phase": "Thought Tree",
                "detail": f"{agent_type}: evaluate candidate strategies for {query}",
            },
            {
                "phase": "Strategy Selection",
                "detail": strategy,
            },
        ]

        for idx, action in enumerate(actions, start=1):
            loop.extend([
                {
                    "phase": f"Action {idx}",
                    "detail": action.get("action", "Execute selected step"),
                },
                {
                    "phase": f"Observation {idx}",
                    "detail": action.get("observation", "No observation recorded"),
                },
            ])
            if action.get("replan"):
                loop.append({
                    "phase": "New Thought Tree",
                    "detail": action.get(
                        "replan",
                        "Use observation to revise candidate strategies.",
                    ),
                })

        loop.append({
            "phase": "Verifier",
            "detail": "Accepted" if verified else "Needs more evidence or user input",
        })
        return loop[:max_steps]

    @staticmethod
    def format_observation_loop(loop: list[dict]):
        return [
            f"Observation-Guided ToT-ReAct: {step['phase']} - {step['detail']}"
            for step in loop
        ]
