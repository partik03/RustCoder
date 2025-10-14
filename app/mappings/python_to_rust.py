"""Python library to Rust crate mappings.

⚠️  DEPRECATED: This module is now DEPRECATED in favor of dynamic LLM-driven crate selection.

The new approach (app/crate_suggester.py) uses LLM to analyze each project's dependencies
and suggest appropriate Rust crates dynamically, with explanations and version numbers.

Benefits of dynamic approach:
- No hardcoded mappings to maintain
- LLM suggests multiple options with rationale
- More context-aware suggestions
- Up-to-date crate recommendations
- User can choose interactively or auto-select

This file is kept for backward compatibility only. New code should use:
  - PythonConverter.analyze_and_prepare_with_crates()
  - DynamicCrateSuggester.analyze_and_suggest_crates()

Migration path:
  OLD: get_rust_crate("flask")  # Returns hardcoded string
  NEW: DynamicCrateSuggester(llm_client).analyze_and_suggest_crates(code, ["flask"], desc)
       # Returns: {"flask": [{"name": "axum", "version": "0.7", "reason": "...", "recommended": True}, ...]}
"""

# DEPRECATED: Hardcoded mappings - DO NOT ADD NEW ENTRIES
# Use app/crate_suggester.py for dynamic LLM-driven suggestions instead
PYTHON_CRATE_MAP = {
    # Web frameworks
    "flask": "axum = \"0.7\" or actix-web = \"4.0\"",
    "fastapi": "axum = \"0.7\" or actix-web = \"4.0\"",
    "django": "actix-web = \"4.0\"",
    "requests": "reqwest = { version = \"0.11\", features = [\"json\"] }",
    "aiohttp": "reqwest = { version = \"0.11\", features = [\"json\"] }",
    
    # Data science
    "numpy": "ndarray = \"0.15\"",
    "pandas": "polars = \"0.35\"",
    
    # CLI
    "click": "clap = { version = \"4.0\", features = [\"derive\"] }",
    "argparse": "clap = { version = \"4.0\", features = [\"derive\"] }",
    
    # Async
    "asyncio": "tokio = { version = \"1\", features = [\"full\"] }",
    
    # Serialization
    "json": "serde_json = \"1.0\"",
    "pydantic": "serde = { version = \"1.0\", features = [\"derive\"] }",
    
    # Database
    "sqlalchemy": "diesel = \"2.0\" or sqlx = \"0.7\"",
    "redis": "redis = \"0.24\"",
    
    # Testing
    "pytest": "# Use cargo test (built-in)",
    "unittest": "# Use cargo test (built-in)",
}


def get_rust_crate(python_lib: str) -> str:
    """Get Rust crate suggestion for Python library."""
    return PYTHON_CRATE_MAP.get(python_lib.lower(), f"# TODO: Find Rust equivalent for {python_lib}")

