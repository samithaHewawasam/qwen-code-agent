"""
Qwen Code Agent - A Claude Code-like agent powered by qwen2.5-coder:7b
"""
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


@dataclass
class Message:
    """Represents a conversation message"""
    role: str  # 'user' or 'assistant'
    content: str


@dataclass
class ToolCall:
    """Represents a parsed tool call from the model"""
    tool_name: str
    parameters: Dict[str, Any]
    raw_text: str


class QwenCodeAgent:
    """Main agent class that manages conversation and tool execution"""

    def __init__(self, model: str = "qwen2.5-coder:7b", ollama_host: str = "http://localhost:11434"):
        self.model = model
        self.ollama_host = ollama_host
        self.conversation_history: List[Message] = []
        self.tools = {}  # Will be populated by tool registry

        # System prompt that teaches Qwen how to use tools
        self.system_prompt = """You are an advanced coding assistant with access to various tools to help with software development tasks.

When you need to use a tool, output it in this EXACT format:
<tool_call>
<tool_name>TOOL_NAME</tool_name>
<parameters>
{
  "param1": "value1",
  "param2": "value2"
}
</parameters>
</tool_call>

Available tools:
1. read_file - Read contents of a file
   Parameters: {"file_path": "path/to/file", "start_line": 1, "end_line": 100}

2. write_file - Write or create a new file
   Parameters: {"file_path": "path/to/file", "content": "file contents"}

3. edit_file - Edit existing file by replacing text
   Parameters: {"file_path": "path/to/file", "old_text": "text to replace", "new_text": "replacement text"}

4. run_command - Execute shell command
   Parameters: {"command": "ls -la", "description": "what this command does"}

5. search_code - Search for code patterns using grep
   Parameters: {"pattern": "regex pattern", "file_pattern": "*.py", "case_sensitive": false}

6. find_files - Find files matching glob pattern
   Parameters: {"pattern": "**/*.py"}

7. rag_query - Query the codebase using RAG for context
   Parameters: {"query": "how does authentication work?", "n_results": 5}

IMPORTANT RULES:
- Only output ONE tool call at a time
- Wait for the tool result before deciding next action
- After receiving tool results, analyze them and provide insights to the user
- Use read_file before editing to understand the current content
- For complex tasks, break them into steps
- Always explain what you're doing and why

When you want to respond to the user without using a tool, just write normally. Only use the <tool_call> format when you need to execute a tool."""

    def add_tool(self, name: str, handler):
        """Register a tool handler"""
        self.tools[name] = handler

    def parse_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse tool calls from model response"""
        tool_calls = []

        # Find all <tool_call>...</tool_call> blocks
        pattern = r'<tool_call>(.*?)</tool_call>'
        matches = re.findall(pattern, response, re.DOTALL)

        for match in matches:
            # Extract tool name
            tool_name_match = re.search(r'<tool_name>(.*?)</tool_name>', match, re.DOTALL)
            if not tool_name_match:
                continue
            tool_name = tool_name_match.group(1).strip()

            # Extract parameters
            params_match = re.search(r'<parameters>(.*?)</parameters>', match, re.DOTALL)
            if not params_match:
                continue

            try:
                parameters = json.loads(params_match.group(1).strip())
            except json.JSONDecodeError:
                console.print(f"[red]Failed to parse parameters for tool {tool_name}[/red]")
                continue

            tool_calls.append(ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                raw_text=match
            ))

        return tool_calls

    def execute_tool(self, tool_call: ToolCall) -> str:
        """Execute a tool and return the result"""
        if tool_call.tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_call.tool_name}'"

        try:
            handler = self.tools[tool_call.tool_name]
            result = handler(**tool_call.parameters)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_call.tool_name}: {str(e)}"

    def generate_response(self, user_message: str) -> str:
        """Generate a response from the model"""
        # Add user message to history
        self.conversation_history.append(Message(role="user", content=user_message))

        # Prepare messages for Ollama
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ])

        # Call Ollama
        response = ollama.chat(
            model=self.model,
            messages=messages
        )

        assistant_response = response['message']['content']

        # Add to history
        self.conversation_history.append(Message(role="assistant", content=assistant_response))

        return assistant_response

    def run_turn(self, user_message: str) -> str:
        """Run a single conversation turn, handling tool calls"""
        response = self.generate_response(user_message)

        # Check for tool calls
        tool_calls = self.parse_tool_calls(response)

        if not tool_calls:
            # No tool calls, return response as-is
            return response

        # Execute tool calls and collect results
        tool_results = []
        for tool_call in tool_calls:
            console.print(f"\n[cyan]Executing: {tool_call.tool_name}[/cyan]")
            console.print(f"[dim]Parameters: {json.dumps(tool_call.parameters, indent=2)}[/dim]")

            result = self.execute_tool(tool_call)
            tool_results.append(f"Tool: {tool_call.tool_name}\nResult:\n{result}")

            console.print(Panel(result[:500] + ("..." if len(result) > 500 else ""),
                              title=f"Tool Result: {tool_call.tool_name}",
                              border_style="green"))

        # Send tool results back to model for analysis
        tool_results_message = "\n\n".join(tool_results)
        follow_up = self.generate_response(f"<tool_results>\n{tool_results_message}\n</tool_results>")

        return follow_up

    def chat(self):
        """Start an interactive chat session"""
        console.print(Panel.fit(
            "[bold green]Qwen Code Agent[/bold green]\n"
            "Powered by qwen2.5-coder:7b\n\n"
            "Type 'exit' or 'quit' to end the session",
            border_style="blue"
        ))

        while True:
            try:
                # Get user input
                user_input = console.input("\n[bold blue]You:[/bold blue] ")

                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if not user_input.strip():
                    continue

                # Generate and display response
                response = self.run_turn(user_input)

                # Display the response
                console.print(f"\n[bold green]Assistant:[/bold green]")
                console.print(Markdown(response))

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                continue
            except Exception as e:
                console.print(f"\n[red]Error: {str(e)}[/red]")
