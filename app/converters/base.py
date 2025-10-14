"""Base converter interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseConverter(ABC):
    """Base class for code converters."""
    
    @abstractmethod
    def convert(self, source_code: str, context: Dict[str, Any]) -> str:
        """Convert source code to Rust."""
        pass
    
    @abstractmethod
    def generate_conversion_prompt(self, source_code: str, analysis: Dict[str, Any]) -> str:
        """Generate LLM prompt for conversion."""
        pass

