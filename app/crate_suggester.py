"""LLM-driven dynamic crate suggestion for Python to Rust conversion."""

from typing import Dict, List, Any
from pathlib import Path


class DynamicCrateSuggester:
    """Use LLM to dynamically suggest Rust crates for Python dependencies."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def analyze_and_suggest_crates(
        self,
        python_code: str,
        dependencies: List[str],
        project_description: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze Python code and suggest appropriate Rust crates.
        
        Args:
            python_code: Sample Python code from the project
            dependencies: List of Python dependencies detected
            project_description: Optional project description
        
        Returns:
            {
                "suggestions": {
                    "flask": [
                        {"name": "axum", "version": "0.7", "reason": "...", "recommended": True},
                        {"name": "actix-web", "version": "4.0", "reason": "...", "recommended": False}
                    ],
                    ...
                },
                "analysis": "Overall analysis text",
                "dependencies_analyzed": ["flask", ...]
            }
        """
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            python_code,
            dependencies,
            project_description
        )
        
        system_message = """You are an expert in both Python and Rust ecosystems.
Analyze Python code and suggest the BEST Rust crates as alternatives.

For each Python library:
1. Suggest 2-3 suitable Rust crates (if multiple good options exist)
2. Explain WHY each crate is appropriate
3. Include version numbers
4. Note any caveats or limitations

Be specific and practical. Focus on mature, well-maintained crates."""
        
        # Call LLM
        response = self.llm_client.generate_text(
            prompt=prompt,
            system_message=system_message,
            max_tokens=2000,
            temperature=0.3
        )
        
        # Parse LLM response into structured format
        suggestions = self._parse_suggestions(response, dependencies)
        
        return {
            "suggestions": suggestions,
            "analysis": response,
            "dependencies_analyzed": dependencies
        }
    
    def _build_analysis_prompt(
        self,
        python_code: str,
        dependencies: List[str],
        project_description: str
    ) -> str:
        """Build prompt for LLM analysis."""
        
        deps_list = "\n".join(f"- {dep}" for dep in dependencies)
        
        # Truncate code to reasonable length
        code_sample = python_code[:1000] if len(python_code) > 1000 else python_code
        truncated = "..." if len(python_code) > 1000 else ""
        
        prompt = f"""Analyze this Python project and suggest appropriate Rust crates.

**Project Description:** {project_description or "Python project to convert to Rust"}

**Python Dependencies Detected:**
{deps_list}

**Sample Python Code:**
```python
{code_sample}{truncated}
```

**Your Task:**
For EACH Python dependency listed above, suggest 2-3 suitable Rust crates.

**Output Format (STRICT):**
For each dependency, use this EXACT format:

DEPENDENCY: <python_package>
OPTION_1:
name: <crate_name>
version: <version>
reason: <why this crate is suitable>
OPTION_2:
name: <crate_name>
version: <version>
reason: <why this crate is suitable>
RECOMMENDED: <option_number>

**Example:**
DEPENDENCY: requests
OPTION_1:
name: reqwest
version: 0.11
reason: Most popular HTTP client, supports async/sync, good ecosystem
OPTION_2:
name: ureq
version: 2.9
reason: Simpler, synchronous-only, smaller binary size
RECOMMENDED: 1

**Now analyze ALL dependencies:**
"""
        return prompt
    
    def _parse_suggestions(
        self,
        llm_response: str,
        dependencies: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Parse LLM response into structured suggestions.
        
        Args:
            llm_response: Raw LLM response text
            dependencies: List of dependencies to parse
        
        Returns:
            {
                "requests": [
                    {"name": "reqwest", "version": "0.11", "reason": "...", "recommended": True},
                    {"name": "ureq", "version": "2.9", "reason": "...", "recommended": False}
                ],
                ...
            }
        """
        suggestions = {}
        
        # Split response by DEPENDENCY markers
        sections = llm_response.split("DEPENDENCY:")
        
        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            # Extract dependency name
            dep_name = lines[0].strip()
            
            # Parse options
            options = []
            current_option = {}
            recommended_idx = None
            
            for line in lines[1:]:
                line = line.strip()
                
                if line.startswith("OPTION_"):
                    if current_option:
                        options.append(current_option)
                    current_option = {}
                
                elif "name:" in line.lower():
                    current_option["name"] = line.split(":", 1)[1].strip()
                
                elif "version:" in line.lower():
                    current_option["version"] = line.split(":", 1)[1].strip()
                
                elif "reason:" in line.lower():
                    current_option["reason"] = line.split(":", 1)[1].strip()
                
                elif line.startswith("RECOMMENDED:"):
                    rec_num = line.split(":", 1)[1].strip()
                    try:
                        recommended_idx = int(rec_num) - 1
                    except:
                        recommended_idx = 0
            
            # Add last option
            if current_option:
                options.append(current_option)
            
            # Mark recommended
            if options and recommended_idx is not None and 0 <= recommended_idx < len(options):
                options[recommended_idx]["recommended"] = True
            elif options:
                # If no recommendation found, mark first as recommended
                options[0]["recommended"] = True
            
            if options:
                suggestions[dep_name] = options
        
        # Add fallback for any dependencies not parsed
        for dep in dependencies:
            if dep not in suggestions:
                suggestions[dep] = self.get_fallback_suggestion(dep)
        
        return suggestions
    
    def get_fallback_suggestion(self, python_lib: str) -> List[Dict]:
        """Fallback if LLM parsing fails or no suggestion available."""
        return [{
            "name": f"[TODO: Research Rust equivalent for {python_lib}]",
            "version": "?",
            "reason": "LLM analysis failed - manual research needed",
            "recommended": True,
            "needs_research": True
        }]

