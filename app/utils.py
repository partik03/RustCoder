"""Utility functions."""

from pathlib import Path
from typing import List


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory."""
    return [f for f in directory.rglob("*.py") if "venv" not in str(f) and ".venv" not in str(f)]


def find_cpp_files(directory: Path) -> List[Path]:
    """Find all C++ files in directory."""
    cpp_extensions = ["*.cpp", "*.cc", "*.cxx", "*.h", "*.hpp"]
    files = []
    for ext in cpp_extensions:
        files.extend(directory.rglob(ext))
    return files


def detect_project_language(directory: Path) -> str:
    """Detect primary language of a project."""
    py_files = len(find_python_files(directory))
    cpp_files = len(find_cpp_files(directory))
    
    if py_files > cpp_files:
        return "python"
    elif cpp_files > 0:
        return "cpp"
    else:
        return "unknown"

