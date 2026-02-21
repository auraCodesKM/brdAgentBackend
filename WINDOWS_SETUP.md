# Windows Deployment Guide

## Why Ollama instead of vLLM?
vLLM requires Linux. Our server runs Windows with an RTX 4090.
Ollama provides identical OpenAI-compatible API, full CUDA GPU
acceleration, and native Windows support. Output quality is identical —
same Qwen 32B weights, same 24GB VRAM usage.

## Model Storage — Important
Ollama manages Qwen 32B in its own cache: C:\Users\USERNAME\.ollama\models
HuggingFace manages all other models: C:\Users\USERNAME\.cache\huggingface
These are completely separate. Do not confuse them.
If you previously downloaded Qwen 32B via huggingface-cli, delete it —
it is wasted space now that Ollama manages its own copy.

## Setup Steps
1. Download Ollama: ollama.com/download/windows
2. Install and restart if prompted
3. Open PowerShell: `ollama pull qwen2.5:32b`
4. Verify GPU: `ollama run qwen2.5:32b "hello"`
   Task Manager → Performance → GPU should spike to 80-100%
5. Start FastAPI normally

## Models Summary
| Model | Managed By | Location |
|---|---|---|
| Qwen 2.5 32B | Ollama | C:\Users\USERNAME\.ollama\models |
| Qwen 2.5 7B | HuggingFace | HF_HOME\hub |
| BGE-M3 | HuggingFace | HF_HOME\hub |
| BGE-reranker-large | HuggingFace | HF_HOME\hub |
| Whisper large-v3 | HuggingFace | HF_HOME\hub |
