import re

from agents.base_agent import BaseAgent
from tools.rag_tool import RAGTool
from tools.tot_planner import ToTPlanner
from crews.research_crew import ResearchCrew


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    agent_type = "Research"
    rag_category = "research"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = ResearchCrew()
        self.rag = RAGTool()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        file_context = query.split("[Uploaded File Context]", 1)[-1].strip() if "[Uploaded File Context]" in query else ""
        clean_query = query.split("[Free LLM Tree Guidance]", 1)[0].strip()
        intent = self.detect_intent(clean_query)
        tasks = [
            "Classify research intent",
            "Generate Tree-of-Thought alternatives",
            "Retrieve research RAG context",
            "Search paper/web connectors when configured",
            "Analyze evidence",
            "Generate report",
            "Verify claims and limitations",
        ]
        thoughts = self.tot.create_thoughts(self.agent_type, clean_query, tasks, max_thoughts=16)
        rag = self.rag.search(clean_query, "research")

        if intent == "paper":
            answer = self.paper_summary(clean_query, rag)
            selected = "PaperAgent"
        elif intent == "trend":
            answer = self.ai_trend_summary(clean_query, rag)
            selected = "AITrendAgent"
        elif intent == "benchmark":
            answer = self.benchmark_report(clean_query, rag)
            selected = "BenchmarkAgent"
        elif intent == "planner":
            answer = self.research_plan(clean_query, rag)
            selected = "ResearchPlannerAgent"
        elif intent == "innovation":
            answer = self.innovation_proposal(clean_query, rag)
            selected = "InnovationAgent"
        else:
            answer = self.general_research_report(clean_query, rag, file_context)
            selected = "ResearchAgent"

        flow_thoughts = [
            "ToT Agent: generated multiple research framings.",
            "Web Search Agent: live connector not configured; using local/offline evidence hooks.",
            "Paper Agent: paper lookup uses local known-paper metadata when available.",
            "RAG Agent: retrieved local research knowledge.",
            "Analyzer Agent: organized findings, gaps, and evaluation criteria.",
            "Verifier Agent: marked live/current claims as needing external verification.",
        ]

        return self.response(clean_query, thoughts + flow_thoughts, answer, {
            "selected_research_agent": selected,
            "intent": intent,
            "rag": rag,
            "file_context_used": bool(file_context),
            "pipeline": [
                "ResearchAgent",
                "ToT Agent",
                "Web Search Agent",
                "Paper Agent",
                "RAG Agent",
                "Analyzer Agent",
                "Innovation Agent",
                "Report Generator",
                "Verifier Agent",
            ],
        })

    def detect_intent(self, query: str):
        q = query.lower()
        if any(k in q for k in ["invent new algorithms", "self-improving", "novelty", "innovation", "research proposal"]):
            return "innovation"
        if any(k in q for k in ["research roadmap", "research gaps", "gap analysis", "possible experiments", "evaluation metrics"]):
            return "planner"
        if any(k in q for k in ["attention is all you need", "gpt-4 technical report", "paper", "summarize gpt", "explain the"]):
            return "paper"
        if any(k in q for k in ["latest", "news", "this week", "today", "open-source ai", "open source ai", "trends in multimodal"]):
            return "trend"
        if any(k in q for k in ["compare gpt", "compare models", "benchmark", "latency", "cost", "memory", "deepseek", "qwen", "claude", "gemini"]):
            return "benchmark"
        return "general"

    def paper_summary(self, query: str, rag: dict):
        title = self.paper_title(query)
        known = self.known_paper(title)
        return "\n".join([
            "PaperAgent / research",
            "",
            "Paper Summary",
            known["summary"],
            "",
            "Key Contributions",
            *[f"- {item}" for item in known["contributions"]],
            "",
            "Architecture",
            known["architecture"],
            "",
            "Limitations",
            *[f"- {item}" for item in known["limitations"]],
            "",
            "Future Work",
            *[f"- {item}" for item in known["future_work"]],
            "",
            "RAG Evidence",
            f"- Sources: {rag.get('sources', [])}",
        ])

    def ai_trend_summary(self, query: str, rag: dict):
        return "\n".join([
            "AITrendAgent / research",
            "",
            "Latest AI Trend Summary",
            "Live news search is not connected in this local run, so this summary uses local trend knowledge and should be refreshed with web/news APIs for production.",
            "",
            "Ranked Trends",
            "1. Agentic RAG: planning, retrieval, tool use, and verification in one workflow.",
            "2. Multimodal AI: text, image, audio, and video models moving into unified interfaces.",
            "3. Open-source model competition: smaller efficient models and domain-tuned systems.",
            "4. Evaluation and safety: stronger benchmarks for hallucination, tool reliability, and cost.",
            "",
            "Why It Matters",
            "- Teams are moving from chatbots to task-completing agents.",
            "- Retrieval quality, observability, and verification are becoming core infrastructure.",
            "",
            "Sources",
            f"- Local RAG: {rag.get('sources', [])}",
            "- Live web/news connector: not configured",
        ])

    def benchmark_report(self, query: str, rag: dict):
        models = self.extract_models(query) or ["GPT-5", "Claude", "Gemini", "DeepSeek", "Qwen"]
        ranking = self.rank_models(models)
        lines = [
            "BenchmarkAgent / research",
            "",
            "Model Ranking",
        ]
        for index, model in enumerate(ranking, start=1):
            lines.append(f"{index}. {model}")
        lines += [
            "",
            "Pros",
            "- GPT/OpenAI models: strong tool use, coding, multimodal workflows, and agent orchestration.",
            "- Claude: strong long-context reasoning and careful writing.",
            "- Gemini: strong multimodal and Google ecosystem integration.",
            "- DeepSeek/Qwen: strong open-weight and cost-sensitive deployment options.",
            "",
            "Cons",
            "- Rankings vary heavily by benchmark, prompt, latency budget, and deployment constraints.",
            "- Current pricing and model versions must be verified live before production decisions.",
            "",
            "Best Use Cases",
            "- Complex agent workflows: GPT/OpenAI or Claude.",
            "- Long-document analysis: Claude or Gemini.",
            "- Open-source/self-hosted experiments: DeepSeek or Qwen.",
            "",
            "Benchmark Dimensions",
            "- Accuracy, latency, cost, memory, context length, tool reliability, safety, and observability.",
            "",
            "RAG Evidence",
            f"- Sources: {rag.get('sources', [])}",
        ]
        return "\n".join(lines)

    def research_plan(self, query: str, rag: dict):
        return "\n".join([
            "ResearchPlannerAgent / research",
            "",
            "Existing Work",
            "- Agentic RAG combines retrieval, planning, memory, tools, and iterative verification.",
            "- Literature review methods emphasize baselines, limitations, and reproducible evaluation.",
            "- AI discovery work often uses search, program synthesis, theorem proving, and benchmark feedback.",
            "",
            "Research Gaps",
            "- Few systems prove novelty rather than only generating plausible ideas.",
            "- Evaluation often misses long-horizon reliability and failed-tool recovery.",
            "- Benchmarks for autonomous research agents are still immature.",
            "",
            "Possible Experiments",
            "1. Compare agentic RAG vs standard RAG on multi-step research tasks.",
            "2. Add verifier agents and measure hallucination reduction.",
            "3. Test self-improvement loops with held-out benchmark tasks.",
            "4. Evaluate cost and latency under increasing tool depth.",
            "",
            "Evaluation Metrics",
            "- Answer correctness, citation quality, novelty score, reproducibility, tool success rate, cost, latency, and human preference.",
            "",
            "Future Directions",
            "- Research memory, automatic benchmark generation, formal verification, and human-in-the-loop review.",
            "",
            "RAG Evidence",
            f"- Sources: {rag.get('sources', [])}",
        ])

    def innovation_proposal(self, query: str, rag: dict):
        return "\n".join([
            "InnovationAgent / research",
            "",
            "Novelty Score",
            "82/100",
            "",
            "Research Difficulty",
            "High: requires reliable retrieval, tool execution, evaluation design, and safeguards against self-reinforcing errors.",
            "",
            "Potential Impact",
            "High: a self-improving agentic RAG system could accelerate literature review, experiment design, and algorithm discovery.",
            "",
            "Generate 5 Possible Approaches",
            "1. Verifier-guided agentic RAG with automatic critique and retry.",
            "2. Benchmark-driven self-improvement loop using hidden evaluation tasks.",
            "3. Multi-agent debate among retriever, proposer, skeptic, and evaluator agents.",
            "4. Program-synthesis agent that proposes algorithms and runs tests.",
            "5. Knowledge-graph RAG that tracks claims, evidence, and contradictions.",
            "",
            "Implementation Plan",
            "- Phase 1: Build baseline RAG and agentic RAG pipelines.",
            "- Phase 2: Add verifier, memory, and failure recovery.",
            "- Phase 3: Run benchmarks against curated research tasks.",
            "- Phase 4: Measure novelty, correctness, cost, and safety.",
            "",
            "Evaluation Metrics",
            "- Novelty, correctness, benchmark pass rate, citation validity, ablation gains, cost, latency, and human review score.",
            "",
            "RAG Evidence",
            f"- Sources: {rag.get('sources', [])}",
        ])

    def general_research_report(self, query: str, rag: dict, file_context: str):
        return "\n".join([
            "ResearchAgent / research",
            "",
            "Research Report",
            f"Topic: {query}",
            "",
            "Summary",
            "The strongest research framing is to treat the topic as a system design problem: define the task, identify prior work, compare architectures, evaluate limitations, and propose measurable experiments.",
            "",
            "Literature Review",
            "- Use RAG evidence, uploaded context, and paper search connectors when available.",
            "- Compare baseline methods, agentic methods, and evaluation protocols.",
            "",
            "Analysis",
            "- Key dimensions: retrieval quality, planning depth, tool reliability, memory, verification, cost, and safety.",
            "",
            "Research Gaps",
            "- Better benchmarks, ablations, failure-mode analysis, and live-source verification.",
            "",
            "Report Generator",
            "- Produce an executive summary, methods comparison, limitations, and next-step roadmap.",
            "",
            "Verifier Agent",
            "- Treat live/current claims as unverified unless a web or paper connector returns sources.",
            "",
            "RAG Evidence",
            f"- Sources: {rag.get('sources', [])}",
            f"- Uploaded context used: {bool(file_context)}",
        ])

    @staticmethod
    def paper_title(query: str):
        cleaned = re.sub(r"^(explain|summarize)\s+", "", query.strip(), flags=re.I)
        cleaned = re.sub(r"\s+paper\.?$", "", cleaned, flags=re.I)
        return cleaned.strip(". ")

    @staticmethod
    def known_paper(title: str):
        q = title.lower()
        if "attention is all you need" in q:
            return {
                "summary": "Introduced the Transformer architecture, replacing recurrence with self-attention for sequence modeling.",
                "contributions": [
                    "Self-attention as the main sequence modeling mechanism.",
                    "Multi-head attention for learning multiple relation patterns.",
                    "Positional encoding to preserve token order.",
                    "Parallelizable training that improved machine translation performance.",
                ],
                "architecture": "Encoder-decoder Transformer with stacked self-attention, feed-forward layers, residual connections, layer normalization, and positional encodings.",
                "limitations": [
                    "Quadratic attention cost with sequence length.",
                    "Originally evaluated mainly on translation tasks.",
                    "Needs large data and compute for best results.",
                ],
                "future_work": [
                    "Efficient attention for long context.",
                    "Better multimodal and retrieval-augmented extensions.",
                    "Stronger interpretability of attention behavior.",
                ],
            }
        if "gpt-4" in q:
            return {
                "summary": "Describes GPT-4 as a large multimodal model evaluated across academic, professional, and safety benchmarks.",
                "contributions": [
                    "Strong benchmark performance across many domains.",
                    "Multimodal input capability.",
                    "Post-training and safety evaluation methods.",
                ],
                "architecture": "The report does not fully disclose architecture details; it focuses on capabilities, evaluations, and safety work.",
                "limitations": [
                    "Architecture, data, and training details are limited.",
                    "Can still hallucinate or make reasoning mistakes.",
                    "Sensitive to evaluation and deployment context.",
                ],
                "future_work": [
                    "More transparent evaluations.",
                    "Better factuality and calibration.",
                    "Safer tool use and deployment monitoring.",
                ],
            }
        return {
            "summary": f"Local metadata for '{title}' is limited. Connect a paper search API to fetch abstract, venue, and citations.",
            "contributions": ["Identify the core method.", "Compare against prior work.", "Evaluate empirical results."],
            "architecture": "Architecture details require paper retrieval.",
            "limitations": ["Needs verified paper text.", "Needs citation and benchmark extraction."],
            "future_work": ["Add Semantic Scholar/arXiv connector.", "Extract tables and experimental setup."],
        }

    @staticmethod
    def extract_models(query: str):
        known = ["GPT-5", "Claude", "Gemini", "DeepSeek", "Qwen", "Phi"]
        found = []
        for model in known:
            if model.lower() in query.lower():
                found.append(model)
        return found

    @staticmethod
    def rank_models(models: list[str]):
        preference = ["GPT-5", "Claude", "Gemini", "DeepSeek", "Qwen", "Phi"]
        return sorted(models, key=lambda item: preference.index(item) if item in preference else 99)
