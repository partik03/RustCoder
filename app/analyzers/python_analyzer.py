"""Python code analyzer using AST."""

import ast
from pathlib import Path
from typing import Dict, Any, List

from app.analyzers.base import BaseAnalyzer


class PythonAnalyzer(BaseAnalyzer):
    """Analyze Python code structure."""
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a Python file.
        
        Returns analysis dict with error handling for syntax errors and large files.
        """
        # Skip __pycache__ and .pyc files
        if "__pycache__" in str(file_path) or file_path.suffix == ".pyc":
            return {"error": "Skipped __pycache__ or .pyc file", "file": str(file_path)}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return {"error": f"Failed to read file: {e}", "file": str(file_path)}
        
        # Check if empty
        if not code.strip():
            return {"error": "Empty file", "file": str(file_path)}
        
        # Check file size (warn if >10KB)
        file_size_kb = len(code) / 1024
        size_warning = None
        if file_size_kb > 10:
            size_warning = f"Large file ({file_size_kb:.1f} KB)"
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "error": f"Syntax error: {e}",
                "file": str(file_path),
                "line": e.lineno if hasattr(e, 'lineno') else None
            }
        except Exception as e:
            return {"error": f"Parse error: {e}", "file": str(file_path)}
        
        result = {
            "file": str(file_path),
            "functions": self._extract_functions(tree),
            "classes": self._extract_classes(tree),
            "imports": self._extract_imports(tree),
            "has_async": self._has_async_code(tree),
            "complexity": self._estimate_complexity(tree),
        }
        
        if size_warning:
            result["warning"] = size_warning
        
        return result
    
    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze entire Python project with proper filtering."""
        python_files = list(project_path.rglob("*.py"))
        
        # Filter out unwanted files
        filtered_files = []
        for py_file in python_files:
            file_str = str(py_file)
            # Skip virtual environments, pycache, and test directories
            if any(skip in file_str for skip in ["venv", ".venv", "__pycache__", ".pyc", "site-packages"]):
                continue
            filtered_files.append(py_file)
        
        analysis = {
            "project_path": str(project_path),
            "total_files": len(filtered_files),
            "files": [],
            "total_functions": 0,
            "total_classes": 0,
            "dependencies": self.extract_dependencies(project_path),
        }
        
        for py_file in filtered_files:
            file_analysis = self.analyze_file(py_file)
            analysis["files"].append(file_analysis)
            
            if "functions" in file_analysis:
                analysis["total_functions"] += len(file_analysis["functions"])
            if "classes" in file_analysis:
                analysis["total_classes"] += len(file_analysis["classes"])
        
        return analysis
    
    def extract_dependencies(self, project_path: Path) -> List[str]:
        """Extract dependencies from requirements.txt or pyproject.toml."""
        deps = []
        
        # Check requirements.txt
        req_file = project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name (before ==, >=, etc.)
                        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        deps.append(pkg)
        
        return deps
    
    def _extract_functions(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "has_decorators": len(node.decorator_list) > 0,
                    "line": node.lineno,
                })
        return functions
    
    def _extract_classes(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "methods": methods,
                    "line": node.lineno,
                })
        return classes
    
    def _extract_imports(self, tree: ast.Module) -> List[str]:
        """Extract import statements."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return list(imports)
    
    def _has_async_code(self, tree: ast.Module) -> bool:
        """Check if code uses async/await."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith)):
                return True
        return False
    
    def _estimate_complexity(self, tree: ast.Module) -> str:
        """Estimate code complexity (simple heuristic)."""
        num_nodes = len(list(ast.walk(tree)))
        
        if num_nodes < 50:
            return "simple"
        elif num_nodes < 200:
            return "moderate"
        else:
            return "complex"

