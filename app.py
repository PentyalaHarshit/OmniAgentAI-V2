from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from llm_tree.free_llm_tree import FreeLLMTree
from agents.agent_router import AgentRouter
from tools.upload_manager import UploadManager
from tools.conversation_state import ConversationState
from tools.chat_memory import ChatMemory

app = FastAPI(title="OmniAgentAI v2 ChatGPT Style Upload Chat")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

llm_tree = FreeLLMTree()
router = AgentRouter()
upload_manager = UploadManager(upload_dir="uploads")
conversation_state = ConversationState()
chat_memory = ChatMemory()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return await upload_manager.save_and_index(file)


@app.get("/files")
def files():
    return upload_manager.list_files()


@app.get("/history/{session_id}")
def history(session_id: str):
    return {"messages": chat_memory.get(session_id)}


@app.post("/reset")
async def reset(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    conversation_state.clear(session_id)
    router.active_conversations.pop(session_id, None)
    chat_memory.clear(session_id)
    return {"message": "Conversation and state cleared"}


@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    query = data.get("query", "").strip()
    file_id = data.get("file_id", "")
    session_id = data.get("session_id", "default")

    if not query:
        return JSONResponse({"error": "Query is required"}, status_code=400)

    chat_memory.add(session_id, "user", query)

    uploaded_context = upload_manager.get_context(file_id, query) if file_id else ""

    if conversation_state.is_waiting(session_id):
        q = query.lower()

        GENERAL_STARTERS = [
            "what is", "who is", "who invented", "when", "where",
            "capital of", "population of", "gdp of",
            # coding / devops — should always break out of slot-filling
            "create", "write", "generate", "build", "implement", "develop",
            "deploy", "setup", "configure", "install", "kubernetes", "docker",
            "dockerfile", "k8s", "script", "code", "program", "function",
            "class", "algorithm", "debug", "fix", "refactor",
        ]

        # Also break out if the new query routes to a DIFFERENT agent than the active one
        prev_state = conversation_state.get(session_id)
        active_agent_name = prev_state.get("active_agent", "") if prev_state else ""
        active_flow = prev_state.get("flow") or "" if prev_state else ""
        is_healthcare_flow = active_flow.startswith("healthcare_")
        is_trip_flow = active_flow.startswith("trip_")
        is_movie_flow = active_flow.startswith("movie_")
        is_shopping_flow = active_flow.startswith("shopping_")
        new_route, _ = router.route(q)
        # Map route name to agent name for comparison
        ROUTE_TO_AGENT = {
            "coding": "CodingAgent", "deployment": "DeploymentAgent",
            "healthcare": "HealthcareAgent",
            "research": "ResearchAgent", "resume": "ResumeAgent",
            "shopping": "ShoppingAgent", "finance": "FinanceAgent", "travel": "TravelAgent",
            "fitness": "FitnessAgent", "recipe": "RecipeAgent", "local_discovery": "LocalDiscoveryAgent",
            "flight": "FlightAgent", "hotel": "HotelAgent",
            "movie": "MovieAgent", "restaurant": "RestaurantAgent",
            "train": "TrainAgent", "bus": "BusAgent", "cab": "CabAgent",
            "event": "EventAgent", "vacation_package": "VacationPackageAgent",
            "payment": "PaymentAgent", "coupon": "CouponAgent",
            "review": "ReviewAgent", "cancellation": "CancellationAgent",
            "notification": "NotificationAgent", "support": "SupportAgent",
            "general": "GeneralAgent", "calculator": "CalculatorAgent",
            "country": "CountryAgent", "code_review": "CodeReviewAgent",
            "debug": "DebugAgent", "test_case": "TestCaseAgent",
            "algorithm": "AlgorithmAgent", "system_design": "SystemDesignAgent",
            "ml": "MLAgent", "data_science": "DataScienceAgent",
            "rag": "RAGAgent", "mlops": "MLOpsAgent",
            "ai_architect": "AIArchitectAgent",
            "self_correction": "SelfCorrectionAgent", "loan": "LoanAgent",
        }
        new_agent_name = ROUTE_TO_AGENT.get(new_route, "")
        is_stateful_flow = is_healthcare_flow or is_trip_flow or is_movie_flow or is_shopping_flow
        stateful_breakout_routes = {
            "coding", "deployment", "healthcare", "research", "resume",
            "shopping", "travel", "flight", "hotel", "movie", "restaurant",
            "train", "bus", "cab", "event", "vacation_package", "payment",
            "finance",
            "code_review", "debug", "test_case", "algorithm",
            "system_design", "ml", "data_science", "rag", "mlops",
            "ai_architect", "self_correction", "loan", "country",
            "coupon", "review", "cancellation", "notification", "support",
            "calculator",
        }
        is_new_domain = bool(
            active_agent_name
            and new_agent_name
            and new_agent_name != active_agent_name
            and (not is_stateful_flow or new_route in stateful_breakout_routes)
        )

        if (any(s in q for s in GENERAL_STARTERS) and not is_stateful_flow) or is_new_domain:
            # New question from a different domain — clear slot-filling state and fall through
            conversation_state.clear(session_id)
        else:
            # Continue the existing slot-filling conversation
            if is_healthcare_flow or is_trip_flow or is_movie_flow or is_shopping_flow:
                prev_state = conversation_state.get(session_id)
                active_agent = prev_state.get("active_agent")
                fields = {}
            else:
                prev_state = conversation_state.update_from_user_reply(session_id, query)
                active_agent = prev_state.get("active_agent")
                fields = prev_state.get("fields", {})

            agent_result = router.run_with_agent_name(
                active_agent,
                query,
                prefilled_fields=fields,
                session_id=session_id
            )

            chat_memory.add(session_id, "assistant", agent_result["answer"])

            return {
                "query": query,
                "session_id": session_id,
                "file_id": file_id,
                "file_context_used": bool(uploaded_context),
                "llm_tree": {
                    "root": "ConversationState",
                    "best_model": "stateful-followup",
                    "best_ollama_model": "not-needed",
                    "best_score": 100,
                    "scores": [],
                    "best_output": "Continuing previous agent slot-filling conversation."
                },
                "agent_result": agent_result,
                "final_answer": agent_result["answer"],
                "messages": chat_memory.get(session_id)
            }

    llm_input = query
    if uploaded_context:
        llm_input += "\n\n[Uploaded File Context]\n" + uploaded_context

    llm_result = llm_tree.run(llm_input)

    enriched_query = query + "\n\n[Free LLM Tree Guidance]\n" + llm_result["best_output"]
    if uploaded_context:
        enriched_query += "\n\n[Uploaded File Context]\n" + uploaded_context

    agent_result = router.run(enriched_query, session_id=session_id, original_query=query)
    chat_memory.add(session_id, "assistant", agent_result["answer"])

    return {
        "query": query,
        "session_id": session_id,
        "file_id": file_id,
        "file_context_used": bool(uploaded_context),
        "llm_tree": llm_result,
        "agent_result": agent_result,
        "final_answer": agent_result["answer"],
        "messages": chat_memory.get(session_id)
    }


@app.get("/health")
def health():
    return {"status": "ok", "app": "OmniAgentAI v2 ChatGPT Style Upload Chat"}
