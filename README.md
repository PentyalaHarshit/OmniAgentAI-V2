# OmniAgentAI v2 — ChatGPT-Style Upload + Human Conversation

This version fixes the upload experience and makes the UI work like a ChatGPT-style chatbot.

## New Features

- Chat thread with user and assistant bubbles
- File upload button inside sidebar and composer
- Uploaded files appear in dropdown
- Attached-file pill shown above message box
- Session chat memory
- Follow-up question flow:
  - User: `I need trip`
  - AI: `Which place do you want to travel to?`
  - User: `Las Vegas`
  - AI: asks next missing field
- Reset chat state button
- RAG still works with uploaded TXT/PDF/DOCX files

## Real APIs

OmniAgentAI now has a live API layer for current-data questions:

- Hotel API: Google Hotels via SerpApi (`HOTEL_PROVIDER=serpapi`, `SERPAPI_API_KEY=...`)
- Weather API: Open-Meteo geocoding + forecast, no key required
- News API: Google News RSS, no key required
- Sports API: TheSportsDB public API, no key required
- Search API: SerpApi Google Search when `SERPAPI_API_KEY` is set, DuckDuckGo Instant Answer fallback otherwise

Example `.env`:

```env
HOTEL_PROVIDER=serpapi
SERPAPI_API_KEY=your_serpapi_key
NEWSAPI_KEY=optional_future_newsapi_key
```

Safety remains unchanged: real APIs can retrieve options and live data, but OmniAgentAI must not buy, pay, book, cancel, or diagnose without explicit user confirmation.

## Run

```bash
cd omniagentai_v11_chatgpt_style_upload_chat

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env

uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## How to Use Upload

1. Click 📎 Upload file.
2. Select TXT, PDF, or DOCX.
3. The file appears in dropdown.
4. Ask: `summarize this file`, `improve my resume`, or `find research gaps`.

## Natural Conversation Examples

```text
I need trip
```

```text
I want hotel
```

```text
I need doctor appointment
```

```text
I want movie tickets
```

The chatbot asks missing details one by one like a human assistant.


## v12 Update: Multithreaded LLM Tree

The LLM tree now runs all free Ollama models at the same time using Python multithreading.

```text
User Query
   ↓
ThreadPoolExecutor
   ├── Qwen thread
   ├── DeepSeek thread
   ├── Llama thread
   ├── Mistral thread
   └── Phi thread
        ↓
Judge Agent scores all outputs
        ↓
Best model guidance selected
```

This reduces latency because it waits for the slowest model instead of running every model one by one.

### Settings

In `.env`:

```env
LLM_TREE_MAX_WORKERS=5
LLM_TREE_MODEL_TIMEOUT=90
```

### Important

Running 5 local models at the same time needs more CPU/RAM/GPU memory. If your laptop is slow, use:

```env
LLM_TREE_MAX_WORKERS=2
```


## v2 Update: vLLM + Parallel Inference

This version supports both:

```text
Ollama parallel inference
vLLM parallel inference
Hybrid Ollama + vLLM parallel inference
```

### Backend modes

In `.env`:

```env
LLM_BACKEND=ollama
```

or:

```env
LLM_BACKEND=vllm
```

or:

```env
LLM_BACKEND=hybrid
```

### vLLM architecture

```text
User Query
   ↓
ThreadPoolExecutor
   ├── Qwen vLLM server     localhost:8001
   ├── DeepSeek vLLM server localhost:8002
   ├── Llama vLLM server    localhost:8003
   ├── Mistral vLLM server  localhost:8004
   └── Phi vLLM server      localhost:8005
        ↓
Judge Agent
        ↓
Best model guidance
        ↓
Agent Router
```

### Install vLLM

vLLM works best on Linux/WSL2 with NVIDIA GPU.

```bash
pip install vllm
```

### Start vLLM servers

Example Qwen:

```bash
python -m vllm.entrypoints.openai.api_server   --model Qwen/Qwen2.5-Coder-7B-Instruct   --host 0.0.0.0   --port 8001
```

Then set:

```env
LLM_BACKEND=vllm
VLLM_QWEN_URL=http://localhost:8001/v1
```

### Important

Running many vLLM servers needs strong GPU memory. If your computer is small, run only one or two vLLM servers and set:

```env
LLM_TREE_MAX_WORKERS=2
```

For CPU/laptop, Ollama backend is easier.
