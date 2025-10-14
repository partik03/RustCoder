"""Tests for Python analyzer."""

import pytest
from pathlib import Path
import tempfile
from app.analyzers.python_analyzer import PythonAnalyzer


def test_analyze_simple_function():
    """Test analyzing a simple Python function."""
    code = """
def greet(name: str) -> str:
    return f"Hello, {name}"
"""
    
    analyzer = PythonAnalyzer()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        result = analyzer.analyze_file(temp_path)
        
        assert "functions" in result
        assert len(result["functions"]) == 1
        assert result["functions"][0]["name"] == "greet"
        assert result["functions"][0]["args"] == ["name"]
    finally:
        temp_path.unlink()


def test_analyze_class():
    """Test analyzing a Python class."""
    code = """
class Calculator:
    def add(self, a, b):
        return a + b
"""
    
    analyzer = PythonAnalyzer()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        result = analyzer.analyze_file(temp_path)
        
        assert "classes" in result
        assert len(result["classes"]) == 1
        assert result["classes"][0]["name"] == "Calculator"
        assert "add" in result["classes"][0]["methods"]
    finally:
        temp_path.unlink()


def test_detect_async():
    """Test detecting async code."""
    code = """
async def fetch():
    await something()
"""
    
    analyzer = PythonAnalyzer()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        result = analyzer.analyze_file(temp_path)
        
        assert result["has_async"] is True
    finally:
        temp_path.unlink()


def test_extract_imports():
    """Test extracting imports."""
    code = """
import os
import sys
from pathlib import Path
"""
    
    analyzer = PythonAnalyzer()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        result = analyzer.analyze_file(temp_path)
        
        assert "imports" in result
        assert "os" in result["imports"]
        assert "sys" in result["imports"]
        assert "pathlib" in result["imports"]
    finally:
        temp_path.unlink()

