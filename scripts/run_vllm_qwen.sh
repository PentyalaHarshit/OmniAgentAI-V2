#!/bin/bash
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-Coder-7B-Instruct --host 0.0.0.0 --port 8001
