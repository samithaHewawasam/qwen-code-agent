"""
Automatic code indexing for the current directory
"""
import os
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class CodeIndexer:
    """Indexes code files in the current directory for RAG"""

    # File extensions to index
    CODE_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
        '.m', '.sh', '.bash', '.zsh', '.fish', '.sql', '.html', '.css', '.scss',
        '.sass', '.vue', '.svelte', '.md', '.json', '.yaml', '.yml', '.toml', '.xml'
    }

    # Directories to skip
    SKIP_DIRS = {
        '.git', '.svn', '.hg', 'node_modules', '__pycache__', '.venv', 'venv',
        'env', '.env', 'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj',
        '.idea', '.vscode', '.pytest_cache', '.mypy_cache', '.tox', 'coverage'
    }

    def __init__(self, chroma_client=None, collection=None):
        self.client = chroma_client
        self.collection = collection

    def should_index_file(self, file_path: Path) -> bool:
        """Check if a file should be indexed"""
        # Check extension
        if file_path.suffix.lower() not in self.CODE_EXTENSIONS:
            return False

        # Check if in skip directory
        for parent in file_path.parents:
            if parent.name in self.SKIP_DIRS:
                return False

        # Check file size (skip files > 1MB)
        try:
            if file_path.stat().st_size > 1_000_000:
                return False
        except:
            return False

        return True

    def find_code_files(self, root_dir: str = ".") -> List[Path]:
        """Find all code files in directory"""
        root = Path(root_dir).resolve()
        code_files = []

        for file_path in root.rglob("*"):
            if file_path.is_file() and self.should_index_file(file_path):
                code_files.append(file_path)

        return code_files

    def chunk_file(self, file_path: Path, chunk_size: int = 50) -> List[dict]:
        """Split file into chunks for indexing"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            chunks = []
            for i in range(0, len(lines), chunk_size):
                chunk_lines = lines[i:i + chunk_size]
                chunk_text = ''.join(chunk_lines)

                chunks.append({
                    'text': chunk_text,
                    'file': str(file_path.relative_to(Path.cwd())),
                    'start_line': i + 1,
                    'end_line': min(i + chunk_size, len(lines))
                })

            return chunks
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
            return []

    def index_directory(self, directory: str = ".", force: bool = False) -> Optional[dict]:
        """Index all code files in directory"""
        if not self.collection:
            console.print("[yellow]ChromaDB not available - skipping indexing[/yellow]")
            return None

        console.print(f"\n[cyan]Indexing code files in {directory}...[/cyan]")

        # Find files
        code_files = self.find_code_files(directory)

        if not code_files:
            console.print("[yellow]No code files found to index[/yellow]")
            return None

        console.print(f"[cyan]Found {len(code_files)} code files[/cyan]")

        # Index files with progress bar
        total_chunks = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Indexing files...", total=len(code_files))

            for file_path in code_files:
                # Chunk file
                chunks = self.chunk_file(file_path, chunk_size=50)

                if chunks:
                    # Add to collection
                    try:
                        self.collection.add(
                            documents=[chunk['text'] for chunk in chunks],
                            metadatas=[{
                                'file': chunk['file'],
                                'start_line': chunk['start_line'],
                                'end_line': chunk['end_line']
                            } for chunk in chunks],
                            ids=[f"{chunk['file']}:{chunk['start_line']}" for chunk in chunks]
                        )
                        total_chunks += len(chunks)
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not index {file_path}: {e}[/yellow]")

                progress.advance(task)

        result = {
            'files_indexed': len(code_files),
            'chunks_created': total_chunks
        }

        console.print(f"[green]Successfully indexed {len(code_files)} files ({total_chunks} chunks)[/green]")
        return result


def auto_index_current_directory(chroma_client, collection) -> bool:
    """Auto-index current directory if not already indexed"""
    try:
        # Check if collection already has documents
        count = collection.count()

        if count > 0:
            console.print(f"[cyan]Codebase already indexed ({count} chunks)[/cyan]")
            return True

        # Index current directory
        indexer = CodeIndexer(chroma_client, collection)
        result = indexer.index_directory(".")

        return result is not None
    except Exception as e:
        console.print(f"[yellow]Warning: Auto-indexing failed: {e}[/yellow]")
        return False
