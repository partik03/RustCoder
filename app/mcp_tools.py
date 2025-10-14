import httpx
import sys
import json
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Get API host from environment variable or use default
# Use localhost as default for non-Docker environments
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

mcp = FastMCP("Rust compiler tools")

@mcp.tool()
async def generate(description: str, requirements: str) -> str:
    """
      Generate a new Rust cargo project from the description and requirements. The input arguments are

        * description: a text string description of the generated Rust project.
        * requiremenets: functional requirements on what the generated Rust project.

      The return value is a text string that contains all files in the project. Each file is seperated by a [filename: path_to_file] line. For example, a project that contains a Cargo.toml file and a src/main.rs file will be returned as the following.

[filename: Cargo.toml]
[package]
name = "a_command_line_calcu"
version = "0.1.0"
edition = "2021"

[dependencies]


[filename: src/main.rs]
fn main() {
    println!("Hello, world!");
}

    """

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{API_BASE_URL}/generate-sync", json={'description': description, 'requirements': requirements})
            response.raise_for_status()

            resp_json = json.loads(response.text)
            if "combined_text" in resp_json:
                return resp_json["combined_text"]
            else:
                return "Rust project creation error."
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return f"Error trying to generate a Rust project: {str(e)}"

@mcp.tool()
async def compile_and_fix(code: str, description: str = "A Rust project", max_attempts: int = 3) -> str:
    """
        Compile a Rust cargo project and fix any compiler errors.

        The argument `code` is a text string that contains all files in the project. Each file is seperated by a [filename: path_to_file] line. For example, a project that contains a Cargo.toml file and a src/main.rs file will be returned as the following.

[filename: Cargo.toml]
[package]
name = "a_command_line_calcu"
version = "0.1.0"
edition = "2021"

[dependencies]


[filename: src/main.rs]
fn main() {
    println!("Hello, world!");
}

        The return value is also a text string that contains all files in the project. It is in the same format as the input `code` argument.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/compile-and-fix", 
                json={'code': code, 'description': description, 'max_attempts': max_attempts}
            )
            response.raise_for_status()
            
            resp_json = json.loads(response.text)
            if "combined_text" in resp_json:
                return resp_json["combined_text"]
            else:
                return "Cannot fix the Rust compiler error."
            # return response.text
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return f"Error trying to fixing the Rust compiler error: {str(e)}"

@mcp.tool()
async def compile(code: str) -> str:
    """
        Compile a Rust cargo project and return the compiler output.

        The argument `code` is a text string that contains all files in the project. Each file is seperated by a [filename: path_to_file] line. For example, a project that contains a Cargo.toml file and a src/main.rs file will be returned as the following.

[filename: Cargo.toml]
[package]
name = "a_command_line_calcu"
version = "0.1.0"
edition = "2021"

[dependencies]


[filename: src/main.rs]
fn main() {
    println!("Hello, world!");
}

        The return value is a text string that contains the Rust compiler output.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{API_BASE_URL}/compile", json={'code': code})
            response.raise_for_status()
            
            resp_json = json.loads(response.text)
            if "build_output" in resp_json:
                return resp_json["build_output"]
            else:
                return "Rust compiler error."
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return f"Rust compiler error: {str(e)}"

@mcp.tool()
async def analyze_python_project(project_path: str) -> str:
    """
    Analyze a Python project to prepare for Rust conversion.
    
    Provides detailed analysis including:
    - All Python files in the project
    - Functions and classes detected
    - Dependencies from requirements.txt
    - Recommended Rust crates
    - Code complexity assessment
    
    Args:
        project_path: Absolute path to the Python project directory
    
    Returns:
        JSON string with comprehensive project analysis
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/analyze-python",
                json={"project_path": project_path}
            )
            response.raise_for_status()
            
            resp_json = json.loads(response.text)
            
            # Format response nicely
            analysis = resp_json.get("analysis", {})
            recommendations = resp_json.get("crate_recommendations", [])
            
            result = f"""Python Project Analysis
{'=' * 50}

Project: {analysis.get('project_path', 'Unknown')}
Total Files: {analysis.get('total_files', 0)}
Total Functions: {analysis.get('total_functions', 0)}
Total Classes: {analysis.get('total_classes', 0)}

Dependencies:
{chr(10).join(f"  - {dep}" for dep in analysis.get('dependencies', [])[:10])}

Recommended Rust Crates:
{chr(10).join(f"  - {rec}" for rec in recommendations[:10])}

