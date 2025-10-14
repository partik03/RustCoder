"""Claude Agent SDK integration for advanced conversion workflows."""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import os

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage
)


class ClaudeSDKWrapper:
    """Wrapper for Claude Agent SDK conversions."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5"
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
    
    async def convert_python_to_rust(
        self,
        python_code: str,
        description: str,
        project_path: Path,
        crate_recommendations: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Convert Python to Rust using Claude Agent SDK.
        
        Uses Claude's built-in file tools and workflows.
        """
        
        # Prepare crate suggestions
        crate_info = ""
        if crate_recommendations:
            crate_info = "\n\nSuggested Rust crates:\n"
            for py_lib, rust_crate in crate_recommendations.items():
                crate_info += f"- {py_lib} → {rust_crate}\n"
        
        # Configure SDK options
        options = ClaudeAgentOptions(
            model=self.model,
            allowed_tools=["Read", "Write", "Edit", "Bash"],
            permission_mode="acceptEdits",
            cwd=str(project_path),
            max_turns=20
        )
        
        # Create SDK client
        async with ClaudeSDKClient(options=options) as client:
            # Main conversion prompt
            prompt = f"""I need you to convert this Python code to Rust.

**Project Description:** {description}

**Python Code:**
```python
{python_code}
```
{crate_info}

**Tasks:**
1. Create a proper Cargo.toml with recommended dependencies
2. Convert the Python code to idiomatic Rust in src/main.rs
3. Ensure proper error handling with Result types
4. Add a README.md explaining the conversion
5. Try to compile with cargo build
6. If there are errors, fix them iteratively

Use the Write tool to create all necessary files in the current directory.
After creating files, use Bash tool to run cargo build and fix any errors.
"""
            
            # Send query to Claude
            await client.query(prompt)
            
            # Collect all responses
            messages = []
            files_created = []
            build_success = False
            build_output = ""
            
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            messages.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            # Track files being written
                            if block.name == "Write":
                                file_path = block.input.get("file_path", "")
                                files_created.append(file_path)
                
                elif isinstance(message, ResultMessage):
                    # Check if conversion succeeded
                    build_success = not message.is_error
                    if hasattr(message, 'result'):
                        build_output = message.result or ""
            
            return {
                "success": build_success,
                "messages": messages,
                "files_created": files_created,
                "build_output": build_output,
                "model_used": self.model
            }
    
    async def analyze_python_code(
        self,
        python_code: str,
        project_path: Path
    ) -> Dict[str, Any]:
        """Analyze Python code structure using Claude SDK."""
        
        options = ClaudeAgentOptions(
            model=self.model,
            allowed_tools=["Read"],
            permission_mode="acceptEdits",
            cwd=str(project_path)
        )
        
        async with ClaudeSDKClient(options=options) as client:
            prompt = f"""Analyze this Python code and provide:

1. Main functions and their purposes
2. Classes and their methods
3. External dependencies used
4. Recommended Rust crates for each dependency
5. Potential conversion challenges

**Python code:**
```python
{python_code}
```

Provide a structured analysis."""
            
            await client.query(prompt)
            
            analysis_text = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            analysis_text += block.text + "\n"
            
            return {
                "success": True,
                "analysis": analysis_text
            }
    
    async def fix_rust_errors(
        self,
        rust_files: Dict[str, str],
        error_output: str,
        project_path: Path
    ) -> Dict[str, Any]:
        """Fix Rust compilation errors using Claude SDK."""
        
        options = ClaudeAgentOptions(
            model=self.model,
            allowed_tools=["Read", "Write", "Edit", "Bash"],
            permission_mode="acceptEdits",
            cwd=str(project_path)
        )
        
        async with ClaudeSDKClient(options=options) as client:
            prompt = f"""The Rust code has compilation errors. Please fix them.

**Compilation Error:**
```
{error_output}
```

**Current Files:**
{self._format_files(rust_files)}

Use the Edit or Write tools to fix the errors, then run cargo build again.
"""
            
            await client.query(prompt)
            
            fixed = False
            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    fixed = not message.is_error
            
            return {
                "success": fixed,
                "fixed": fixed
            }
    
    def _format_files(self, files: Dict[str, str]) -> str:
        """Format files for display."""
        result = ""
        for filename, content in files.items():
            result += f"\n**{filename}:**\n```\n{content[:500]}...\n```\n"
        return result


def is_claude_sdk_available() -> bool:
    """Check if Claude SDK is available."""
    try:
        import claude_agent_sdk
        return os.getenv("ANTHROPIC_API_KEY") is not None
    except ImportError:
        return False
