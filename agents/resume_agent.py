from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.resume_crew import ResumeCrew


class ResumeAgent(BaseAgent):
    name = "ResumeAgent"
    agent_type = "Resume"
    rag_category = "resume"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = ResumeCrew()

    def run(self, query: str):
        file_context = query.split("[Uploaded File Context]", 1)[-1].strip() if "[Uploaded File Context]" in query else ""
        tasks = ["Read resume/JD", "Retrieve resume RAG", "Extract skills", "Estimate ATS", "Rewrite bullets", "Self-check truthfulness"]
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=14)
        result = self.crew.run(query, file_context)
        crew_thoughts = [s["thought"] for s in result["crew_steps"]]
        return self.response(query, thoughts + crew_thoughts, result["answer"], {"crew_result": result})
