"""
Tool implementations for the Qwen Code Agent
"""
import os
import subprocess
import glob as glob_module
import re
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class FileTools:
    """File operation tools"""

    @staticmethod
    def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Read contents of a file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File '{file_path}' does not exist"

            if not path.is_file():
                return f"Error: '{file_path}' is not a file"

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Handle line ranges
            if start_line is not None or end_line is not None:
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else len(lines)
                lines = lines[start:end]

            # Add line numbers
            numbered_lines = []
            start_num = start_line if start_line else 1
            for i, line in enumerate(lines, start=start_num):
                numbered_lines.append(f"{i:4d} | {line.rstrip()}")

            return "\n".join(numbered_lines)

        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def write_file(file_path: str, content: str) -> str:
        """Write or create a new file"""
        try:
            path = Path(file_path)

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists
            existed = path.exists()

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            action = "Updated" if existed else "Created"
            return f"{action} file '{file_path}' ({len(content)} bytes)"

        except Exception as e:
            return f"Error writing file: {str(e)}"

    @staticmethod
    def edit_file(file_path: str, old_text: str, new_text: str) -> str:
        """Edit existing file by replacing text"""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File '{file_path}' does not exist. Use write_file to create it."

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if old_text exists
            if old_text not in content:
                return f"Error: Could not find the text to replace in '{file_path}'. Make sure the text matches exactly."

            # Count occurrences
            count = content.count(old_text)
            if count > 1:
                return f"Error: Found {count} occurrences of the text. Please provide more context to make it unique."

            # Perform replacement
            new_content = content.replace(old_text, new_text)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"Successfully edited '{file_path}' (replaced {len(old_text)} chars with {len(new_text)} chars)"

        except Exception as e:
            return f"Error editing file: {str(e)}"


class ShellTools:
    """Shell command execution tools"""

    @staticmethod
    def run_command(command: str, description: str = "", timeout: int = 30) -> str:
        """Execute a shell command"""
        try:
            console.print(f"[yellow]Running: {command}[/yellow]")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )

            output = []
            if description:
                output.append(f"Description: {description}")

            output.append(f"Command: {command}")
            output.append(f"Exit code: {result.returncode}")

            if result.stdout:
                output.append(f"\nStdout:\n{result.stdout}")

            if result.stderr:
                output.append(f"\nStderr:\n{result.stderr}")

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error running command: {str(e)}"


class SearchTools:
    """Code search tools"""

    @staticmethod
    def search_code(pattern: str, file_pattern: str = "*", case_sensitive: bool = True,
                   max_results: int = 50) -> str:
        """Search for code patterns using grep-like functionality"""
        try:
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE

            # Compile regex pattern
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return f"Error: Invalid regex pattern: {str(e)}"

            # Find files matching file_pattern
            files = glob_module.glob(f"**/{file_pattern}", recursive=True)

            count = 0
            for file_path in files:
                path = Path(file_path)

                # Skip directories and binary files
                if not path.is_file():
                    continue

                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                results.append(f"{file_path}:{line_num}: {line.rstrip()}")
                                count += 1

                                if count >= max_results:
                                    results.append(f"\n... (stopped at {max_results} results)")
                                    return "\n".join(results)
                except Exception:
                    # Skip files we can't read
                    continue

            if not results:
                return f"No matches found for pattern '{pattern}'"

            return "\n".join(results)

        except Exception as e:
            return f"Error searching code: {str(e)}"

    @staticmethod
    def find_files(pattern: str, max_results: int = 100) -> str:
        """Find files matching glob pattern"""
        try:
            files = glob_module.glob(f"**/{pattern}", recursive=True)

            # Filter to only files (not directories)
            files = [f for f in files if Path(f).is_file()]

            if not files:
                return f"No files found matching pattern '{pattern}'"

            # Limit results
            if len(files) > max_results:
                files = files[:max_results]
                truncated = f"\n... (showing first {max_results} of {len(files)} files)"
            else:
                truncated = ""

            return "\n".join(files) + truncated

        except Exception as e:
            return f"Error finding files: {str(e)}"


class RAGTools:
    """RAG and codebase indexing tools"""

    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8000,
                 collection_name: str = "codebase"):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.collection_name = collection_name
        self.client = None
        self.collection = None

    def initialize(self):
        """Initialize ChromaDB connection"""
        try:
            import chromadb

            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )

            return True
        except Exception as e:
            console.print(f"[yellow]Warning: Could not connect to ChromaDB: {str(e)}[/yellow]")
            console.print("[yellow]RAG features will be disabled[/yellow]")
            return False

    def rag_query(self, query: str, n_results: int = 5) -> str:
        """Query the codebase using RAG"""
        if not self.collection:
            return "Error: RAG not initialized. Make sure ChromaDB is running and accessible."

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            if not results['documents'] or not results['documents'][0]:
                return f"No relevant code found for query: '{query}'"

            output = [f"Found {len(results['documents'][0])} relevant code snippets:\n"]

            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
                output.append(f"\n--- Result {i} (distance: {distance:.3f}) ---")

                if metadata:
                    if 'file' in metadata:
                        output.append(f"File: {metadata['file']}")
                    if 'line' in metadata:
                        output.append(f"Line: {metadata['line']}")

                output.append(f"Content:\n{doc}\n")

            return "\n".join(output)

        except Exception as e:
            return f"Error querying RAG: {str(e)}"


def register_tools(agent, chroma_host: str = "localhost", chroma_port: int = 8000,
                   collection_name: str = "codebase", auto_index: bool = True):
    """Register all tools with the agent"""

    # File tools
    agent.add_tool("read_file", FileTools.read_file)
    agent.add_tool("write_file", FileTools.write_file)
    agent.add_tool("edit_file", FileTools.edit_file)

    # Shell tools
    agent.add_tool("run_command", ShellTools.run_command)

    # Search tools
    agent.add_tool("search_code", SearchTools.search_code)
    agent.add_tool("find_files", SearchTools.find_files)

    # RAG tools
    rag_tools = RAGTools(chroma_host, chroma_port, collection_name)
    if rag_tools.initialize():
        agent.add_tool("rag_query", rag_tools.rag_query)
        console.print("[green]RAG tools initialized successfully[/green]")

        # Auto-index current directory if enabled
        if auto_index:
            from indexer import auto_index_current_directory
            auto_index_current_directory(rag_tools.client, rag_tools.collection)
    else:
        console.print("[yellow]RAG tools not available[/yellow]")