Ready for conversion: {'Yes' if analysis.get('total_files', 0) > 0 else 'No'}
"""
            return result
            
    except httpx.HTTPError as e:
        return f"Error analyzing project: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@mcp.tool()
async def convert_python_to_rust(
    project_path: str,
    description: str = "",
    max_fix_attempts: int = 3
) -> str:
    """
    Convert a Python project to Rust.
    
    This tool performs a complete conversion:
    1. Analyzes the Python code structure
    2. Generates idiomatic Rust code using AI
    3. Compiles the Rust code
    4. Automatically fixes compilation errors
    5. Returns the complete Rust project
    
    Args:
        project_path: Absolute path to the Python project directory
        description: Optional description of what the code does (helps with conversion)
        max_fix_attempts: Maximum attempts to fix compilation errors (default: 3)
    
    Returns:
        Multi-file Rust project in [filename: ...] format
    
    Example:
        convert_python_to_rust(
            project_path="/home/user/my_python_app",
            description="A CLI calculator that adds and multiplies numbers",
            max_fix_attempts=5
        )
    """
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/convert-python-to-rust",
                json={
                    "project_path": project_path,
                    "description": description,
                    "max_fix_attempts": max_fix_attempts
                }
            )
            response.raise_for_status()
            
            resp_json = json.loads(response.text)
            
            # Check if conversion was successful
            if resp_json.get("success"):
                return resp_json.get("combined_text", "Conversion completed but no output")
            else:
                error_msg = resp_json.get("error", "Unknown error")
                return f"Conversion failed: {error_msg}"
                
    except httpx.TimeoutException:
        return "Error: Conversion timed out. Try with a smaller project or increase timeout."
    except httpx.HTTPError as e:
        return f"Error during conversion: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@mcp.tool()
async def convert_python_file_to_rust(
    file_path: str,
    description: str = ""
) -> str:
    """
    Convert a single Python file to Rust.
    
    Simpler than convert_python_to_rust - just converts one file.
    Useful for converting individual Python modules or scripts.
    
    Args:
        file_path: Absolute path to the Python file
        description: Optional description of what the code does
    
    Returns:
        Rust code as a single file or simple Cargo project
    """
    try:
        # Read the Python file
        from pathlib import Path
        py_file = Path(file_path)
        
        if not py_file.exists():
            return f"Error: File not found: {file_path}"
        
        with open(py_file, 'r', encoding='utf-8') as f:
            python_code = f.read()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/convert-python-file",
                json={
                    "python_code": python_code,
                    "file_name": py_file.name,
                    "description": description
                }
            )
            response.raise_for_status()
            
            resp_json = json.loads(response.text)
            return resp_json.get("rust_code", "Conversion failed")
            
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def set_model(model: str) -> str:
    """
    Set the LLM model for conversions.
    
    Available models:
    - claude-sonnet: Claude Sonnet 4.5 (recommended for quality)
    - claude-opus: Claude Opus 4 (most capable, slower)
    - gemini: Gemini Pro (Google's model)
    - local: Local/Gaia model (fastest, no API cost)
    
    Args:
        model: Model identifier (claude-sonnet, claude-opus, gemini, local)
    
    Returns:
        Confirmation message with model details
    
    Example:
        set_model(model="claude-sonnet")
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/config/model/{model}"
            )
            response.raise_for_status()
            
            result = json.loads(response.text)
            
            if result.get("success"):
                return f"""✓ Model set successfully!

Model: {result.get('model')}
Full Name: {result.get('model_name')}

This model will be used for all future conversions.
"""
            else:
                return f"Failed to set model: {result.get('message', 'Unknown error')}"
                
    except httpx.HTTPError as e:
        return f"Error setting model: {str(e)}\n\nAvailable models: claude-sonnet, claude-opus, gemini, local"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@mcp.tool()
async def get_current_model() -> str:
    """
    Get the currently active LLM model configuration.
    
    Returns:
        Current model information including:
        - Active model name
        - Full model identifier
        - Available models
        - API configuration
    
    Example:
        get_current_model()
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/config/model"
            )
            response.raise_for_status()
            
            config = json.loads(response.text)
            
            available = config.get("available_models", [])
            
            return f"""Current Model Configuration:

Active Model: {config.get('model')}
Full Name: {config.get('model_name')}

Available Models:
{chr(10).join(f"  - {m}" for m in available)}

To change model, use:
  set_model(model="model-name")
"""
            
    except Exception as e:
        return f"Error getting model config: {str(e)}"


if __name__ == "__main__":
    # Use transport from environment variable or default to stdio
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    print(f"Starting MCP server with {transport} transport")
    print(f"API URL: {API_BASE_URL}")
    mcp.run(transport=transport)
