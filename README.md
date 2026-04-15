# Qwen Code Agent

A Claude Code-like AI coding assistant powered by **qwen2.5-coder:7b** running locally via Ollama. This agent provides interactive coding assistance with file operations, shell commands, code search, and RAG-based codebase understanding.

## Features

- **Interactive Chat Interface**: Chat with the AI agent about your code
- **File Operations**: Read, write, and edit files
- **Shell Command Execution**: Run git, npm, build commands, etc.
- **Code Search**: Find files and search code patterns
- **RAG Integration**: Query your codebase using semantic search with ChromaDB
- **Local & Private**: Runs entirely on your machine using Ollama

## Why Qwen Instead of Claude?

While Claude Code uses Anthropic's Claude models with native function calling, this project demonstrates how to build a similar agentic coding assistant using open-source models like Qwen that don't have native tool calling support.

**Key Differences:**
- Uses **prompt-based tool parsing** instead of native function calling
- Qwen is optimized for code generation and understanding
- Runs completely locally with no API costs
- Customizable and extensible

## Prerequisites

1. **Ollama** installed and running
   ```bash
   # Install Ollama from https://ollama.ai

   # Pull the qwen2.5-coder model
   ollama pull qwen2.5-coder:7b
   ```

2. **ChromaDB** (optional, for RAG features)
   ```bash
   # Run ChromaDB server
   docker run -p 8000:8000 chromadb/chroma

   # Or install and run locally
   pip install chromadb
   chroma run --host localhost --port 8000
   ```

3. **Python 3.8+**

## Installation

1. Navigate to the project directory:
   ```bash
   cd qwen-code-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Make the main script executable:
   ```bash
   chmod +x main.py
   ```

## Usage

### Interactive Chat Mode

Start an interactive session:

```bash
python main.py chat
```

Example conversation:

```
You: Read the package.json file