# Qwen Code Agent - Quick Start Guide

## 1. Setup (5 minutes)

### Install Ollama and Pull Qwen Model

```bash
# Install Ollama from https://ollama.ai
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the qwen2.5-coder:7b model (this may take a few minutes)
ollama pull qwen2.5-coder:7b

# Verify it's running
ollama list
```

### Install Python Dependencies

```bash
cd qwen-code-agent
pip install -r requirements.txt
```

### Create Environment File

```bash
cp .env.example .env
```

Default settings work fine - no need to edit unless you want to customize.

## 2. Test the Agent

### Check System Status

```bash
python main.py info
```

You should see:
- Ollama: Connected
- Available models: 1 or more
- ChromaDB: Not connected (this is OK if you don't need RAG)

### Run a Simple Command

```bash
python main.py run "List all Python files in the current directory"
```

The agent will use the `find_files` tool to search for Python files.

### Start Interactive Chat

```bash
python main.py chat
```

Try these commands:
1. `Find all JavaScript files`
2. `Read the README.md file`
3. `Search for the word 'function' in Python files`

## 3. Common Use Cases

### Code Review

```
You: Read the file src/main.py and suggest improvements
```

The agent will:
1. Use `read_file` tool to read the file
2. Analyze the code
3. Provide suggestions

### Creating New Files

```
You: Create a new Python file called hello.py with a simple hello world function
```

The agent will:
1. Use `write_file` tool
2. Create the file with proper content
3. Confirm creation

### Editing Files

```
You: Read utils.py and fix any syntax errors
```

The agent will:
1. Use `read_file` to analyze
2. Use `edit_file` to make corrections
3. Explain the changes

### Running Tests

```
You: Run the tests using npm test
```

The agent will:
1. Use `run_command` tool
2. Execute the command
3. Analyze the results

## 4. Enable RAG (Optional)

If you want semantic codebase search:

### Start ChromaDB

```bash
docker run -p 8000:8000 chromadb/chroma
```

### Index Your Codebase

Use your existing `ollama-rag` project to index files into ChromaDB.

### Test RAG

```bash
python main.py chat
```

```
You: Using RAG, find information about authentication in the codebase
```

## 5. Troubleshooting

### "Connection refused" error

- Make sure Ollama is running: `ollama serve`
- Check with: `ollama list`

### Model not found

- Pull the model: `ollama pull qwen2.5-coder:7b`

### Slow responses

- The 7B model is designed for consumer hardware
- First response may be slower while model loads
- Consider using a smaller model or upgrading hardware

### RAG not working

- ChromaDB is optional
- Check if ChromaDB is running: `curl http://localhost:8000/api/v1/heartbeat`
- The agent works fine without RAG for file operations and code search

## 6. Tips for Best Results

1. **Be Specific**: Instead of "fix my code", say "read app.py and fix the syntax error on line 42"

2. **One Task at a Time**: Qwen works best with focused tasks

3. **Use Tools Explicitly**: You can suggest which tool to use: "Use grep to search for..."

4. **Provide Context**: "Read the README first, then..." gives the agent context

5. **Iterate**: If the first attempt isn't perfect, provide feedback

## Next Steps

- Read [EXAMPLES.md](EXAMPLES.md) for more usage examples
- Explore the code in `agent.py` and `tools.py`
- Customize the system prompt in `agent.py` for your workflow
- Add custom tools in `tools.py`
