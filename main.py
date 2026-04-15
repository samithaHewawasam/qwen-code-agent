#!/usr/bin/env python3
"""
Qwen Code Agent - CLI Entry Point
A Claude Code-like coding assistant powered by qwen2.5-coder:7b
"""
import os
import sys
from typing import Optional, Dict, Any
import click
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from agent import QwenCodeAgent
from tools import register_tools

console = Console()

# Load environment variables
load_dotenv()


def get_config(
    model: Optional[str] = None,
    ollama_host: Optional[str] = None,
    chroma_host: Optional[str] = None,
    chroma_port: Optional[int] = None
) -> Dict[str, Any]:
    """Load configuration from parameters or environment variables"""
    return {
        'model': model or os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b'),
        'ollama_host': ollama_host or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'chroma_host': chroma_host or os.getenv('CHROMA_HOST', 'localhost'),
        'chroma_port': chroma_port or int(os.getenv('CHROMA_PORT', '8000')),
        'collection_name': os.getenv('CHROMA_COLLECTION', 'codebase')
    }


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Qwen Code Agent - AI coding assistant powered by qwen2.5-coder:7b"""
    # If no subcommand is provided, start interactive chat
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


@cli.command()
@click.option('--model', default=None, help='Ollama model to use')
@click.option('--ollama-host', default=None, help='Ollama server URL')
@click.option('--chroma-host', default=None, help='ChromaDB host')
@click.option('--chroma-port', type=int, default=None, help='ChromaDB port')
def chat(model, ollama_host, chroma_host, chroma_port):
    """Start an interactive chat session with the agent"""

    # Get configuration from env or parameters
    config = get_config(model, ollama_host, chroma_host, chroma_port)

    try:
        # Initialize agent
        console.print(f"[cyan]Initializing agent with model: {config['model']}[/cyan]")
        agent = QwenCodeAgent(model=config['model'], ollama_host=config['ollama_host'])

        # Register tools
        console.print("[cyan]Registering tools...[/cyan]")
        register_tools(agent, config['chroma_host'], config['chroma_port'], config['collection_name'])

        # Start chat
        agent.chat()

    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('prompt')
@click.option('--model', default=None, help='Ollama model to use')
@click.option('--ollama-host', default=None, help='Ollama server URL')
def run(prompt, model, ollama_host):
    """Run a single prompt and exit"""

    config = get_config(model, ollama_host)

    try:
        # Initialize agent
        agent = QwenCodeAgent(model=config['model'], ollama_host=config['ollama_host'])
        register_tools(agent, config['chroma_host'], config['chroma_port'], config['collection_name'])

        # Run single turn
        response = agent.run_turn(prompt)

        # Print response
        console.print(Markdown(response))

    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--force', is_flag=True, help='Force re-indexing even if already indexed')
def index(force):
    """Index the current directory for code search"""
    config = get_config()

    try:
        import chromadb
        from indexer import CodeIndexer

        # Connect to ChromaDB
        console.print("[cyan]Connecting to ChromaDB...[/cyan]")
        client = chromadb.HttpClient(
            host=config['chroma_host'],
            port=config['chroma_port']
        )

        collection = client.get_or_create_collection(name=config['collection_name'])

        # Check if already indexed
        if not force:
            count = collection.count()
            if count > 0:
                console.print(f"[yellow]Codebase already indexed ({count} chunks)[/yellow]")
                console.print("[yellow]Use --force to re-index[/yellow]")
                return

        # Clear collection if force
        if force:
            console.print("[yellow]Clearing existing index...[/yellow]")
            client.delete_collection(name=config['collection_name'])
            collection = client.get_or_create_collection(name=config['collection_name'])

        # Index directory
        indexer = CodeIndexer(client, collection)
        result = indexer.index_directory(".")

        if result:
            console.print("\n[green]Indexing complete![/green]")
        else:
            console.print("\n[yellow]No files were indexed[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
def info():
    """Display system information and configuration"""

    console.print("\n[bold cyan]Qwen Code Agent - System Information[/bold cyan]\n")

    # Environment configuration
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Ollama Model: {os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b')}")
    console.print(f"  Ollama Host: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
    console.print(f"  ChromaDB Host: {os.getenv('CHROMA_HOST', 'localhost')}")
    console.print(f"  ChromaDB Port: {os.getenv('CHROMA_PORT', '8000')}")
    console.print(f"  Collection: {os.getenv('CHROMA_COLLECTION', 'codebase')}")

    # Check Ollama connection
    console.print("\n[bold]Service Status:[/bold]")
    try:
        import ollama
        models = ollama.list()
        console.print("  Ollama: [green]Connected[/green]")
        console.print(f"  Available models: {len(models.get('models', []))}")
    except Exception as e:
        console.print(f"  Ollama: [red]Not connected ({str(e)})[/red]")

    # Check ChromaDB connection
    try:
        import chromadb
        client = chromadb.HttpClient(
            host=os.getenv('CHROMA_HOST', 'localhost'),
            port=int(os.getenv('CHROMA_PORT', '8000'))
        )
        client.heartbeat()
        console.print("  ChromaDB: [green]Connected[/green]")
    except Exception as e:
        console.print(f"  ChromaDB: [yellow]Not connected ({str(e)})[/yellow]")

    console.print()


if __name__ == '__main__':
    cli()
