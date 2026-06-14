import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "OmniAgentAI v9 All Agents RAG Healthcare"

USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen2.5-coder:7b")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-coder:6.7b")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama3.2:3b")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral:7b")
PHI_MODEL = os.getenv("PHI_MODEL", "phi3:mini")

CPP_COMPILER = os.getenv("CPP_COMPILER", "g++")
PYTHON_BIN = os.getenv("PYTHON_BIN", "python")
MAX_SELF_CORRECT_ROUNDS = int(os.getenv("MAX_SELF_CORRECT_ROUNDS", "2"))
KNOWLEDGE_DIR = "knowledge"

# Real/live API providers
HOTEL_PROVIDER = os.getenv("HOTEL_PROVIDER", "demo").lower()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")


LLM_TREE_MAX_WORKERS = int(os.getenv("LLM_TREE_MAX_WORKERS", "5"))
LLM_TREE_MODEL_TIMEOUT = int(os.getenv("LLM_TREE_MODEL_TIMEOUT", "90"))

# Inference backend:
# ollama = local Ollama API
# vllm = vLLM OpenAI-compatible API
# hybrid = run Ollama + vLLM nodes together
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").lower()

# vLLM OpenAI-compatible server URLs
VLLM_QWEN_URL = os.getenv("VLLM_QWEN_URL", "http://localhost:8001/v1")
VLLM_DEEPSEEK_URL = os.getenv("VLLM_DEEPSEEK_URL", "http://localhost:8002/v1")
VLLM_LLAMA_URL = os.getenv("VLLM_LLAMA_URL", "http://localhost:8003/v1")
VLLM_MISTRAL_URL = os.getenv("VLLM_MISTRAL_URL", "http://localhost:8004/v1")
VLLM_PHI_URL = os.getenv("VLLM_PHI_URL", "http://localhost:8005/v1")

# vLLM model names must match the served model name.
VLLM_QWEN_MODEL = os.getenv("VLLM_QWEN_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
VLLM_DEEPSEEK_MODEL = os.getenv("VLLM_DEEPSEEK_MODEL", "deepseek-ai/deepseek-coder-6.7b-instruct")
VLLM_LLAMA_MODEL = os.getenv("VLLM_LLAMA_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
VLLM_MISTRAL_MODEL = os.getenv("VLLM_MISTRAL_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
VLLM_PHI_MODEL = os.getenv("VLLM_PHI_MODEL", "microsoft/Phi-3-mini-4k-instruct")

VLLM_API_KEY = os.getenv("VLLM_API_KEY", "EMPTY")
VLLM_TEMPERATURE = float(os.getenv("VLLM_TEMPERATURE", "0.2"))
VLLM_MAX_TOKENS = int(os.getenv("VLLM_MAX_TOKENS", "512"))
