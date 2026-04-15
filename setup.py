#!/usr/bin/env python3
"""
Setup script for Qwen Code Agent
Install globally with: pip install -e .
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="qwen-code-agent",
    version="0.1.0",
    description="A Claude Code-like coding assistant powered by qwen2.5-coder:7b",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/qwen-code-agent",
    py_modules=["main", "agent", "tools", "indexer"],
    python_requires=">=3.8",
    install_requires=[
        "ollama>=0.1.0",
        "chromadb>=0.4.0",
        "rich>=13.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "qwen=main:cli",  # Main command
            "qwen-agent=main:cli",
            "qa=main:cli",  # Short alias
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
