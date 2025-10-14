"""C++ code analyzer (basic pattern matching)."""

from pathlib import Path
from typing import Dict, Any, List
import re

from app.analyzers.base import BaseAnalyzer


class CppAnalyzer(BaseAnalyzer):
    """Analyze C++ code structure (basic implementation)."""
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a C++ file (basic pattern matching)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        return {
            "file": str(file_path),
            "classes": self._find_classes(code),
            "functions": self._find_functions(code),
            "includes": self._find_includes(code),
            "has_templates": "<template>" in code or "template<" in code,
            "has_pointers": "*" in code or "->" in code,
        }
    
    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze C++ project."""
        cpp_files = list(project_path.rglob("*.cpp")) + list(project_path.rglob("*.h"))
        
        return {
            "project_path": str(project_path),
            "total_files": len(cpp_files),
            "files": [self.analyze_file(f) for f in cpp_files],
            "note": "Basic C++ analysis - may need enhancement",
        }
    
    def extract_dependencies(self, project_path: Path) -> List[str]:
        """Extract C++ dependencies (from CMakeLists.txt or includes)."""
        # TODO: Parse CMakeLists.txt
        return ["TODO: Implement C++ dependency extraction"]
    
    def _find_classes(self, code: str) -> List[str]:
        """Find class definitions."""
        pattern = r'class\s+(\w+)'
        return re.findall(pattern, code)
    
    def _find_functions(self, code: str) -> List[str]:
        """Find function definitions (very basic)."""
        pattern = r'\w+\s+(\w+)\s*\([^)]*\)\s*{'
        return re.findall(pattern, code)
    
    def _find_includes(self, code: str) -> List[str]:
        """Find #include statements."""
        pattern = r'#include\s*[<"]([^>"]+)[>"]'
        return re.findall(pattern, code)

