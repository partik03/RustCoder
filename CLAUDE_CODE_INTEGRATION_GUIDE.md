# Claude Code Integration Guide for RustCoder
## Extending RustCoder with Claude Code Agent Capabilities

**Document Purpose:** Comprehensive guide for integrating RustCoder's Python/C++ to Rust conversion capabilities with Claude Code.

**Target Audience:** LFX Mentorship participants, RustCoder contributors, Claude Code users

**Last Updated:** October 10, 2025

---

## 📋 Table of Contents

1. [Understanding Claude Code](#1-understanding-claude-code-architecture)
2. [Available Extension Methods](#2-available-extension-methods)
3. [Recommended Approach](#3-recommended-approach-for-rustcoder)
4. [Implementation Strategy](#4-detailed-implementation-strategy)
5. [Python SDK Integration](#5-python-sdk-integration-detailed)
6. [MCP Server Enhancement](#6-mcp-server-enhancement)
7. [User Experience Design](#7-user-experience-design)
8. [Testing & Validation](#8-testing--validation)
9. [Deployment & Distribution](#9-deployment--distribution)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Understanding Claude Code Architecture

### 1.1 What is Claude Code?

**Claude Code** is Anthropic's **command-line AI coding agent** - NOT a traditional IDE plugin or extension.

**Key Characteristics:**
- **CLI Tool:** Runs as a standalone command-line application
- **Written in TypeScript:** Distributed as npm package `@anthropic-ai/claude-code`
- **Agent-based:** Uses autonomous agent loop to complete complex coding tasks
- **Tool-equipped:** Has built-in tools (Bash, Read, Write, Edit, Grep, etc.)
- **Extensible via MCP:** Supports Model Context Protocol servers for custom tools

**Official Resources:**
- **GitHub:** https://github.com/anthropics/claude-code
- **Documentation:** https://docs.claude.com/en/docs/claude-code/overview
- **Python SDK:** `claude-agent-sdk` package on PyPI

### 1.2 How Claude Code Works

```
User Input (Natural Language)
        ↓
Claude Code CLI Process
        ↓
Claude AI Model (3.5 Sonnet, etc.)
        ↓
Agent Loop:
    1. Understand task
    2. Plan approach
    3. Use tools (Bash, Read, Write, Edit, etc.)
    4. Check results
    5. Repeat until task complete
        ↓
MCP Servers (External Tools)
    - Can add custom functionality
    - Invoked by Claude when needed
        ↓
Output: Modified files, executed commands, etc.
```

**Agent Autonomy:**
- Claude decides WHEN to use tools
- Claude decides WHICH tools to use
- Claude can iterate and self-correct
- Users provide high-level instructions

### 1.3 Built-in Tools

Claude Code comes with these tools out-of-the-box:

| Tool | Purpose | Example |
|------|---------|---------|
| **Bash** | Execute shell commands | Run tests, install packages |
| **Read** | Read file contents | Analyze source code |
| **Write** | Create new files | Generate boilerplate |
| **Edit** | Modify existing files | Fix bugs, refactor |
| **Grep** | Search file contents | Find function definitions |
| **Glob** | List files matching pattern | Find all `.py` files |
| **History** | View conversation history | Context retrieval |

### 1.4 Extension Mechanisms

Claude Code can be extended in these ways:

1. **MCP Servers** (Primary)
   - Add custom tools via Model Context Protocol
   - Tools are invoked by Claude, not directly by user
   - Can be standalone servers or SDK-based

2. **Python Agent SDK** (Programmatic)
   - Python library to control Claude Code programmatically
   - Create custom workflows on top of Claude
   - Maintain conversation context

3. **TypeScript API** (Advanced)
   - Direct API access to Claude Code internals
   - Requires TypeScript development
   - Most flexible but most complex

---

## 2. Available Extension Methods

### 2.1 Method 1: Standalone MCP Server (Current State)

**What we have:** RustCoder is already an MCP server!

**Architecture:**
```
User
  ↓
Claude Code CLI
  ↓
Connects to RustCoder MCP Server (port 3000)
  ↓
RustCoder Tools: generate, compile, compile_and_fix
  ↓
Claude uses tools to accomplish Rust conversion
```

**Configuration:**
```json
// ~/.claude/config.json or project-level config
{
  "mcpServers": {
    "rustcoder": {
      "command": "docker",
      "args": ["compose", "-f", "/path/to/RustCoder/docker-compose.yml", "up", "mcp-server"],
      "env": {
        "LLM_API_BASE": "...",
        "LLM_API_KEY": "..."
      }
    }
  }
}
```

**Pros:**
- ✅ **Zero refactoring:** Use existing RustCoder as-is
- ✅ **Clean separation:** RustCoder and Claude Code are independent
- ✅ **Easy maintenance:** Update either component separately
- ✅ **Works today:** No development needed

**Cons:**
- ❌ **No direct control:** Can't guide Claude's tool usage precisely
- ❌ **User must configure:** Non-trivial setup for users
- ❌ **Limited workflow:** Claude decides when to use tools
- ❌ **No Python/C++ specific tools yet:** Need to add new MCP tools

**Best For:**
- Users who already have Claude Code installed
- Quick experimentation
- Leveraging existing RustCoder functionality

---

### 2.2 Method 2: Python Agent SDK + Custom Workflows (RECOMMENDED)

**What it is:** Create a Python CLI that uses Claude Code as a backend agent.

**Architecture:**
```
User
  ↓
rustcoder CLI (our Python package)
  ↓
Python Agent SDK (ClaudeSDKClient)
  ↓
Claude Code Process (managed by SDK)
  ↓
Custom MCP Tools (defined in our code)
  ↓
Python/C++ Analysis → Rust Generation → Build → Fix
```

**Code Structure:**
```python
# Our new Python package
rustcoder-agent/
├── pyproject.toml
├── README.md
├── src/
│   └── rustcoder_agent/
│       ├── __init__.py
│       ├── cli.py              # User-facing CLI
│       ├── tools/              # MCP tool definitions
│       │   ├── __init__.py
│       │   ├── import_python.py
│       │   ├── import_cpp.py
│       │   ├── convert.py
│       │   ├── build.py
│       │   └── analyze.py
│       ├── workflows/          # Orchestration logic
│       │   ├── __init__.py
│       │   ├── python_to_rust.py
│       │   └── cpp_to_rust.py
│       ├── sdk_client.py       # ClaudeSDKClient wrapper
│       └── mcp_server.py       # MCP server factory
└── tests/
```

**Pros:**
- ✅ **Full control:** Programmatic workflow orchestration
- ✅ **Better UX:** `rustcoder convert my-project` instead of complex instructions
- ✅ **Python/C++ specific:** Can add source language analysis tools
- ✅ **Context maintained:** Conversation persists across interactions
- ✅ **Flexible:** Can add interactive mode, web UI, etc.

**Cons:**
- ❌ **New development:** Need to build Python SDK integration
- ❌ **Dependency:** Requires `claude-agent-sdk` package
- ❌ **Distribution:** Need to package and distribute Python CLI

**Best For:**
- Production-ready solution
- Users who want simple CLI experience
- Our LFX mentorship goals (Python/C++ conversion focus)

---

### 2.3 Method 3: Hybrid Approach (MCP Server + SDK)

**What it is:** Enhance existing RustCoder MCP server AND create Python SDK workflows.

**Architecture:**
```
                  User
                    ↓
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  Claude Code CLI        rustcoder CLI
  (direct usage)         (SDK-based)
        │                       │
        └───────────┬───────────┘
                    ↓
          Enhanced RustCoder MCP
          (More Python/C++ tools)
                    ↓
       Rust Generation & Compilation
```

**Pros:**
- ✅ **Best of both worlds:** Direct usage + programmatic control
- ✅ **Flexibility:** Users choose their interface
- ✅ **Reusable:** MCP server serves both use cases

**Cons:**
- ❌ **More work:** Build both MCP enhancements and SDK integration
- ❌ **Complexity:** Maintain two interfaces

**Best For:**
- Long-term solution
- Supporting diverse user needs
- Community adoption

---

### 2.4 Method 4: Fork Claude Code (NOT RECOMMENDED)

**What it is:** Fork the Claude Code repository and add features directly.

**Pros:**
- ✅ **Full control:** Can add anything
- ✅ **True slash commands:** Can add `/import-python` to CLI

**Cons:**
- ❌ **Maintenance nightmare:** Must track upstream changes
- ❌ **Distribution:** Can't use official releases
- ❌ **TypeScript required:** Need to work in TypeScript
- ❌ **User adoption:** Users prefer official tools

**Verdict:** **Avoid** unless absolutely necessary.

---

## 3. Recommended Approach for RustCoder

### 3.1 Our Decision: Python Agent SDK + Enhanced MCP

**Primary Implementation:** Python SDK-based CLI (`rustcoder-agent`)

**Secondary Support:** Enhanced standalone MCP server (for direct Claude Code usage)

### 3.2 Rationale

**Why Python SDK?**

1. **Better User Experience:**
   ```bash
   # What we want
   rustcoder convert ./my-python-project
   
   # vs. what standalone MCP requires
   claude
   > "Please use the rustcoder MCP server to convert my Python project at ./my-python-project to Rust, making sure to analyze dependencies, convert each file, build the result, and fix any errors iteratively"
   ```

2. **Programmatic Control:**
   - We can orchestrate the conversion workflow step-by-step
   - We can add pre-processing (analyze Python AST before conversion)
   - We can add post-processing (format Rust code, run Clippy)
   - We can handle errors gracefully

3. **Python/C++ Specific Tools:**
   - `import_python_project` - Analyze Python structure
   - `import_cpp_project` - Analyze C++ structure
   - `suggest_crates` - Map Python/C++ libs to Rust crates
   - `validate_conversion` - Check converted code
   - `generate_bindings` - Create PyO3/FFI scaffolding

4. **Maintains Our Python Ecosystem:**
   - RustCoder backend is Python
   - New agent SDK is Python
   - All in one language = easier development

**Why Keep MCP Server?**

1. **Power Users:** Some users want direct Claude Code control
2. **Integration:** Other tools can use our MCP server
3. **Reusability:** Same tools serve both SDK and standalone usage

### 3.3 Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     USER INTERFACES                      │
├──────────────────────────────────────────────────────────┤
│  rustcoder CLI         │  Claude Code CLI                │
│  (Python SDK-based)    │  (Direct MCP connection)        │
└───────────┬─────────────┴──────────────┬─────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│  Python Agent SDK       │   │  Cardea MCP Proxy        │
│  (ClaudeSDKClient)      │   │  (Port 3000)             │
└───────────┬─────────────┘   └─────────┬────────────────┘
            │                           │
            └────────────┬──────────────┘
                         ▼
            ┌─────────────────────────┐
            │   Enhanced RustCoder    │
            │      MCP Server         │
            ├─────────────────────────┤
            │ Existing Tools:         │
            │  - generate             │
            │  - compile              │
            │  - compile_and_fix      │
            │                         │
            │ NEW Tools:              │
            │  - import_python        │
            │  - import_cpp           │
            │  - analyze_structure    │
            │  - suggest_crates       │
            │  - create_bindings      │
            │  - validate_rust        │
            └────────────┬────────────┘
                         ▼
            ┌─────────────────────────┐
            │   RustCoder Backend     │
            │   (FastAPI + LLM)       │
            └─────────────────────────┘
```

---

## 4. Detailed Implementation Strategy

### 4.1 Phase 1: Enhance MCP Server (Week 1-2)

**Goal:** Add Python/C++ conversion tools to existing MCP server

**Tasks:**

1. **Add `import_python` tool** to `app/mcp_tools.py`:
   ```python
   @mcp.tool()
   async def import_python(project_path: str) -> str:
       """
       Import and analyze a Python project.
       Returns: JSON with file list, dependencies, structure
       """
       # Implementation
   ```

2. **Add `import_cpp` tool**:
   ```python
   @mcp.tool()
   async def import_cpp(project_path: str) -> str:
       """
       Import and analyze a C++ project.
       Returns: JSON with file list, dependencies, structure
       """
       # Implementation
   ```

3. **Add `suggest_rust_crates` tool**:
   ```python
   @mcp.tool()
   async def suggest_rust_crates(dependencies: str) -> str:
       """
       Suggest Rust crates for given Python/C++ dependencies.
       Input: JSON list of dependencies
       Returns: Mapping of source lib -> Rust crate
       """
       # Implementation
   ```

4. **Add `create_interop_bindings` tool**:
   ```python
   @mcp.tool()
   async def create_interop_bindings(
       rust_code: str,
       source_language: str
   ) -> str:
       """
       Generate PyO3 or FFI bindings for gradual migration.
       """
       # Implementation
   ```

**Deliverable:** Enhanced MCP server with 4+ new tools

---

### 4.2 Phase 2: Build Python SDK Agent (Week 3-4)

**Goal:** Create `rustcoder-agent` Python package

**Project Structure:**
```
rustcoder-agent/
├── pyproject.toml
├── README.md
├── LICENSE
├── .env.example
├── src/
│   └── rustcoder_agent/
│       ├── __init__.py
│       ├── cli.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── import_tools.py
│       │   ├── convert_tools.py
│       │   ├── build_tools.py
│       │   └── analyze_tools.py
│       ├── workflows/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── python_workflow.py
│       │   └── cpp_workflow.py
│       ├── sdk_wrapper.py
│       └── config.py
├── tests/
│   ├── test_tools.py
│   ├── test_workflows.py
│   └── test_cli.py
└── examples/
    ├── convert_python.py
    └── convert_cpp.py
```

**Key Files:**

**`pyproject.toml`:**
```toml
[project]
name = "rustcoder-agent"
version = "0.1.0"
description = "AI-powered Python/C++ to Rust conversion using Claude Code"
authors = [{name = "RustCoder Contributors"}]
license = {text = "GPLv3"}
requires-python = ">=3.10"
dependencies = [
    "claude-agent-sdk>=0.1.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]

[project.scripts]
rustcoder = "rustcoder_agent.cli:main"

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
```

**Deliverable:** Installable Python package with CLI

---

### 4.3 Phase 3: Implement Workflows (Week 5-6)

**Goal:** Create end-to-end conversion workflows

**Python to Rust Workflow:**
```python
async def python_to_rust_workflow(project_path: str):
    """
    Complete workflow for Python → Rust conversion.
    """
    # 1. Import and analyze
    analysis = await import_python_project(project_path)
    
    # 2. Create migration plan
    plan = await create_migration_plan(analysis)
    
    # 3. Convert files one by one
    for py_file in analysis.files:
        await convert_python_file(py_file)
    
    # 4. Build Rust project
    build_result = await build_rust_project()
    
    # 5. Fix errors iteratively
    if not build_result.success:
        await fix_build_errors(build_result.errors)
    
    # 6. Generate interop bindings (optional)
    if create_bindings:
        await generate_pyo3_bindings()
    
    return ConversionResult(...)
```

**Deliverable:** Working Python and C++ conversion workflows

---

### 4.4 Phase 4: Testing & Documentation (Week 7-8)

**Goal:** Ensure quality and usability

**Tasks:**

1. **Unit Tests:**
   - Test each tool function
   - Mock Claude Code responses
   - Validate tool outputs

2. **Integration Tests:**
   - Test full workflows end-to-end
   - Use real Python/C++ projects
   - Measure success rates

3. **Documentation:**
   - Installation guide
   - Usage examples
   - Troubleshooting guide
   - Architecture documentation

4. **Example Projects:**
   - Simple Python script → Rust
   - Flask app → Axum
   - C++ utility → Rust library

**Deliverable:** Production-ready package with docs

---

## 5. Python SDK Integration (Detailed)

### 5.1 Tool Definitions

**File:** `src/rustcoder_agent/tools/import_tools.py`

```python
from claude_agent_sdk import tool
from typing import Any
import os
import ast
import json

@tool(
    "import_python_project",
    "Import and analyze a Python project for Rust conversion",
    {
        "project_path": str,
        "include_tests": bool  # Optional, default True
    }
)
async def import_python_project(args: dict[str, Any]) -> dict[str, Any]:
    """
    Scans Python project and extracts:
    - File list
    - Dependencies (from requirements.txt, pyproject.toml)
    - Entry points
    - Class/function structure (via AST)
    """
    project_path = args["project_path"]
    include_tests = args.get("include_tests", True)
    
    # Validate path
    if not os.path.exists(project_path):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Path '{project_path}' does not exist"
            }],
            "is_error": True
        }
    
    # Find Python files
    python_files = []
    for root, dirs, files in os.walk(project_path):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules', '.pytest_cache'
        }]
        
        # Skip test files if requested
        if not include_tests and ('test' in root or 'tests' in root):
            continue
        
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_path)
                python_files.append({
                    "path": rel_path,
                    "full_path": full_path,
                    "size": os.path.getsize(full_path)
                })
    
    # Extract dependencies
    dependencies = []
    
    # Check requirements.txt
    req_file = os.path.join(project_path, "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse "package==version" or "package>=version"
                    dep_name = line.split('==')[0].split('>=')[0].split('~=')[0].strip()
                    dependencies.append(dep_name)
    
    # Check pyproject.toml (simplified)
    pyproject_file = os.path.join(project_path, "pyproject.toml")
    if os.path.exists(pyproject_file):
        # Could use tomli to parse, but keeping simple for now
        with open(pyproject_file) as f:
            content = f.read()
            # Very naive parsing - just look for dependencies section
            if 'dependencies' in content:
                # Would need proper TOML parsing for production
                pass
    
    # Analyze structure of first few files (AST parsing)
    structure_analysis = []
    for file_info in python_files[:5]:  # Analyze first 5 files
        try:
            with open(file_info["full_path"]) as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    classes.append({
                        "name": node.name,
                        "methods": methods
                    })
                elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                    # Top-level function
                    if not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree) if node in p.body):
                        functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            structure_analysis.append({
                "file": file_info["path"],
                "classes": classes,
                "functions": functions,
                "imports": list(set(imports))
            })
        except SyntaxError:
            # Skip files with syntax errors
            pass
    
    # Build result
    result = {
        "project_path": project_path,
        "files": python_files,
        "file_count": len(python_files),
        "total_size": sum(f["size"] for f in python_files),
        "dependencies": list(set(dependencies)),
        "structure": structure_analysis
    }
    
    # Format human-readable summary
    summary = f"""Python Project Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Project: {project_path}
📄 Files: {len(python_files)} Python files
📦 Dependencies: {len(dependencies)} packages
📏 Total Size: {sum(f['size'] for f in python_files) / 1024:.1f} KB

Top Files:
{chr(10).join(f"  • {f['path']} ({f['size'] / 1024:.1f} KB)" for f in python_files[:5])}
{'  ...' if len(python_files) > 5 else ''}

Dependencies:
{chr(10).join(f"  • {dep}" for dep in dependencies[:10])}
{'  ...' if len(dependencies) > 10 else ''}

Structure (Sample):
{chr(10).join(
    f"  • {s['file']}: {len(s['classes'])} classes, {len(s['functions'])} functions"
    for s in structure_analysis
)}
"""
    
    return {
        "content": [{
            "type": "text",
            "text": summary
        }]
    }

@tool(
    "suggest_rust_crates",
    "Suggest Rust crates for Python/C++ dependencies",
    {
        "dependencies": list,
        "source_language": str  # "python" or "cpp"
    }
)
async def suggest_rust_crates(args: dict[str, Any]) -> dict[str, Any]:
    """
    Maps common Python/C++ libraries to Rust crates.
    """
    dependencies = args["dependencies"]
    source_lang = args["source_language"]
    
    # Mapping dictionaries
    PYTHON_TO_RUST = {
        "requests": "reqwest",
        "flask": "axum, actix-web, or rocket",
        "django": "axum or actix-web (with diesel for ORM)",
        "fastapi": "axum or actix-web",
        "numpy": "ndarray",
        "pandas": "polars",
        "sqlalchemy": "diesel or sqlx",
        "pytest": "cargo test (built-in)",
        "click": "clap",
        "argparse": "clap",
        "aiohttp": "reqwest (async)",
        "pillow": "image",
        "beautifulsoup4": "scraper or select",
        "scikit-learn": "linfa",
        "matplotlib": "plotters",
        "pydantic": "serde with validation",
        "redis": "redis-rs",
        "celery": "tokio (for async tasks)",
        "jinja2": "tera or askama",
    }
    
    CPP_TO_RUST = {
        "boost": "Various (std lib covers much)",
        "qt": "qt_widgets (bindings)",
        "opencv": "opencv-rust",
        "eigen": "nalgebra",
        "protobuf": "prost",
        "grpc": "tonic",
        "gtest": "cargo test (built-in)",
        "fmt": "std::fmt (built-in)",
        "json": "serde_json",
        "yaml-cpp": "serde_yaml",
        "sqlite3": "rusqlite",
        "curl": "reqwest or curl-rust",
    }
    
    mapping = PYTHON_TO_RUST if source_lang == "python" else CPP_TO_RUST
    
    suggestions = {}
    for dep in dependencies:
        # Normalize dependency name
        dep_lower = dep.lower().replace('-', '_')
        
        if dep_lower in mapping:
            suggestions[dep] = mapping[dep_lower]
        else:
            suggestions[dep] = f"Search crates.io for '{dep}'"
    
    # Format output
    output = "Rust Crate Suggestions:\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for dep, crate in suggestions.items():
        output += f"📦 {dep}\n   → {crate}\n\n"
    
    output += "\n💡 Tip: Search https://crates.io for alternatives"
    
    return {
        "content": [{
            "type": "text",
            "text": output
        }]
    }
```

### 5.2 Workflow Implementation

**File:** `src/rustcoder_agent/workflows/python_workflow.py`

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from ..tools import import_tools, convert_tools, build_tools
from ..mcp_server import create_rustcoder_mcp
import asyncio
from typing import Optional

class PythonToRustWorkflow:
    """
    Orchestrates the complete Python → Rust conversion process.
    """
    
    def __init__(
        self,
        project_path: str,
        output_path: Optional[str] = None,
        create_bindings: bool = False,
        max_build_attempts: int = 3
    ):
        self.project_path = project_path
        self.output_path = output_path or f"{project_path}_rust"
        self.create_bindings = create_bindings
        self.max_build_attempts = max_build_attempts
        
        # Create MCP server with our tools
        self.mcp_server = create_rustcoder_mcp()
        
        # Configure Claude SDK options
        self.options = ClaudeAgentOptions(
            mcp_servers={"rustcoder": self.mcp_server},
            allowed_tools=[
                "mcp__rustcoder__import_python_project",
                "mcp__rustcoder__suggest_rust_crates",
                "mcp__rustcoder__convert_to_rust",
                "mcp__rustcoder__build_rust_project",
                "Read",  # Built-in: read files
                "Write",  # Built-in: write files
                "Edit",  # Built-in: edit files
                "Bash",  # Built-in: run commands
                "Grep",  # Built-in: search files
            ],
            permission_mode="acceptEdits",  # Auto-accept file edits
            cwd=self.output_path,
            verbose=True
        )
    
    async def run(self):
        """
        Execute the full conversion workflow.
        """
        print(f"🚀 Starting Python → Rust conversion")
        print(f"📁 Source: {self.project_path}")
        print(f"📁 Target: {self.output_path}")
        print()
        
        async with ClaudeSDKClient(options=self.options) as client:
            # Step 1: Import and analyze Python project
            print("📊 Step 1: Analyzing Python project...")
            await client.query(
                f"Use the import_python_project tool to analyze the Python project at {self.project_path}. "
                f"Provide a detailed summary of the project structure, dependencies, and complexity."
            )
            
            analysis_result = None
            async for message in client.receive_response():
                # Capture analysis results
                print(message)
                analysis_result = message
            
            # Step 2: Suggest Rust crates
            print("\n📦 Step 2: Suggesting Rust crates...")
            await client.query(
                "Based on the Python dependencies you found, use the suggest_rust_crates tool "
                "to recommend appropriate Rust crates."
            )
            
            async for message in client.receive_response():
                print(message)
            
            # Step 3: Create Rust project structure
            print("\n🏗  Step 3: Creating Rust project structure...")
            await client.query(
                f"Create a new Rust project structure at {self.output_path}. "
                f"Use 'cargo init' to initialize the project. "
                f"Update Cargo.toml with the suggested dependencies."
            )
            
            async for message in client.receive_response():
                print(message)
            
            # Step 4: Convert Python files to Rust
            print("\n🔄 Step 4: Converting Python files to Rust...")
            await client.query(
                f"For each Python file in the analysis, read the Python code, "
                f"convert it to idiomatic Rust, and write it to the appropriate location in {self.output_path}/src/. "
                f"Start with utility modules and work up to main entry points. "
                f"Use the Read tool to read Python files and Write tool to create Rust files."
            )
            
            async for message in client.receive_response():
                print(message)
            
            # Step 5: Build and fix errors
            print(f"\n🔨 Step 5: Building Rust project (max {self.max_build_attempts} attempts)...")
            
            for attempt in range(1, self.max_build_attempts + 1):
                print(f"\n  Build attempt {attempt}/{self.max_build_attempts}...")
                
                await client.query(
                    f"Navigate to {self.output_path} and run 'cargo build'. "
                    f"If there are compilation errors, analyze them and fix the Rust code. "
                    f"Use the Edit tool to make fixes."
                )
                
                build_success = False
                async for message in client.receive_response():
                    print(message)
                    # Check if build succeeded
                    if "Finished" in str(message) and "dev" in str(message):
                        build_success = True
                
                if build_success:
                    print("\n✅ Build successful!")
                    break
            else:
                print(f"\n⚠️  Build still has errors after {self.max_build_attempts} attempts")
                print("   Manual review may be needed.")
            
            # Step 6: Generate interop bindings (optional)
            if self.create_bindings:
                print("\n🔗 Step 6: Generating PyO3 bindings...")
                await client.query(
                    f"Create PyO3 bindings to allow calling the Rust code from Python. "
                    f"Add pyo3 dependency to Cargo.toml and create lib.rs with #[pymodule]."
                )
                
                async for message in client.receive_response():
                    print(message)
            
            # Step 7: Summary
            print("\n📝 Step 7: Generating conversion summary...")
            await client.query(
                "Provide a summary of the conversion: "
                "- What was converted "
                "- What challenges were encountered "
                "- What manual changes might be needed "
                "- How to build and run the Rust version"
            )
            
            async for message in client.receive_response():
                print(message)
        
        print("\n" + "="*60)
        print("✨ Conversion workflow complete!")
        print(f"📁 Rust project: {self.output_path}")
        print("="*60)
```

### 5.3 CLI Implementation

**File:** `src/rustcoder_agent/cli.py`

```python
import click
import asyncio
from pathlib import Path
from .workflows.python_workflow import PythonToRustWorkflow
from .workflows.cpp_workflow import CppToRustWorkflow

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    RustCoder Agent - AI-powered Python/C++ to Rust conversion
    
    Uses Claude Code to intelligently convert source projects to Rust.
    """
    pass

@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output directory for Rust project (default: <project>_rust)'
)
@click.option(
    '--from-lang',
    type=click.Choice(['python', 'cpp'], case_sensitive=False),
    default='python',
    help='Source language (python or cpp)'
)
@click.option(
    '--bindings/--no-bindings',
    default=False,
    help='Generate interop bindings (PyO3/FFI) for gradual migration'
)
@click.option(
    '--max-attempts',
    type=int,
    default=3,
    help='Maximum build fix attempts'
)
def convert(project_path, output, from_lang, bindings, max_attempts):
    """
    Convert a Python or C++ project to Rust.
    
    Example:
        rustcoder convert ./my-python-project
        rustcoder convert ./my-cpp-project --from-lang cpp --bindings
    """
    project_path = Path(project_path).resolve()
    
    click.echo(f"🦀 RustCoder Agent - Conversion Tool")
    click.echo(f"")
    click.echo(f"Source: {project_path}")
    click.echo(f"Language: {from_lang.upper()}")
    click.echo(f"Bindings: {'Yes' if bindings else 'No'}")
    click.echo(f"")
    
    if from_lang == 'python':
        workflow = PythonToRustWorkflow(
            project_path=str(project_path),
            output_path=output,
            create_bindings=bindings,
            max_build_attempts=max_attempts
        )
    else:
        workflow = CppToRustWorkflow(
            project_path=str(project_path),
            output_path=output,
            create_bindings=bindings,
            max_build_attempts=max_attempts
        )
    
    try:
        asyncio.run(workflow.run())
    except KeyboardInterrupt:
        click.echo("\n⚠️  Conversion interrupted by user")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        raise

@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option(
    '--from-lang',
    type=click.Choice(['python', 'cpp'], case_sensitive=False),
    required=True,
    help='Source language'
)
def analyze(project_path, from_lang):
    """
    Analyze a project and suggest conversion strategy (no conversion).
    
    Example:
        rustcoder analyze ./my-project --from-lang python
    """
    click.echo(f"📊 Analyzing {from_lang.upper()} project: {project_path}")
    click.echo("(Analysis feature coming soon)")

@cli.command()
def chat():
    """
    Start an interactive conversation with Claude about Rust conversion.
    
    Example:
        rustcoder chat
    """
    click.echo("💬 Interactive chat mode")
    click.echo("(Chat feature coming soon)")

def main():
    cli()

if __name__ == '__main__':
    main()
```

---

## 6. MCP Server Enhancement

### 6.1 New Tools to Add

**File:** `app/mcp_tools.py` (additions)

```python
# Add after existing tools (line 136+)

@mcp.tool()
async def import_python(project_path: str, include_tests: bool = True) -> str:
    """
    Import and analyze a Python project for Rust conversion.
    
    Returns JSON with:
    - File list
    - Dependencies
    - Project structure (classes, functions)
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/import-python",
            json={'project_path': project_path, 'include_tests': include_tests}
        )
        response.raise_for_status()
        return response.text

@mcp.tool()
async def import_cpp(project_path: str) -> str:
    """
    Import and analyze a C++ project for Rust conversion.
    
    Returns JSON with:
    - File list (.h, .cpp, .hpp)
    - Build system (CMake, Make)
    - Dependencies
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/import-cpp",
            json={'project_path': project_path}
        )
        response.raise_for_status()
        return response.text

@mcp.tool()
async def suggest_crates(
    dependencies: str,
    source_language: str
) -> str:
    """
    Suggest Rust crates for given Python/C++ dependencies.
    
    Args:
        dependencies: JSON list of dependency names
        source_language: "python" or "cpp"
    
    Returns:
        Mapping of source lib -> Rust crate recommendations
    """
    import json
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/suggest-crates",
            json={
                'dependencies': json.loads(dependencies),
                'source_language': source_language
            }
        )
        response.raise_for_status()
        return response.text

@mcp.tool()
async def create_bindings(
    rust_code: str,
    source_language: str,
    binding_type: str = "pyo3"
) -> str:
    """
    Generate interop bindings (PyO3/FFI) for Rust code.
    
    Args:
        rust_code: Rust code to create bindings for
        source_language: "python" or "cpp"
        binding_type: "pyo3" for Python, "ffi" for C++
    
    Returns:
        Generated binding code
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/create-bindings",
            json={
                'rust_code': rust_code,
                'source_language': source_language,
                'binding_type': binding_type
            }
        )
        response.raise_for_status()
        return response.text
```

### 6.2 Backend Endpoints to Add

**File:** `app/main.py` (additions)

```python
# Add after line 725

@app.post("/import-python")
async def import_python_project(request: dict):
    """
    Import and analyze a Python project.
    
    Args:
        project_path (str): Path to Python project
        include_tests (bool): Whether to include test files
    
    Returns:
        JSON with project analysis
    """
    from app.code_analyzer import PythonAnalyzer
    
    project_path = request.get("project_path")
    include_tests = request.get("include_tests", True)
    
    if not project_path:
        raise HTTPException(status_code=400, detail="project_path required")
    
    analyzer = PythonAnalyzer()
    analysis = analyzer.analyze(project_path, include_tests=include_tests)
    
    return JSONResponse(content=analysis)

@app.post("/import-cpp")
async def import_cpp_project(request: dict):
    """
    Import and analyze a C++ project.
    """
    from app.code_analyzer import CppAnalyzer
    
    project_path = request.get("project_path")
    
    if not project_path:
        raise HTTPException(status_code=400, detail="project_path required")
    
    analyzer = CppAnalyzer()
    analysis = analyzer.analyze(project_path)
    
    return JSONResponse(content=analysis)

@app.post("/suggest-crates")
async def suggest_rust_crates(request: dict):
    """
    Suggest Rust crates for Python/C++ dependencies.
    """
    from app.crate_mapper import CrateMapper
    
    dependencies = request.get("dependencies", [])
    source_language = request.get("source_language", "python")
    
    mapper = CrateMapper()
    suggestions = mapper.suggest(dependencies, source_language)
    
    return JSONResponse(content=suggestions)

@app.post("/create-bindings")
async def create_interop_bindings(request: dict):
    """
    Generate PyO3/FFI bindings for Rust code.
    """
    from app.binding_generator import BindingGenerator
    
    rust_code = request.get("rust_code")
    source_language = request.get("source_language")
    binding_type = request.get("binding_type", "pyo3")
    
    if not rust_code:
        raise HTTPException(status_code=400, detail="rust_code required")
    
    generator = BindingGenerator()
    bindings = generator.generate(rust_code, source_language, binding_type)
    
    return JSONResponse(content={"bindings": bindings})
```

---

## 7. User Experience Design

### 7.1 Installation

**For Python SDK Approach:**

```bash
# Install rustcoder-agent
pip install rustcoder-agent

# Verify installation
rustcoder --version
```

**For Standalone MCP Approach:**

```bash
# Clone RustCoder
git clone https://github.com/YOUR_USERNAME/RustCoder.git
cd RustCoder

# Start MCP server
docker-compose up -d mcp-server

# Configure Claude Code
cat > ~/.claude/mcp-config.json << EOF
{
  "mcpServers": {
    "rustcoder": {
      "url": "http://localhost:3000"
    }
  }
}
EOF
```

### 7.2 Usage Examples

**Example 1: Convert Simple Python Script**

```bash
$ rustcoder convert my_script.py

🦀 RustCoder Agent - Conversion Tool

Source: /home/user/my_script.py
Language: PYTHON
Bindings: No

🚀 Starting Python → Rust conversion
📁 Source: /home/user/my_script.py
📁 Target: /home/user/my_script_rust

📊 Step 1: Analyzing Python project...
Python Project Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Project: /home/user
📄 Files: 1 Python file
📦 Dependencies: 0 packages

🔄 Step 4: Converting Python files to Rust...
Converting: my_script.py → src/main.rs

🔨 Step 5: Building Rust project...
  Build attempt 1/3...
✅ Build successful!

✨ Conversion workflow complete!
📁 Rust project: /home/user/my_script_rust
```

**Example 2: Convert Flask App with Bindings**

```bash
$ rustcoder convert ./flask-api --bindings

🚀 Starting Python → Rust conversion
📁 Source: /home/user/flask-api
📁 Target: /home/user/flask-api_rust

📊 Step 1: Analyzing Python project...
Python Project Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Project: /home/user/flask-api
📄 Files: 5 Python files
📦 Dependencies: 3 packages
  • flask
  • sqlalchemy
  • marshmallow

📦 Step 2: Suggesting Rust crates...
Rust Crate Suggestions:
━━━━━━━━━━━━━━━━━━━━━━━
📦 flask
   → axum, actix-web, or rocket

📦 sqlalchemy
   → diesel or sqlx

📦 marshmallow
   → serde with validation

🔄 Step 4: Converting Python files to Rust...
  • app.py → src/main.rs
  • models.py → src/models.rs
  • routes.py → src/routes.rs

🔨 Step 5: Building Rust project...
✅ Build successful!

🔗 Step 6: Generating PyO3 bindings...
  Creating lib.rs with #[pymodule]...
  ✅ Bindings generated

✨ Conversion complete!
```

### 7.3 Interactive Mode (Future)

```bash
$ rustcoder chat

💬 RustCoder Agent - Interactive Mode

Type your questions or commands. Examples:
  • "Convert my Flask app"
  • "Analyze my Python project"
  • "What Rust crates should I use for numpy?"
  • "exit" to quit

You> I have a Flask app that uses SQLAlchemy. What's the best way to convert it?

Claude> I'd recommend converting to Axum for the web framework and Diesel 
for the ORM. Here's my suggested approach:

1. Web Layer: Flask → Axum
   - Flask routes become Axum handlers
   - Flask blueprints become Axum routers
   - Middleware stays similar

2. Database: SQLAlchemy → Diesel
   - Models become Diesel schema
   - Queries become Diesel DSL
   - Migrations use diesel_migrations

3. Serialization: Flask-Marshmallow → Serde
   - Schemas become Rust structs with #[derive(Serialize, Deserialize)]

Would you like me to convert your project now, or would you prefer to see 
code examples first?

You> Convert it, and create PyO3 bindings so I can migrate gradually

Claude> Great! I'll start the conversion with PyO3 bindings...

[Conversion proceeds...]
```

---

## 8. Testing & Validation

### 8.1 Unit Tests

**File:** `tests/test_tools.py`

```python
import pytest
from rustcoder_agent.tools.import_tools import import_python_project

@pytest.mark.asyncio
async def test_import_python_project():
    """Test Python project import tool."""
    result = await import_python_project({
        "project_path": "./test_data/simple_py_project",
        "include_tests": True
    })
    
    assert "content" in result
    assert len(result["content"]) > 0
    # More assertions...

@pytest.mark.asyncio
async def test_suggest_rust_crates():
    """Test crate suggestion tool."""
    from rustcoder_agent.tools.import_tools import suggest_rust_crates
    
    result = await suggest_rust_crates({
        "dependencies": ["requests", "flask", "numpy"],
        "source_language": "python"
    })
    
    text = result["content"][0]["text"]
    assert "reqwest" in text
    assert "axum" in text or "actix-web" in text
    assert "ndarray" in text
```

### 8.2 Integration Tests

**File:** `tests/test_workflows.py`

```python
import pytest
from rustcoder_agent.workflows.python_workflow import PythonToRustWorkflow
import tempfile
import shutil

@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_python_conversion():
    """Test conversion of a simple Python script."""
    # Create test Python file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = f"{tmpdir}/hello.py"
        with open(test_file, 'w') as f:
            f.write("def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()\n")
        
        # Run conversion
        workflow = PythonToRustWorkflow(
            project_path=tmpdir,
            output_path=f"{tmpdir}_rust",
            max_build_attempts=1
        )
        
        await workflow.run()
        
        # Verify Rust project was created
        assert (Path(f"{tmpdir}_rust") / "Cargo.toml").exists()
        assert (Path(f"{tmpdir}_rust") / "src" / "main.rs").exists()
        
        # Cleanup
        shutil.rmtree(f"{tmpdir}_rust")
```

### 8.3 Example Projects for Testing

**Create test suite:**

```
tests/test_projects/
├── simple_python/
│   └── hello.py          # Simple script
├── flask_api/
│   ├── app.py            # Flask app
│   ├── models.py
│   └── requirements.txt
├── cli_tool/
│   ├── main.py           # Click-based CLI
│   └── utils.py
└── cpp_utility/
    ├── main.cpp
    ├── utils.cpp
    └── utils.h
```

---

## 9. Deployment & Distribution

### 9.1 Python Package Distribution

**Publish to PyPI:**

```bash
# Build package
python -m build

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ rustcoder-agent

# Upload to PyPI
python -m twine upload dist/*
```

### 9.2 Docker Distribution

**Dockerfile for agent:**

```dockerfile
FROM python:3.11-slim

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install rustcoder-agent
RUN pip install rustcoder-agent

# Set up working directory
WORKDIR /workspace

ENTRYPOINT ["rustcoder"]
```

**Docker Compose for full stack:**

```yaml
version: '3.8'

services:
  rustcoder-mcp:
    build: ./RustCoder
    ports:
      - "3000:3000"
    environment:
      - LLM_API_BASE=...
      - LLM_API_KEY=...
  
  rustcoder-agent:
    build: ./rustcoder-agent
    volumes:
      - ./projects:/workspace
    depends_on:
      - rustcoder-mcp
```

### 9.3 Documentation Site

**Structure:**

```
docs/
├── index.md              # Home
├── installation.md       # Installation guide
├── quickstart.md         # 5-minute tutorial
├── guides/
│   ├── python-to-rust.md
│   ├── cpp-to-rust.md
│   └── bindings.md
├── api/
│   ├── cli.md
│   ├── mcp-tools.md
│   └── sdk.md
└── examples/
    ├── flask-to-axum.md
    ├── cli-tool.md
    └── library.md
```

---

## 10. Troubleshooting

### 10.1 Common Issues

**Issue: "claude-agent-sdk not found"**

```bash
# Solution: Install SDK
pip install claude-agent-sdk
```

**Issue: "MCP server connection refused"**

```bash
# Check if MCP server is running
docker ps | grep rustcoder

# Restart MCP server
cd RustCoder
docker-compose restart mcp-server

# Check logs
docker-compose logs mcp-server
```

**Issue: "Build fails with cargo error"**

```bash
# Verify Rust is installed
rustc --version
cargo --version

# If not installed:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Issue: "Conversion takes too long"**

- Start with smaller projects
- Use `--max-attempts 1` to limit fix iterations
- Check LLM API rate limits

### 10.2 Debug Mode

**Enable verbose logging:**

```bash
export RUSTCODER_DEBUG=1
rustcoder convert ./project
```

**Check SDK logs:**

```python
# In workflow
self.options = ClaudeAgentOptions(
    verbose=True,  # Enable SDK logging
    # ...
)
```

---

## 11. Appendix

### 11.1 Complete Example: Flask to Axum

**Input: Flask App**

```python
# app.py
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/hello/<name>')
def hello(name):
    return jsonify({"message": f"Hello, {name}!"})

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    # Process user creation
    return jsonify({"id": 1, "name": data["name"]}), 201

if __name__ == '__main__':
    app.run(debug=True)
```

**Command:**

```bash
rustcoder convert ./flask-app
```

**Output: Axum App**

```rust
// src/main.rs
use axum::{
    extract::{Path, Json},
    http::StatusCode,
    response::Json as ResponseJson,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct HelloResponse {
    message: String,
}

#[derive(Deserialize)]
struct CreateUserRequest {
    name: String,
}

#[derive(Serialize)]
struct UserResponse {
    id: u32,
    name: String,
}

async fn hello(Path(name): Path<String>) -> ResponseJson<HelloResponse> {
    ResponseJson(HelloResponse {
        message: format!("Hello, {}!", name),
    })
}

async fn create_user(
    Json(payload): Json<CreateUserRequest>,
) -> (StatusCode, ResponseJson<UserResponse>) {
    // Process user creation
    (
        StatusCode::CREATED,
        ResponseJson(UserResponse {
            id: 1,
            name: payload.name,
        }),
    )
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/hello/:name", get(hello))
        .route("/api/users", post(create_user));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    
    println!("Server running on http://localhost:3000");
    
    axum::serve(listener, app).await.unwrap();
}
```

### 11.2 Resources

**Official Documentation:**
- Claude Code: https://docs.claude.com/en/docs/claude-code/overview
- Python SDK: https://github.com/anthropics/claude-code
- MCP Spec: https://modelcontextprotocol.io/

**Rust Resources:**
- PyO3 Guide: https://pyo3.rs/
- Rust FFI: https://doc.rust-lang.org/nomicon/ffi.html
- Axum Web Framework: https://github.com/tokio-rs/axum
- Diesel ORM: https://diesel.rs/

**Community:**
- RustCoder Discord: [TBD]
- GitHub Discussions: https://github.com/YOUR_USERNAME/RustCoder/discussions

---

## 12. Conclusion

This guide provides a comprehensive strategy for integrating RustCoder with Claude Code using the **Python Agent SDK approach**. This approach offers:

1. ✅ **Best User Experience:** Simple CLI (`rustcoder convert project`)
2. ✅ **Full Control:** Programmatic workflow orchestration
3. ✅ **Extensibility:** Easy to add Python/C++ specific features
4. ✅ **Maintainability:** Clean separation of concerns
5. ✅ **Production Ready:** Testable, documentable, distributable

**Next Steps:**
1. Implement Phase 1 (MCP Server enhancements)
2. Build Phase 2 (Python SDK agent)
3. Test with real projects
4. Document and release

---

**Document Version:** 1.0  
**Last Updated:** October 10, 2025  
**Authors:** RustCoder Contributors (LFX Mentorship)  
**License:** GPLv3

