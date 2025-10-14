"""Python to Rust converter."""

from typing import Dict, Any, List
from pathlib import Path

from app.converters.base import BaseConverter
from app.analyzers.python_analyzer import PythonAnalyzer
from app.mappings.python_to_rust import get_rust_crate


class PythonConverter(BaseConverter):
    """Convert Python code to Rust using LLM."""
    
    def __init__(self):
        self.analyzer = PythonAnalyzer()
    
    def convert(self, source_code: str, context: Dict[str, Any]) -> str:
        """
        Convert Python code to Rust.
        
        This is a placeholder that will be called by the API endpoint.
        The actual LLM call happens in the API layer.
        """
        # This method will be used by the API endpoint
        # The actual conversion happens in generate_conversion_prompt + LLM call
        pass
    
    def generate_conversion_prompt(
        self, 
        source_code: str, 
        analysis: Dict[str, Any],
        project_description: str = ""
    ) -> str:
        """
        Generate a detailed prompt for Python → Rust conversion.
        
        Args:
            source_code: Original Python code
            analysis: Analysis from PythonAnalyzer
            project_description: Optional description of what the code does
        
        Returns:
            Formatted prompt for LLM
        """
        # Extract key information from analysis
        functions = analysis.get("functions", [])
        classes = analysis.get("classes", [])
        imports = analysis.get("imports", [])
        has_async = analysis.get("has_async", False)
        
        # Generate Rust crate recommendations
        crate_recommendations = self._generate_crate_recommendations(imports)
        
        # Build comprehensive prompt
        prompt = f"""You are an expert Rust developer specializing in converting Python code to idiomatic Rust.

TASK: Convert the following Python code to Rust.

PROJECT DESCRIPTION:
{project_description or "A Python project that needs to be converted to Rust."}

PYTHON CODE ANALYSIS:
- Functions: {len(functions)}
- Classes: {len(classes)}
- Uses async/await: {has_async}
- External dependencies: {len(imports)}

DETECTED PYTHON IMPORTS:
{self._format_imports(imports)}

RECOMMENDED RUST CRATES:
{crate_recommendations}

CONVERSION REQUIREMENTS:
1. Create a complete Cargo project with proper structure
2. Convert all Python functions to Rust functions with proper types
3. Convert Python classes to Rust structs with impl blocks
4. Handle Python's dynamic typing by using appropriate Rust types (i32, String, Vec, etc.)
5. Convert Python error handling (try/except) to Rust's Result<T, E>
6. If async code is present, use tokio runtime
7. Add proper error handling with Result and Option types
8. Include appropriate derive macros (Debug, Clone, etc.)
9. Add comprehensive Cargo.toml with all necessary dependencies
10. Include helpful comments explaining non-obvious conversions

PYTHON CODE TO CONVERT:
```python
{source_code}
```

OUTPUT FORMAT:
Provide the converted Rust code in the following format:

[filename: Cargo.toml]
[package]
name = "converted_project"
version = "0.1.0"
edition = "2021"

[dependencies]
# Include all recommended crates here
{self._format_cargo_dependencies(imports)}

[filename: src/main.rs]
// Converted Rust code here
// Include all necessary imports, structs, functions

[filename: README.md]
# Converted Python to Rust Project

## Original Python Features
- List the key features from the Python code

## Rust Implementation Notes
- Explain any significant conversion decisions
- Note any Python features that required special handling

IMPORTANT:
- Use the exact [filename: ...] format for all files
- Ensure the Rust code compiles without errors
- Use idiomatic Rust patterns (ownership, borrowing, lifetimes)
- Preserve the original functionality while making it type-safe
- Add error handling where Python code might fail at runtime
"""
        return prompt
    
    def _generate_crate_recommendations(self, imports: List[str]) -> str:
        """Generate Rust crate recommendations based on Python imports."""
        if not imports:
            return "No external dependencies detected."
        
        recommendations = []
        for imp in imports:
            crate = get_rust_crate(imp)
            recommendations.append(f"  - {imp} (Python) → {crate}")
        
        return "\n".join(recommendations)
    
    def _format_imports(self, imports: List[str]) -> str:
        """Format Python imports for display."""
        if not imports:
            return "  (none - uses only standard library)"
        
        return "\n".join(f"  - {imp}" for imp in imports)
    
    def _format_cargo_dependencies(self, imports: List[str]) -> str:
        """Format Cargo.toml dependencies based on Python imports."""
        if not imports:
            return "# No external dependencies needed"
        
        deps = []
        for imp in imports:
            crate = get_rust_crate(imp)
            if not crate.startswith("#"):
                deps.append(crate)
        
        return "\n".join(deps) if deps else "# Add dependencies as needed"
    
    def analyze_and_prepare(self, project_path: Path) -> Dict[str, Any]:
        """
        Analyze a Python project and prepare conversion context.
        
        Returns:
            Dictionary with analysis and conversion context
        
        Raises:
            ValueError: If no Python files found or main file is empty
        """
        analysis = self.analyzer.analyze_project(project_path)
        
        # Find main entry point
        main_file = self._find_main_file(project_path)
        
        if not main_file:
            raise ValueError(f"No Python files found in {project_path}")
        
        # Read main file content
        main_code = ""
        if main_file:
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    main_code = f.read()
            except Exception as e:
                raise ValueError(f"Failed to read {main_file}: {e}")
        
        # Check if file is empty
        if not main_code.strip():
            raise ValueError(f"Main file {main_file} is empty")
        
        # Check file size and truncate if too large (warn if >50KB)
        max_size = 50 * 1024  # 50KB
        if len(main_code) > max_size:
            warning = f"File {main_file} is large ({len(main_code)} bytes). Truncating to {max_size} bytes for conversion."
            print(f"WARNING: {warning}")
            main_code = main_code[:max_size] + "\n# ... (truncated for LLM context limit)"
        
        return {
            "analysis": analysis,
            "main_file": str(main_file) if main_file else None,
            "main_code": main_code,
            "project_path": str(project_path),
        }
    
    def _find_main_file(self, project_path: Path) -> Path:
        """Find the main entry point file."""
        # Common main file names
        candidates = [
            "__main__.py",
            "main.py",
            "app.py",
            "__init__.py",
            "cli.py",
            "run.py",
        ]
        
        for candidate in candidates:
            main_file = project_path / candidate
            if main_file.exists():
                return main_file
        
        # If no common name found, return first .py file
        py_files = list(project_path.glob("*.py"))
        if py_files:
            return py_files[0]
        
        return None
    
    def validate_conversion_result(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate the conversion result to ensure quality.
        
        Args:
            files: Dictionary of filename -> content from LLM
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check for required files
        if "Cargo.toml" not in files:
            errors.append("Missing Cargo.toml file")
        
        if "src/main.rs" not in files and "main.rs" not in files:
            errors.append("Missing src/main.rs or main.rs file")
        
        # Validate Cargo.toml
        cargo_toml = files.get("Cargo.toml", "")
        if cargo_toml:
            if "[package]" not in cargo_toml:
                errors.append("Cargo.toml missing [package] section")
            if "name =" not in cargo_toml:
                errors.append("Cargo.toml missing package name")
            if "edition" not in cargo_toml:
                warnings.append("Cargo.toml missing edition field")
        
        # Validate main.rs
        main_rs = files.get("src/main.rs", files.get("main.rs", ""))
        if main_rs:
            # Check for at least one function or struct
            has_fn = "fn " in main_rs
            has_struct = "struct " in main_rs
            has_impl = "impl " in main_rs
            
            if not (has_fn or has_struct):
                warnings.append("No functions or structs found in main.rs")
            
            # Check for main function
            if "fn main()" not in main_rs:
                warnings.append("No main() function found - might not be executable")
            
            # Check for common issues
            if main_rs.strip().startswith("```"):
                errors.append("main.rs contains markdown code blocks - parsing failed")
            
            # Check minimum length
            if len(main_rs.strip()) < 10:
                errors.append("main.rs is too short - conversion likely failed")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "files_count": len(files),
            "has_cargo_toml": "Cargo.toml" in files,
            "has_main_rs": bool(main_rs),
        }
    
    async def convert_with_sdk(
        self,
        project_path: Path,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Convert using Claude Agent SDK (advanced mode).
        
        This uses Claude's Anthropic API for more powerful workflow orchestration.
        Requires ANTHROPIC_API_KEY to be set.
        
        Args:
            project_path: Path to Python project
            description: Project description
        
        Returns:
            Dict with conversion results including files, messages, success status
        
        Raises:
            ValueError: If no Python code found or SDK not available
            ImportError: If anthropic package not installed
        """
        from app.claude_sdk_wrapper import ClaudeSDKWrapper, is_claude_sdk_available
        
        if not is_claude_sdk_available():
            raise ValueError(
                "Claude SDK not available. "
                "Install anthropic package and set ANTHROPIC_API_KEY environment variable."
            )
        
        # Analyze first using standard analyzer
        conversion_context = self.analyze_and_prepare(project_path)
        main_code = conversion_context.get("main_code", "")
        analysis = conversion_context.get("analysis", {})
        
        if not main_code:
            raise ValueError("No Python code found in project")
        
        # Get crate recommendations from mappings
        dependencies = analysis.get("dependencies", [])
        crate_recommendations = {}
        
        from app.mappings.python_to_rust import get_rust_crate
        for dep in dependencies:
            rust_crate = get_rust_crate(dep)
            if not rust_crate.startswith("#"):  # Skip comments
                crate_recommendations[dep] = rust_crate
        
        # Use SDK for conversion
        import os
        wrapper = ClaudeSDKWrapper(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("CLAUDE_SDK_MODEL", "claude-sonnet-4")
        )
        
        try:
            result = await wrapper.convert_python_to_rust(
                main_code,
                description,
                project_path,
                crate_recommendations
            )
            
            return result
            
        finally:
            await wrapper.close()
    
    def analyze_and_prepare_with_crates(
        self,
        project_path: Path,
        description: str = "",
        interactive: bool = True,
        llm_client=None
    ) -> Dict[str, Any]:
        """
        Analyze Python project and get dynamic crate suggestions from LLM.
        
        This is the NEW dynamic approach that replaces hardcoded mappings.
        
        Args:
            project_path: Path to Python project
            description: Project description
            interactive: If True, user selects crates; if False, auto-select
            llm_client: LLM client instance (optional, will use global if not provided)
        
        Returns:
            All context needed for conversion including selected crates
        """
        from app.crate_suggester import DynamicCrateSuggester
        from app.interactive_selector import InteractiveCrateSelector
        
        # Step 1: Basic analysis
        analysis = self.analyzer.analyze_project(project_path)
        
        # Step 2: Read all Python files
        python_files = {}
        for file_info in analysis.get("files", []):
            file_path = Path(file_info["file"])
            if file_path.exists() and file_path.suffix == ".py":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        python_files[file_path.name] = f.read()
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
        
        if not python_files:
            raise ValueError("No Python files found in project")
        
        # Step 3: Get main file for LLM analysis
        main_file = self._find_main_file(project_path)
        sample_code = ""
        if main_file and main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                sample_code = f.read()
        else:
            # Use first file as sample
            sample_code = list(python_files.values())[0]
        
        # Step 4: LLM-driven crate suggestion
        dependencies = analysis.get("dependencies", [])
        selected_crates = {}
        llm_analysis = ""
        
        if dependencies:
            # Get LLM client
            if llm_client is None:
                # Import here to avoid circular imports
                import os
                from app.llm_client import LlamaEdgeClient
                llm_client = LlamaEdgeClient(
                    api_base=os.getenv("LLM_API_BASE", "http://localhost:8080/v1"),
                    api_key=os.getenv("LLM_API_KEY", ""),
                    model=os.getenv("LLM_MODEL", "Qwen2.5-Coder-3B-Instruct")
                )
            
            suggester = DynamicCrateSuggester(llm_client)
            
            print("🤖 Asking LLM to analyze dependencies and suggest Rust crates...")
            
            suggestion_result = suggester.analyze_and_suggest_crates(
                sample_code,
                dependencies,
                description
            )
            
            suggestions = suggestion_result["suggestions"]
            llm_analysis = suggestion_result.get("analysis", "")
            
            # Step 5: User selects from suggestions
            selector = InteractiveCrateSelector()
            selected_crates = selector.select_from_suggestions(
                suggestions,
                auto_mode=not interactive
            )
        else:
            print("ℹ️  No external dependencies detected")
        
        return {
            "analysis": analysis,
            "python_files": python_files,
            "main_file": str(main_file) if main_file else None,
            "sample_code": sample_code,
            "selected_crates": selected_crates,
            "llm_analysis": llm_analysis
        }
    
    def generate_conversion_prompt_dynamic(
        self,
        conversion_context: Dict[str, Any],
        project_description: str = ""
    ) -> str:
        """
        Generate conversion prompt using dynamic LLM-suggested crates.
        
        NO hardcoded mappings - uses actual LLM suggestions from analyze_and_prepare_with_crates.
        
        Args:
            conversion_context: Result from analyze_and_prepare_with_crates
            project_description: Optional project description
        
        Returns:
            Formatted conversion prompt for LLM
        """
        
        analysis = conversion_context["analysis"]
        python_files = conversion_context["python_files"]
        selected_crates = conversion_context["selected_crates"]
        sample_code = conversion_context["sample_code"]
        
        # Format selected crates info
        crate_details = ""
        if selected_crates:
            crate_details = "\n**Selected Rust Crates (LLM-suggested):**\n"
            for py_dep, crate_info in selected_crates.items():
                crate_details += f"\n• {py_dep} → {crate_info['name']} v{crate_info['version']}\n"
                crate_details += f"  Reason: {crate_info['reason']}\n"
        
        # Format file structure
        file_structure = "\n**Project Files:**\n"
        for filename in python_files.keys():
            file_structure += f"- {filename}\n"
        
        # Build comprehensive prompt
        prompt = f"""Convert this Python project to idiomatic Rust.

**Project:** {project_description or "Python to Rust conversion"}

**Analysis:**
- Total Files: {len(python_files)}
- Functions: {analysis.get('total_functions', 0)}
- Classes: {analysis.get('total_classes', 0)}
- Dependencies: {len(analysis.get('dependencies', []))}
{file_structure}
{crate_details}

**CRITICAL Requirements:**

1. **Use ONLY the Rust crates listed above**
   - These were specifically selected via LLM analysis
   - Do NOT substitute or add other crates
   - If a Python library has no Rust equivalent listed, note it as TODO

2. **Project Structure:**
   - Cargo.toml with EXACT crates listed above
   - src/main.rs or src/lib.rs
   - Preserve module structure from Python

3. **Code Quality:**
   - Idiomatic Rust (not direct translation)
   - Proper error handling with Result/Option
   - Use Rust ownership correctly
   - Add type annotations
   - Follow Rust naming (snake_case)

4. **For Each Python File:**
   - Convert to appropriate Rust module
   - Maintain functionality
   - Add doc comments

**Python Code:**

{self._format_all_files(python_files)}

**Output Format:**

[filename: Cargo.toml]
[package]
name = "converted_project"
version = "0.1.0"
edition = "2021"

[dependencies]
{self._format_cargo_deps_dynamic(selected_crates)}

[filename: src/main.rs]
// Converted Rust code

[filename: README.md]
# Conversion Notes
- Python files converted: {len(python_files)}
- Rust crates used: {len(selected_crates)}

**MUST compile without errors!**
"""
        return prompt
    
    def _format_all_files(self, python_files: Dict[str, str]) -> str:
        """Format all Python files for prompt."""
        formatted = ""
        for filename, code in python_files.items():
            formatted += f"\n### File: {filename}\n```python\n{code}\n```\n"
        return formatted
    
    def _format_cargo_deps_dynamic(self, selected_crates: Dict[str, Dict]) -> str:
        """Format dependencies from dynamic selections."""
        from app.interactive_selector import InteractiveCrateSelector
        selector = InteractiveCrateSelector()
        return selector.format_for_cargo(selected_crates)
