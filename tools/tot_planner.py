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
