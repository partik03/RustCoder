"""Base analyzer interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path


class BaseAnalyzer(ABC):
    """Base class for code analyzers."""
    
    @abstractmethod
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single source file."""
        pass
    
    @abstractmethod
    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze an entire project."""
        pass
    
    @abstractmethod
    def extract_dependencies(self, project_path: Path) -> List[str]:
        """Extract project dependencies."""
        pass

