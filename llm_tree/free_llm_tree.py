from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from config import (
    LLM_BACKEND,
    QWEN_MODEL,
    DEEPSEEK_MODEL,
    LLAMA_MODEL,
    MISTRAL_MODEL,
    PHI_MODEL,
    VLLM_QWEN_URL,
    VLLM_DEEPSEEK_URL,
    VLLM_LLAMA_URL,
    VLLM_MISTRAL_URL,
    VLLM_PHI_URL,
    VLLM_QWEN_MODEL,
    VLLM_DEEPSEEK_MODEL,
    VLLM_LLAMA_MODEL,
    VLLM_MISTRAL_MODEL,
    VLLM_PHI_MODEL,
    LLM_TREE_MAX_WORKERS,
)
from llm_tree.ollama_client import OllamaClient
from llm_tree.vllm_client import VLLMClient
from llm_tree.judge_agent import JudgeAgent


class FreeLLMTree:
    """
    Parallel LLM Tree with optional vLLM inference.

    Backends:
    - LLM_BACKEND=ollama
    - LLM_BACKEND=vllm
    - LLM_BACKEND=hybrid

    All selected model nodes run concurrently using ThreadPoolExecutor.
    """

    def __init__(self):
        self.judge = JudgeAgent()
        self.nodes = self._build_nodes()

    def _build_nodes(self):
        ollama_nodes = [
            ("Qwen-Ollama", "ollama", OllamaClient(QWEN_MODEL)),
            ("DeepSeek-Ollama", "ollama", OllamaClient(DEEPSEEK_MODEL)),
            ("Llama-Ollama", "ollama", OllamaClient(LLAMA_MODEL)),
            ("Mistral-Ollama", "ollama", OllamaClient(MISTRAL_MODEL)),
            ("Phi-Ollama", "ollama", OllamaClient(PHI_MODEL)),
        ]

        vllm_nodes = [
            ("Qwen-vLLM", "vllm", VLLMClient(VLLM_QWEN_MODEL, VLLM_QWEN_URL, "Qwen-vLLM")),
            ("DeepSeek-vLLM", "vllm", VLLMClient(VLLM_DEEPSEEK_MODEL, VLLM_DEEPSEEK_URL, "DeepSeek-vLLM")),
            ("Llama-vLLM", "vllm", VLLMClient(VLLM_LLAMA_MODEL, VLLM_LLAMA_URL, "Llama-vLLM")),
            ("Mistral-vLLM", "vllm", VLLMClient(VLLM_MISTRAL_MODEL, VLLM_MISTRAL_URL, "Mistral-vLLM")),
            ("Phi-vLLM", "vllm", VLLMClient(VLLM_PHI_MODEL, VLLM_PHI_URL, "Phi-vLLM")),
        ]

        if LLM_BACKEND == "vllm":
            return vllm_nodes

        if LLM_BACKEND == "hybrid":
            return ollama_nodes + vllm_nodes

        return ollama_nodes

    def _run_single_model(self, name: str, backend: str, client, query: str):
        start = time.time()

        try:
            output = client.generate(query)
            error = None
        except Exception as e:
            output = f"{name} failed. Error: {e}"
            error = str(e)

        latency = round(time.time() - start, 3)

        model_id = getattr(client, "model_name", name)

        return {
            "model": name,
            "backend": backend,
            "model_id": model_id,
            "ollama_model": model_id if backend == "ollama" else "",
            "vllm_model": model_id if backend == "vllm" else "",
            "output": output,
            "latency_seconds": latency,
            "error": error,
        }

    def run(self, query: str):
        start_all = time.time()
        raw_results = []

        max_workers = min(LLM_TREE_MAX_WORKERS, len(self.nodes))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._run_single_model, name, backend, client, query)
                for name, backend, client in self.nodes
            ]

            for future in as_completed(futures):
                raw_results.append(future.result())

        model_order = {name: i for i, (name, _, _) in enumerate(self.nodes)}
        raw_results.sort(key=lambda x: model_order.get(x["model"], 999))

        outputs = [item["output"] for item in raw_results]

        scored = []
        for item in raw_results:
            scored.append({
                "model": item["model"],
                "backend": item["backend"],
                "model_id": item["model_id"],
                "ollama_model": item["ollama_model"],
                "vllm_model": item["vllm_model"],
                "output": item["output"],
                "latency_seconds": item["latency_seconds"],
                "error": item["error"],
                "score": self.judge.score(query, item["output"], outputs),
            })

        scored.sort(key=lambda x: x["score"]["final_score"], reverse=True)
        best = scored[0]

        total_latency = round(time.time() - start_all, 3)

        return {
            "root": "ParallelVLLMFreeLLMTree",
            "parallel": True,
            "backend": LLM_BACKEND,
            "max_workers": max_workers,
            "total_latency_seconds": total_latency,
            "models_tested": [x["model"] for x in scored],
            "scores": scored,
            "best_model": best["model"],
            "best_backend": best["backend"],
            "best_model_id": best["model_id"],
            "best_ollama_model": best.get("ollama_model", ""),
            "best_vllm_model": best.get("vllm_model", ""),
            "best_score": best["score"]["final_score"],
            "best_output": best["output"],
            "note": "Parallel LLM tree used with backend: " + LLM_BACKEND,
        }
