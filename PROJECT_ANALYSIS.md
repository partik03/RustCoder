# RustCoder Technical Architecture
## Deep Technical Analysis for Claude Code Integration

**Document Purpose:** Detailed technical analysis of RustCoder's architecture to plan Claude Code integration for Python/C++ to Rust conversion workflows.

**Important Note:** ⚠️ RustCoder is a **Python-based project**, not TypeScript! Uses FastAPI + FastMCP, not a Node.js MCP server.

---

## 1. MCP Server Implementation

### Core Protocol Files

**Primary MCP Server:**
- **File:** `app/mcp_tools.py` (143 lines)
- **Framework:** FastMCP (Python MCP SDK)
- **Transport:** STDIO (wrapped by Cardea proxy for SSE/HTTP)
- **Port:** 3000 (when proxied via Cardea)

**Support Files:**
- **File:** `app/main.py` (770 lines) - REST API that MCP tools call internally
- **File:** `docker-compose.yml` - Defines MCP server container with Cardea wrapper

### MCP Library Used

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Rust compiler tools")
```

**FastMCP Features:**
- Simple decorator-based tool registration: `@mcp.tool()`
- Automatic type validation from function signatures
- Built-in async support
- SSE transport when wrapped with Cardea proxy

### Tool Registration Process

**How Tools Are Registered:**

1. **Create FastMCP instance** with server name:
   ```python
   mcp = FastMCP("Rust compiler tools")
   ```

2. **Define tool as async function** with type hints:
   ```python
   @mcp.tool()
   async def generate(description: str, requirements: str) -> str:
       """Docstring becomes tool description"""
       # implementation
   ```

3. **Run MCP server** with transport mode:
   ```python
   mcp.run(transport=transport)  # stdio or sse
   ```

**Tool Discovery:**
- Tools are auto-discovered via decorator
- Function signature defines parameters
- Docstring defines tool description
- Type hints enable validation

### Communication Flow

```
Claude Desktop / MCP Client
         ↓
    [STDIO/SSE Protocol]
         ↓
Cardea Proxy (Port 3000) ← Docker wrapper
         ↓
    [STDIO Transport]
         ↓
FastMCP Server (app/mcp_tools.py)
         ↓
    [Tool Router - Decorator-based]
         ↓
Tool Function (generate/compile/compile_and_fix)
         ↓
    [HTTP Request via httpx]
         ↓
FastAPI Server (app/main.py) - Port 8000
         ↓
    [Business Logic]
    - LLM Client (llm_client.py)
    - Compiler Wrapper (compiler.py)
    - Response Parser (response_parser.py)
    - Vector Store (vector_store.py)
         ↓
External Services:
    - LLM API (Gaia/OpenAI-compatible)
    - Qdrant Vector DB
    - Rust Cargo/Rustc
         ↓
Response flows back up the chain
         ↓
Returns to Claude Desktop
```

**Key Insight:** MCP tools are **thin wrappers** around REST API endpoints. The MCP server doesn't contain business logic - it forwards requests to the FastAPI server.

---

## 2. Existing MCP Tools

### Tool 1: `generate`

**File:** `app/mcp_tools.py` (lines 19-58)

**Function Signature:**
```python
async def generate(description: str, requirements: str) -> str
```

**Purpose:** Generate a new Rust cargo project from description and requirements

**Input Parameters:**
- `description` (str): Text description of the Rust project
- `requirements` (str): Functional requirements for the project

**Output Format:**
Multi-file text format with `[filename: path]` markers:
```
[filename: Cargo.toml]
[package]
name = "project"
...

[filename: src/main.rs]
fn main() { ... }
```

**Implementation:**
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(
        f"{API_BASE_URL}/generate-sync",
        json={'description': description, 'requirements': requirements}
    )
    resp_json = json.loads(response.text)
    return resp_json["combined_text"]
```

**Backend Endpoint:** `POST /generate-sync` (app/main.py, lines 541-725)

**Backend Workflow:**
1. Optional vector search for similar projects
2. Generate prompt with template
3. Call LLM API with system message
4. Parse LLM response into files
5. Write files to temp directory
6. Compile with cargo
7. If errors, attempt auto-fix (1 iteration)
8. Return combined text format

**Example Usage:**
```bash
cmcp http://localhost:3000 tools/call name=generate \
  arguments:='{"description": "CLI calculator", "requirements": "Support +,-,*,/"}'
```

---

### Tool 2: `compile_and_fix`

**File:** `app/mcp_tools.py` (lines 59-98)

**Function Signature:**
```python
async def compile_and_fix(
    code: str, 
    description: str = "A Rust project", 
    max_attempts: int = 3
) -> str
```

**Purpose:** Compile Rust code and iteratively fix compilation errors using AI

**Input Parameters:**
- `code` (str): Multi-file Rust project in text format
- `description` (str, optional): Project description for context (default: "A Rust project")
- `max_attempts` (int, optional): Maximum fix iterations (default: 3)

**Output Format:**
Same multi-file text format as input, but with fixes applied

**Implementation:**
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(
        f"{API_BASE_URL}/compile-and-fix",
        json={'code': code, 'description': description, 'max_attempts': max_attempts}
    )
    resp_json = json.loads(response.text)
    return resp_json["combined_text"]
```

**Backend Endpoint:** `POST /compile-and-fix` (app/main.py, lines 168-312)

**Backend Workflow:**
1. Parse multi-file text into separate files
2. Write files to temp directory
3. **Attempt compilation loop** (up to max_attempts):
   - Run `cargo build`
   - If success: Return fixed code
   - If error:
     - Extract error context
     - Optional vector search for similar errors
     - Build fix prompt with error + context
     - Call LLM to generate fix
     - Apply fixes to files
     - Retry compilation
4. Return result (success or failure after max attempts)

**Example Usage:**
```bash
cmcp http://localhost:3000 tools/call name=compile_and_fix \
  arguments:='{"code": "[filename: src/main.rs]\nfn main() { print!(\"hello\") }", "max_attempts": 5}'
```

---

### Tool 3: `compile`

**File:** `app/mcp_tools.py` (lines 100-136)

**Function Signature:**
```python
async def compile(code: str) -> str
```

**Purpose:** Compile Rust code and return compiler output (no auto-fixing)

**Input Parameters:**
- `code` (str): Multi-file Rust project in text format

**Output Format:**
Compiler output string (success message or error details)

**Implementation:**
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(
        f"{API_BASE_URL}/compile",
        json={'code': code}
    )
    resp_json = json.loads(response.text)
    return resp_json["build_output"]
```

**Backend Endpoint:** `POST /compile` (app/main.py, lines 128-166)

**Backend Workflow:**
1. Parse multi-file text into files
2. Write to temp directory
3. Run `cargo build`
4. If success: Try `cargo run` and return output
5. If error: Return error details
6. **No fixing attempted** - just returns compilation result

**Example Usage:**
```bash
cmcp http://localhost:3000 tools/call name=compile \
  arguments:='{"code": "[filename: Cargo.toml]\n...\n[filename: src/main.rs]\n..."}'
```

---

### Summary of MCP Tools

| Tool | Purpose | Auto-Fix | LLM Called | Vector Search |
|------|---------|----------|------------|---------------|
| `generate` | Create new project | Yes (1x) | Yes | Optional |
| `compile_and_fix` | Fix errors iteratively | Yes (Nx) | Yes | Optional |
| `compile` | Just compile | No | No | No |

**Key Observations:**
- All tools use multi-file text format (not filesystem operations)
- Tools are async and use httpx for HTTP calls
- Tools forward to REST API - no business logic in MCP layer
- Error handling wraps HTTP errors in try/except

---

## 3. AI/LLM Integration

### Current LLM Setup

**Provider:** OpenAI-compatible API (flexible)
- **Default:** Gaia nodes (distributed LLM network)
- **Supports:** Any OpenAI-compatible endpoint (local LLMs, etc.)

**Model Configuration:**
- **Text Generation:** `LLM_MODEL` env var (default: `Qwen2.5-Coder-3B-Instruct`)
- **Embeddings:** `LLM_EMBED_MODEL` env var (default: `nomic-embed`)
- **Embedding Size:** `LLM_EMBED_SIZE` env var (default: 1536, but 768 for Gaia)

**Integration File:** `app/llm_client.py` (191 lines)

**Key Class:**
```python
class LlamaEdgeClient:
    def __init__(self, api_key=None, api_base=None, model=None, embed_model=None)
    def generate_text(prompt: str, system_message: str, max_tokens: int, temperature: float) -> str
    def get_embeddings(texts: List[str]) -> List[List[float]]
```

**Client Initialization:**
```python
from openai import OpenAI

self.client = OpenAI(
    api_key=api_key_to_use,
    base_url=self.base_url  # Custom base URL for non-OpenAI providers
)
```

**Fallback Mechanism:**
- If LLM API fails, returns hardcoded templates
- If embedding API fails, uses hash-based pseudo-embeddings
- Ensures system never crashes due to API issues

---

### Prompt System

**Prompt Location:**

1. **Template File:** `templates/project_prompts.txt` (17 lines)
   - Basic template with placeholders: `$project_description`, `$additional_requirements`
   - Uses chat format tags: `<|im_start|>`, `<|im_end|>`

2. **Hardcoded in Code:** `app/prompt_generator.py` (70 lines)
   - Class: `PromptGenerator`
   - Method: `generate_prompt(description, requirements)`
   - Has default template if file not found

3. **Enhanced System Messages:** `app/llm_client.py` (lines 46-60)
   - Adds explicit formatting instructions
   - Enforces `[filename: ...]` format
   - Embedded in every LLM call

**System Message for Generation:**
```python
enhanced_system_message = f"""
You are an expert Rust developer. Create a complete, working Rust project.
Always include at minimum these files: Cargo.toml, src/main.rs, and README.md.
For Cargo.toml, include proper dependencies and metadata.
Format your response with clear file headers like:

[filename: Cargo.toml]
<cargo toml content>

[filename: src/main.rs]
<rust code content>

[filename: README.md]
<readme content>

Do not include explanations outside of these file blocks.
"""
```

**System Message for Fixing:**
```python
fix_prompt = f"""
Here is a Rust project that failed to compile. Help me fix the compilation errors.

Project description: {description}

Compilation error:
{error_context["full_error"]}

{fix_examples}  # From vector search if available

Please provide the fixed code for all affected files.
"""
```

**Prompt Templates:**
- **Tool Instructions:** `app/prompt_generator.py` (lines 45-58)
  - Explains vector database query functions
  - Not currently used (would be for LLM tool calling)
- **Project Generation:** `app/prompt_generator.py` (lines 61-69)
  - Basic project creation prompt
  - Includes description and requirements

**Key Insight:** Prompts are relatively simple. The main sophistication comes from:
1. System message enforcing file format
2. Vector search providing examples
3. Iterative error fixing loop

---

### Vector Search / RAG Implementation

**Purpose:** Retrieval-Augmented Generation for better code quality

**Collections:**
- `project_examples` - Example Rust projects (4 examples)
- `error_examples` - Compiler error solutions (5 examples)

**Integration Points:**

1. **Project Generation** (`app/main.py`, lines 338-346, 564-573):
   ```python
   query_embedding = llm_client.get_embeddings([description])[0]
   similar_projects = vector_store.search("project_examples", query_embedding, limit=1)
   if similar_projects:
       example_text = f"\nHere's a similar project you can use as reference:\n{similar_projects[0]['example']}"
       # Append to requirements
   ```

2. **Error Fixing** (`app/main.py`, lines 251-262, 426-438):
   ```python
   error_embedding = llm_client.get_embeddings([error_context["full_error"]])[0]
   similar_errors = vector_store.search("error_examples", error_embedding, limit=3)
   fix_examples = ""
   for i, err in enumerate(similar_errors):
       fix_examples += f"Example {i+1}:\n{err['error']}\nFix: {err['solution']}\n\n"
   # Include in fix prompt
   ```

**Vector Search Tool (Not Used):**
- **File:** `app/llm_tools.py` (45 lines)
- **Class:** `VectorStoreQueryTool`
- **Method:** `query_examples(query, collection, limit)`
- **Status:** Defined but NOT exposed to LLM
- **Potential:** Could enable LLM to dynamically query examples

**Data Loading:**
- **Script:** `app/load_data.py` (62 lines)
- **Functions:** `load_project_examples()`, `load_error_examples()`
- **Trigger:** Auto-loads on startup if collections empty (app/main.py, lines 58-61)
- **Format:** JSON files in `data/project_examples/` and `data/error_examples/`

---

### Response Processing

**Parser File:** `app/response_parser.py` (145 lines)

**Key Class:**
```python
class ResponseParser:
    def parse_response(response: str) -> Dict[str, str]
    def write_files(files: Dict[str, str], project_dir: str) -> List[str]
```

**Parsing Strategy (Multi-level Fallback):**

1. **Level 1:** Extract using `[filename: ...]` markers (regex)
   ```python
   file_blocks = re.findall(r'\[filename:\s*(.*?)\](.*?)(?=\[filename:|$)', response, re.DOTALL)
   ```

2. **Level 2:** Find code blocks by content patterns
   - Look for `[package]` + `name =` → Cargo.toml
   - Look for `fn main()` → src/main.rs
   - Look for `# ` at start → README.md

3. **Level 3:** Aggressive section extraction
   - Split on file name mentions
   - Extract content between markers

4. **Level 4:** Create default files if nothing found
   ```python
   if not files.get("Cargo.toml"):
       files["Cargo.toml"] = """[package]\nname = "rust_project"\n..."""
   if not files.get("src/main.rs"):
       files["src/main.rs"] = """fn main() {\n    println!("Hello, world!");\n}"""
   ```

**Cleaning Operations:**
- Remove triple backticks and language identifiers
- Remove common language identifier files ("toml", "rust", etc.)
- Normalize file paths (OS-specific separators)
- Create directories as needed

**Key Insight:** Parser is extremely robust with multiple fallback strategies. This defensive approach ensures the system always produces valid files even if LLM output is malformed.

---

## 4. Data Flow Diagram

### Complete Request Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    1. CLIENT REQUEST                             │
│  Claude Desktop / MCP Client / CLI / HTTP Request                │
└──────────────────────┬───────────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐
│   2a. MCP ROUTE      │  │   2b. REST ROUTE     │
│   Port 3000 (SSE)    │  │   Port 8000 (HTTP)   │
│   app/mcp_tools.py   │  │   app/main.py        │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           │ HTTP POST               │ Direct call
           │ via httpx               │
           │                         │
           └────────────┬────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   3. ENDPOINT HANDLER          │
        │   FastAPI route in main.py     │
        │   - /generate-sync             │
        │   - /compile                   │
        │   - /compile-and-fix           │
        └───────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────────┐         ┌────────────────────┐
│ 4a. VECTOR SEARCH │         │ 4b. SKIP (compile) │
│ (if enabled)      │         │                    │
│ vector_store.py   │         └────────────────────┘
└────────┬──────────┘
         │ Get similar examples
         ▼
┌────────────────────────────┐
│  5. PROMPT GENERATION      │
│  prompt_generator.py       │
│  + System message          │
│  + User description        │
│  + Vector search results   │
└───────────┬────────────────┘
            │
            ▼
┌────────────────────────────┐
│  6. LLM API CALL           │
│  llm_client.py             │
│  → OpenAI-compatible API   │
│  ← Generated code response │
└───────────┬────────────────┘
            │
            ▼
┌────────────────────────────┐
│  7. RESPONSE PARSING       │
│  response_parser.py        │
│  Extract files from text   │
│  [filename: ...] markers   │
└───────────┬────────────────┘
            │
            ▼
┌────────────────────────────┐
│  8. FILE WRITING           │
│  Write to temp directory   │
│  or output/{project_id}/   │
└───────────┬────────────────┘
            │
            ▼
┌────────────────────────────┐
│  9. RUST COMPILATION       │
│  compiler.py               │
│  cargo build & cargo run   │
└───────────┬────────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌─────────┐    ┌──────────────────────────┐
│SUCCESS  │    │  ERROR - FIX LOOP        │
└────┬────┘    │  (compile-and-fix only)  │
     │         └────────┬─────────────────┘
     │                  │
     │         ┌────────┴────────┐
     │         ▼                 │
     │    ┌─────────────────────────────┐
     │    │ 10. ERROR ANALYSIS          │
     │    │ compiler.extract_error()    │
     │    └────────┬────────────────────┘
     │             │
     │             ▼
     │    ┌─────────────────────────────┐
     │    │ 11. VECTOR SEARCH (errors)  │
     │    │ Find similar error solutions│
     │    └────────┬────────────────────┘
     │             │
     │             ▼
     │    ┌─────────────────────────────┐
     │    │ 12. FIX PROMPT + LLM CALL   │
     │    │ Include error + examples    │
     │    └────────┬────────────────────┘
     │             │
     │             ▼
     │    ┌─────────────────────────────┐
     │    │ 13. APPLY FIXES             │
     │    │ Update files in temp dir    │
     │    └────────┬────────────────────┘
     │             │
     │             └────────┬ Retry (max_attempts)
     │                      │
     └──────────────────────┘
                 │
                 ▼
┌────────────────────────────────────┐
│  14. FORMAT RESPONSE               │
│  - Combined text format            │
│  - JSON with files dict            │
│  - Build/run output                │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│  15. RETURN TO CLIENT              │
│  Via MCP protocol or HTTP response │
└────────────────────────────────────┘
```

### Key Flow Characteristics

**Synchronous Path:**
- `/generate-sync` and `/compile*` endpoints
- Client waits for full completion
- Suitable for MCP tools (Claude expects response)

**Asynchronous Path:**
- `/generate` endpoint (not used by MCP)
- Returns project_id immediately
- Client polls `/project/{id}` for status
- Results stored in `output/{project_id}/`

**Error Handling:**
- Try/except at every external call
- Fallbacks for LLM and vector search failures
- Never crashes - always returns something

---

## 5. File-by-File Analysis

### app/main.py (770 lines)
**Purpose:** FastAPI REST API server - core business logic

**Key Functions:**

1. **`generate_project(request, background_tasks)`** (lines 92-113)
   - Async project generation
   - Returns project_id
   - Actual work done in background task

2. **`generate_project_sync(request)`** (lines 541-725)
   - Synchronous project generation
   - Used by MCP `generate` tool
   - Waits for completion
   - Returns combined_text format

3. **`compile_rust(request)`** (lines 128-166)
   - Compile Rust code without fixing
   - Used by MCP `compile` tool
   - Returns build/run output

4. **`compile_and_fix_rust(request)`** (lines 168-312)
   - Compile with iterative fixing
   - Used by MCP `compile_and_fix` tool
   - Loops up to max_attempts
   - Returns fixed code or failure

5. **`handle_project_generation(...)`** (lines 314-490)
   - Background task for async generation
   - Does actual generation work
   - Updates status.json file

6. **`get_project_status(project_id)`** (lines 115-126)
   - Check async project status
   - Reads status.json

7. **`get_project_file(project_id, file_path)`** (lines 499-512)
   - Get specific file from project
   - Returns file contents

8. **`download_project(project_id)`** (lines 514-537)
   - Create ZIP of project
   - Return as download

**Imports:**
- FastAPI, BackgroundTasks, HTTPException
- All app modules (compiler, llm_client, etc.)
- tempfile, uuid, json, os

**Configuration:**
```python
class AppConfig:
    api_key = os.getenv("LLM_API_KEY")
    skip_vector_search = os.getenv("SKIP_VECTOR_SEARCH") == "true"
    embed_size = int(os.getenv("LLM_EMBED_SIZE", "1536"))
```

**Extension Points for Our Goals:**

1. **Add new endpoint:** `POST /convert-python` or `/convert-cpp`
   - Similar to `/generate-sync` but takes source code as input
   - Would analyze Python/C++ code
   - Generate equivalent Rust code
   - Compile and fix

2. **Extend `generate_project_sync`:**
   - Add `source_language` parameter
   - Add `source_code` parameter
   - Change prompt generation based on language

3. **Add new helper functions:**
   - `analyze_python_code(code: str)`
   - `analyze_cpp_code(code: str)`
   - `generate_conversion_prompt(source_code, source_lang, analysis)`

---

### app/mcp_tools.py (143 lines)
**Purpose:** MCP server implementation - thin wrapper around REST API

**Key Functions:**

1. **`generate(description, requirements)`** (lines 19-58)
   - MCP tool for project generation
   - Forwards to `/generate-sync`
   - Returns combined_text

2. **`compile_and_fix(code, description, max_attempts)`** (lines 59-98)
   - MCP tool for compilation with fixing
   - Forwards to `/compile-and-fix`
   - Returns fixed code

3. **`compile(code)`** (lines 100-136)
   - MCP tool for compilation only
   - Forwards to `/compile`
   - Returns compiler output

**Global Configuration:**
```python
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
mcp = FastMCP("Rust compiler tools")
```

**Main Entry:**
```python
if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
```

**Extension Points for Our Goals:**

1. **Add new MCP tools:**
   ```python
   @mcp.tool()
   async def convert_python(source_code: str, description: str) -> str:
       """Convert Python code to Rust"""
       # Forward to new /convert-python endpoint
   
   @mcp.tool()
   async def convert_cpp(source_code: str, description: str) -> str:
       """Convert C++ code to Rust"""
       # Forward to new /convert-cpp endpoint
   
   @mcp.tool()
   async def analyze_for_conversion(source_code: str, language: str) -> str:
       """Analyze code and suggest Rust equivalents"""
       # Forward to new /analyze endpoint
   ```

2. **Keep thin wrapper pattern:**
   - MCP tools should remain simple HTTP forwarders
   - All logic goes in app/main.py
   - This maintains separation of concerns

---

### app/compiler.py (71 lines)
**Purpose:** Wrapper around Rust compiler (cargo/rustc)

**Key Functions:**

1. **`build_project(project_path)`** (lines 13-31)
   - Runs `cargo build` in project directory
   - Returns (success: bool, output: str)
   - Uses subprocess.run with capture_output

2. **`run_project(project_path)`** (lines 55-71)
   - Runs `cargo run` in project directory
   - Returns (success: bool, output: str)
   - Only called after successful build

3. **`extract_error_context(error_output)`** (lines 33-53)
   - Parses compiler error output
   - Extracts error message and location
   - Returns dict with error details
   - Simple implementation - could be enhanced

**Configuration:**
```python
self.cargo_path = os.getenv("CARGO_PATH", "cargo")
self.rustc_path = os.getenv("RUST_COMPILER_PATH", "rustc")
```

**Extension Points for Our Goals:**

1. **Add validation methods:**
   ```python
   def check_rust_version(self) -> str:
       """Check installed Rust version"""
   
   def suggest_crates(self, features: List[str]) -> List[str]:
       """Suggest Rust crates for required features"""
   
   def validate_syntax(self, code: str) -> Tuple[bool, str]:
       """Quick syntax check without full build"""
   ```

2. **Enhance error parsing:**
   - Better extraction of error codes (E0XXX)
   - Extract suggested fixes from compiler
   - Categorize errors (borrow, lifetime, type, etc.)

**Reusability:** Can be used as-is for compiling converted Rust code. No modifications needed unless we want better error analysis.

---

### app/llm_client.py (191 lines)
**Purpose:** Interface to LLM APIs (OpenAI-compatible)

**Key Functions:**

1. **`__init__(...)`** (lines 10-36)
   - Initialize OpenAI client
   - Support custom base URLs
   - Handle authentication
   - Set default models

2. **`generate_text(prompt, system_message, max_tokens, temperature)`** (lines 38-105)
   - Main text generation method
   - Uses OpenAI chat completions API
   - Has fallback templates on failure
   - Returns generated text

3. **`get_embeddings(texts)`** (lines 163-186)
   - Generate embeddings for texts
   - Uses OpenAI embeddings API
   - Falls back to hash-based pseudo-embeddings
   - Returns list of vectors

4. **`_get_fallback_response(prompt)`** (lines 107-161)
   - Returns hardcoded templates when API fails
   - Has templates for calculator, hello world
   - Ensures system never crashes

**Key Features:**
- Flexible base URL (supports any OpenAI-compatible API)
- Optional API key (for public/local nodes)
- Automatic fallbacks
- Timeout handling (60 seconds)
- Response validation and fixing

**Extension Points for Our Goals:**

1. **Add specialized generation methods:**
   ```python
   def generate_rust_from_python(self, python_code: str, context: dict) -> str:
       """Generate Rust code from Python with specific system message"""
   
   def generate_rust_from_cpp(self, cpp_code: str, context: dict) -> str:
       """Generate Rust code from C++ with specific system message"""
   
   def analyze_code_structure(self, code: str, language: str) -> dict:
       """Use LLM to analyze code structure"""
   ```

2. **Add conversion-specific prompts:**
   - Templates for Python → Rust
   - Templates for C++ → Rust
   - Templates for explaining idiomatic Rust equivalents

**Reusability:** Core client can be reused. We'll add specialized methods for conversion workflows.

---

### app/vector_store.py (156 lines)
**Purpose:** Interface to Qdrant vector database

**Key Functions:**

1. **`__init__(...)`** (lines 14-27)
   - Initialize Qdrant client
   - Support cloud, local file, or server
   - Set embedding size

2. **`create_collection(name, vector_size)`** (lines 29-55)
   - Create Qdrant collection
   - Configure vector size and distance metric
   - Skip if already exists

3. **`search(collection_name, query_vector, limit)`** (lines 73-82)
   - Find similar vectors
   - Return payload data
   - Used for RAG

4. **`add_item(collection_name, vector, item)`** (lines 91-118)
   - Add single item to collection
   - Generate UUID
   - Upsert to Qdrant

5. **`count(collection_name)`** (lines 120-127)
   - Get number of items in collection
   - Used to check if loading needed

**Data Loading Functions:**
- **`load_project_examples()`** (lines 129-156)
  - Load JSON files from data/project_examples/
  - Generate embeddings
  - Insert into vector DB

**Extension Points for Our Goals:**

1. **Add new collections:**
   ```python
   # In app/main.py initialization:
   vector_store.create_collection("python_patterns")
   vector_store.create_collection("cpp_patterns")
   vector_store.create_collection("conversion_examples")
   ```

2. **Add conversion examples:**
   - Create `data/conversion_examples/python_to_rust.json`
   - Create `data/conversion_examples/cpp_to_rust.json`
   - Each with source code + Rust equivalent

3. **Add pattern search methods:**
   ```python
   def find_similar_python_pattern(self, code_snippet: str) -> List[dict]:
       """Find Python patterns similar to snippet"""
   
   def find_rust_equivalent(self, source_pattern: dict) -> dict:
       """Find Rust equivalent for source pattern"""
   ```

**Reusability:** Fully reusable. Just add new collections and examples for Python/C++ patterns.

---

### app/prompt_generator.py (70 lines)
**Purpose:** Generate prompts for LLM

**Key Functions:**

1. **`__init__(template_path)`** (lines 8-40)
   - Load prompt template from file
   - Has default template if file not found
   - Uses Python Template class

2. **`generate_prompt(description, requirements)`** (lines 42-69)
   - Create prompt from description
   - Include tool instructions
   - Add requirements
   - Format for LLM

**Current Template:**
```
<|im_start|>system
You are an expert Rust developer. Create a complete, working Cargo project...
<|im_end|>
<|im_start|>user
Create a Rust Cargo project for: $project_description
$additional_requirements
<|im_end|>
```

**Extension Points for Our Goals:**

1. **Add conversion templates:**
   ```python
   def generate_conversion_prompt(
       self, 
       source_code: str, 
       source_lang: str, 
       description: str
   ) -> str:
       """Generate prompt for code conversion"""
       if source_lang == "python":
           return self._python_conversion_template(source_code, description)
       elif source_lang == "cpp":
           return self._cpp_conversion_template(source_code, description)
   ```

2. **Create new template files:**
   - `templates/python_to_rust_prompt.txt`
   - `templates/cpp_to_rust_prompt.txt`
   - `templates/analysis_prompt.txt`

3. **Add analysis prompts:**
   ```python
   def generate_analysis_prompt(self, code: str, language: str) -> str:
       """Generate prompt to analyze source code structure"""
   ```

**Reusability:** Can reuse template loading mechanism. Need to add new templates for conversion.

---

### app/response_parser.py (145 lines)
**Purpose:** Parse LLM responses into files

**Key Functions:**

1. **`parse_response(response)`** (lines 11-94)
   - Extract files from LLM response
   - Multiple fallback strategies
   - Returns dict of {filename: content}
   - Very robust parsing

2. **`write_files(files, project_dir)`** (lines 129-145)
   - Write files to disk
   - Create directories as needed
   - Normalize paths
   - Returns list of file paths

3. **`_clean_code_block(text)`** (lines 96-106)
   - Remove backticks and language identifiers
   - Clean whitespace

4. **`_extract_section(response, identifier)`** (lines 109-127)
   - Extract section by identifier
   - Used in fallback parsing

**Parsing Strategies:**
1. Regex for `[filename: ...]` markers
2. Content pattern matching (detect Cargo.toml, main.rs)
3. Section extraction by file name
4. Default file creation

**Extension Points for Our Goals:**

1. **Add source code parsing:**
   ```python
   def parse_source_code(self, code: str, language: str) -> Dict[str, any]:
       """Parse Python/C++ source into AST or structure"""
       if language == "python":
           return self._parse_python(code)
       elif language == "cpp":
           return self._parse_cpp(code)
   ```

2. **Add conversion result validation:**
   ```python
   def validate_conversion(self, source_files: dict, rust_files: dict) -> bool:
       """Check if conversion includes all source modules"""
   ```

**Reusability:** Fully reusable for Rust code. Need to add Python/C++ parsing capabilities.

---

### app/load_data.py (62 lines)
**Purpose:** Load examples into vector database

**Key Functions:**

1. **`load_examples(vector_store, llm_client, collection_name, file_pattern, text_key)`** (lines 17-43)
   - Generic example loader
   - Read JSON files
   - Generate embeddings
   - Batch insert into Qdrant

2. **`load_project_examples()`** (lines 45-50)
   - Load Rust project examples
   - Uses `query` field for embedding

3. **`load_error_examples()`** (lines 52-57)
   - Load compiler error examples
   - Uses `error` field for embedding

**Data Format:**
```json
{
  "query": "text to embed",
  "example": "full example",
  "project_files": { ... }
}
```

**Extension Points for Our Goals:**

1. **Add conversion example loaders:**
   ```python
   def load_python_conversion_examples():
       """Load Python→Rust conversion examples"""
       load_examples(
           vector_store, llm_client,
           "python_conversions",
           "data/conversion_examples/python_*.json",
           "python_code"
       )
   
   def load_cpp_conversion_examples():
       """Load C++→Rust conversion examples"""
   ```

2. **Create example data structure:**
   ```json
   {
     "python_code": "def add(a, b): return a + b",
     "rust_code": "fn add(a: i32, b: i32) -> i32 { a + b }",
     "explanation": "...",
     "patterns": ["function", "parameters", "return"]
   }
   ```

**Reusability:** Fully reusable. Just add new loader functions and data files.

---

### app/llm_tools.py (45 lines)
**Purpose:** LLM tool definitions (vector store query tool)

**Key Class:**
```python
class VectorStoreQueryTool:
    def query_examples(query, collection, limit) -> str
```

**Status:** Defined but NOT used

**Potential Use:** Could expose to LLM for dynamic example retrieval

**Extension Points for Our Goals:**

1. **Add to LLM tool calling:**
   - Enable LLM to query conversion examples
   - LLM could search for similar Python/C++ patterns
   - LLM could fetch relevant Rust idioms

2. **Add new tools:**
   ```python
   class CodeAnalysisTool:
       def analyze_structure(code: str, language: str) -> dict:
           """Let LLM analyze code structure"""
   
   class CrateRecommendationTool:
       def suggest_crates(features: List[str]) -> List[str]:
           """Let LLM recommend Rust crates"""
   ```

**Reusability:** Pattern is useful. Could enable more sophisticated LLM interactions.

---

### cli/main.py (347 lines)
**Purpose:** Command-line interface using Typer

**Key Commands:**

1. **`generate`** - Generate projects (sync/async)
2. **`status`** - Check project status
3. **`download`** - Download project ZIP
4. **`cat`** - View file contents
5. **`compile`** - Compile Rust code
6. **`fix`** - Auto-fix compilation errors
7. **`version`** - Show version info

**Implementation:** Uses Typer + Rich for CLI

**Extension Points for Our Goals:**

1. **Add conversion commands:**
   ```python
   @app.command()
   def convert_python(
       source: str = typer.Option(..., "--source", help="Python file"),
       out: str = typer.Option(None, "--out", help="Output directory")
   ):
       """Convert Python code to Rust"""
   
   @app.command()
   def convert_cpp(
       source: str = typer.Option(..., "--source", help="C++ file"),
       out: str = typer.Option(None, "--out", help="Output directory")
   ):
       """Convert C++ code to Rust"""
   
   @app.command()
   def analyze(
       source: str = typer.Option(..., "--source", help="Source file"),
       language: str = typer.Option(..., "--language", help="Source language")
   ):
       """Analyze code for Rust conversion"""
   ```

**Reusability:** CLI framework is great. Easy to add new commands.

---

### app/utils.py (1 line)
**Purpose:** Utility functions

**Status:** Empty file

**Extension Points for Our Goals:**

1. **Add utility functions:**
   ```python
   def detect_language(file_path: str) -> str:
       """Detect source language from file extension"""
   
   def extract_dependencies(code: str, language: str) -> List[str]:
       """Extract library dependencies from code"""
   
   def format_rust_code(code: str) -> str:
       """Format Rust code with rustfmt"""
   
   def validate_rust_names(name: str) -> str:
       """Convert identifier to valid Rust name"""
   ```

**Reusability:** Perfect place to add helper functions for conversion.

---

## 6. Claude Code Integration Strategy

### Understanding Claude Code

**What is Claude Code?**
- Cursor-like AI coding interface
- Uses slash commands (e.g., `/fix`, `/test`, `/add`)
- Can read/write files in workspace
- Can execute commands
- Uses MCP for extended capabilities

**How RustCoder Fits:**
- RustCoder is an MCP server
- Claude Code can use RustCoder tools
- We add new tools for Python/C++ conversion
- Claude Code UI makes tools accessible via slash commands

---

### Approach: Extend MCP Server with Conversion Tools

**Recommended Strategy:** Add new MCP tools for conversion workflows

**Rationale:**
1. Minimal changes to existing code
2. Maintains backward compatibility
3. Works with Claude Desktop, Claude Code, and any MCP client
4. Separates concerns (MCP layer vs business logic)

---

### Where to Add New Functionality

#### Step 1: Add Backend Endpoints (app/main.py)

**Location:** After line 725 (end of `generate_project_sync`)

**New Endpoints:**

```python
@app.post("/analyze-for-conversion")
async def analyze_for_conversion(request: dict):
    """
    Analyze Python/C++ code and provide conversion plan
    
    Args:
        source_code (str): Source code to analyze
        source_language (str): "python" or "cpp"
        
    Returns:
        analysis (dict): Structure, dependencies, patterns, recommendations
    """
    # Implementation here

@app.post("/convert-to-rust")
async def convert_to_rust(request: dict):
    """
    Convert Python/C++ code to Rust
    
    Args:
        source_code (str): Source code to convert
        source_language (str): "python" or "cpp"
        description (str): Optional description
        include_interop (bool): Generate PyO3/FFI bindings
        
    Returns:
        combined_text (str): Generated Rust code
        analysis (dict): Conversion notes
        interop_code (str): Optional binding code
    """
    # Implementation here

@app.post("/suggest-migration-strategy")
async def suggest_migration_strategy(request: dict):
    """
    Suggest incremental migration strategy
    
    Args:
        project_structure (dict): Source project file tree
        entry_points (list): Main entry points
        
    Returns:
        strategy (dict): Step-by-step migration plan
    """
    # Implementation here
```

#### Step 2: Add MCP Tools (app/mcp_tools.py)

**Location:** After line 136 (end of `compile` function)

**New Tools:**

```python
@mcp.tool()
async def analyze_for_conversion(source_code: str, source_language: str) -> str:
    """
    Analyze Python or C++ code to prepare for Rust conversion.
    
    Provides:
    - Code structure analysis
    - Dependency mapping
    - Idiomatic Rust recommendations
    - Potential challenges
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/analyze-for-conversion",
            json={'source_code': source_code, 'source_language': source_language}
        )
        response.raise_for_status()
        return response.text

@mcp.tool()
async def convert_to_rust(
    source_code: str,
    source_language: str,
    description: str = "",
    include_interop: bool = False
) -> str:
    """
    Convert Python or C++ code to Rust.
    
    Arguments:
    - source_code: The source code to convert
    - source_language: Either "python" or "cpp"
    - description: Optional description of the code's purpose
    - include_interop: If true, generate PyO3/FFI bindings for gradual migration
    
    Returns multi-file Rust project in [filename: ...] format.
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/convert-to-rust",
            json={
                'source_code': source_code,
                'source_language': source_language,
                'description': description,
                'include_interop': include_interop
            }
        )
        response.raise_for_status()
        resp_json = json.loads(response.text)
        return resp_json["combined_text"]

@mcp.tool()
async def suggest_migration_strategy(
    project_structure: str,
    entry_points: str
) -> str:
    """
    Suggest an incremental migration strategy for a Python/C++ project.
    
    Analyzes project structure and recommends:
    - Which modules to convert first
    - Dependency order
    - Interop strategies
    - Testing approach
    
    Arguments:
    - project_structure: JSON string describing project file tree
    - entry_points: Comma-separated list of main entry points
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/suggest-migration-strategy",
            json={
                'project_structure': json.loads(project_structure),
                'entry_points': entry_points.split(',')
            }
        )
        response.raise_for_status()
        return response.text
```

#### Step 3: Add Analysis Modules (New Files)

**Create:** `app/code_analyzer.py`

```python
"""
Analyze Python and C++ code to prepare for Rust conversion
"""
class CodeAnalyzer:
    def analyze_python(self, code: str) -> dict:
        """Parse Python code and extract structure"""
        # Use ast module
        
    def analyze_cpp(self, code: str) -> dict:
        """Parse C++ code and extract structure"""
        # Use libclang or regex patterns
        
    def extract_dependencies(self, code: str, language: str) -> List[str]:
        """Extract library dependencies"""
        
    def identify_patterns(self, code: str, language: str) -> List[str]:
        """Identify language-specific patterns"""
        
    def suggest_rust_equivalents(self, analysis: dict) -> dict:
        """Map source patterns to Rust idioms"""
```

**Create:** `app/conversion_prompts.py`

```python
"""
Specialized prompts for code conversion
"""
class ConversionPromptGenerator:
    def python_to_rust_prompt(self, code: str, analysis: dict) -> str:
        """Generate prompt for Python→Rust conversion"""
        
    def cpp_to_rust_prompt(self, code: str, analysis: dict) -> str:
        """Generate prompt for C++→Rust conversion"""
        
    def interop_prompt(self, rust_code: str, source_lang: str) -> str:
        """Generate prompt for PyO3/FFI binding code"""
```

#### Step 4: Add Conversion Examples (New Data)

**Create:** `data/conversion_examples/`

```
data/conversion_examples/
├── python_to_rust/
│   ├── classes.json
│   ├── functions.json
│   ├── file_io.json
│   ├── async.json
│   └── data_structures.json
│
└── cpp_to_rust/
    ├── classes.json
    ├── pointers.json
    ├── templates.json
    ├── memory.json
    └── concurrency.json
```

**Example Format:**
```json
{
  "python_code": "class Calculator:\n    def add(self, a, b):\n        return a + b",
  "rust_code": "struct Calculator;\n\nimpl Calculator {\n    fn add(&self, a: i32, b: i32) -> i32 {\n        a + b\n    }\n}",
  "explanation": "Python classes map to Rust structs with impl blocks",
  "patterns": ["class", "method", "self"],
  "rust_patterns": ["struct", "impl", "method", "reference"],
  "difficulty": "easy"
}
```

#### Step 5: Add CLI Commands (cli/main.py)

**Location:** After line 340 (end of `fix` command)

```python
@app.command()
def convert(
    source: str = typer.Option(..., "--source", help="Source file to convert"),
    language: str = typer.Option(..., "--language", help="Source language (python/cpp)"),
    output: str = typer.Option("./converted", "--output", help="Output directory"),
    interop: bool = typer.Option(False, "--interop", help="Generate interop bindings"),
    analyze_only: bool = typer.Option(False, "--analyze", help="Only analyze, don't convert"),
    ctx: typer.Context = typer.Option(None),
):
    """Convert Python or C++ code to Rust"""
    # Implementation
```

---

### Files That Need Modification

**Must Modify:**
1. ✅ `app/main.py` - Add 3 new endpoints
2. ✅ `app/mcp_tools.py` - Add 3 new MCP tools
3. ⚠️ `cli/main.py` - Add conversion commands (optional)

**Must Create:**
1. 📄 `app/code_analyzer.py` - Code analysis module
2. 📄 `app/conversion_prompts.py` - Conversion-specific prompts
3. 📄 `templates/python_to_rust.txt` - Conversion prompt template
4. 📄 `templates/cpp_to_rust.txt` - Conversion prompt template
5. 📄 `data/conversion_examples/` - Example conversions (directory)

**May Modify:**
1. ⚠️ `app/prompt_generator.py` - Add conversion prompt methods
2. ⚠️ `app/response_parser.py` - Add source code parsing (if needed)
3. ⚠️ `app/utils.py` - Add helper functions
4. ⚠️ `app/load_data.py` - Add conversion example loaders

---

### Configuration Updates Needed

**Environment Variables (.env):**
- No new variables required
- Existing LLM config works for conversion

**Dependencies (requirements.txt):**
```
# Add for Python code analysis:
ast (built-in)

# Add for better Python parsing:
astor>=0.8.1  # Python AST tools

# Optional for C++ parsing:
# libclang-py3>=3.9  # If we want real C++ parsing
```

---

### Integration with Claude Code

**How Users Will Use It:**

1. **In Claude Code workspace:**
   - User has Python/C++ project open
   - Starts RustCoder MCP server
   - Uses slash commands:
     - `/analyze-for-conversion <file>` - Analyze code
     - `/convert-to-rust <file>` - Convert to Rust
     - `/suggest-migration` - Get migration plan

2. **Claude Code connects via MCP:**
   ```json
   // claude_desktop_config.json
   {
     "mcpServers": {
       "rustcoder": {
         "command": "docker",
         "args": ["compose", "up", "mcp-server"],
         "cwd": "/path/to/RustCoder"
       }
     }
   }
   ```

3. **Tools appear in Claude Code UI:**
   - Auto-complete for tool names
   - Type validation for parameters
   - Streaming responses for long operations

---

## 7. Reusable Components for Our Goals

### For Python/C++ Conversion

**✅ Can Reuse:**

1. **LLM Client** (`app/llm_client.py`)
   - ✅ OpenAI integration works as-is
   - ✅ Fallback mechanisms
   - ✅ Embedding generation
   - 📝 Action: Add conversion-specific methods

2. **Response Parser** (`app/response_parser.py`)
   - ✅ `[filename: ...]` parsing works for Rust output
   - ✅ Multi-fallback strategy is robust
   - ❌ No Python/C++ parsing yet
   - 📝 Action: Add source code parsing methods

3. **Compiler Wrapper** (`app/compiler.py`)
   - ✅ Can compile converted Rust code
   - ✅ Error extraction works
   - 📝 Action: None needed

4. **Vector Store** (`app/vector_store.py`)
   - ✅ RAG infrastructure ready
   - ✅ Can add new collections
   - 📝 Action: Add conversion example collections

5. **MCP Framework** (`app/mcp_tools.py`)
   - ✅ Tool registration pattern is simple
   - ✅ Async HTTP forwarding works
   - 📝 Action: Add 3 new tools

6. **REST API Framework** (`app/main.py`)
   - ✅ FastAPI endpoints are easy to add
   - ✅ Error handling is consistent
   - 📝 Action: Add 3 new endpoints

**❌ Need to Build:**

1. **Code Analyzer**
   - ❌ No Python AST parsing
   - ❌ No C++ parsing
   - ❌ No dependency extraction
   - 📝 Action: Create `app/code_analyzer.py`

2. **Conversion Prompts**
   - ❌ No Python→Rust prompts
   - ❌ No C++→Rust prompts
   - ❌ No interop prompts
   - 📝 Action: Create `app/conversion_prompts.py` + templates

3. **Conversion Examples**
   - ❌ No Python pattern examples
   - ❌ No C++ pattern examples
   - 📝 Action: Create `data/conversion_examples/`

4. **Migration Strategy Logic**
   - ❌ No project structure analysis
   - ❌ No dependency ordering
   - ❌ No incremental migration planning
   - 📝 Action: Create `app/migration_planner.py`

---

### Rust-Specific Resources

**✅ Already Implemented:**

1. **Rust Documentation Access** - Via LLM knowledge
   - ✅ LLM has Rust knowledge
   - ✅ Can query examples
   - 📝 Status: Works implicitly through LLM

2. **Knowledge Base** - Rust examples
   - ✅ 4 project examples in vector DB
   - ✅ 5 error examples in vector DB
   - ⚠️ Limited to specific examples
   - 📝 Action: Add more examples

3. **Compilation Feedback Loop**
   - ✅ Iterative error fixing works
   - ✅ Vector search for errors
   - 📝 Status: Fully functional

**❌ Not Implemented:**

1. **Crate Recommendation System**
   - ❌ No crate database
   - ❌ No feature→crate mapping
   - 📝 Action: Could use LLM knowledge or crates.io API

2. **Idiomatic Rust Patterns Database**
   - ❌ Limited pattern examples
   - 📝 Action: Add to vector DB

3. **PyO3/FFI Template Library**
   - ❌ No interop templates
   - 📝 Action: Create interop examples

---

## 8. Dependencies Analysis

### Critical Dependencies for Our Work

**Must Understand:**

1. **`fastmcp`** (MCP Python SDK)
   - **Why:** Core of MCP server implementation
   - **Usage:** `@mcp.tool()` decorator, `mcp.run(transport)`
   - **Docs:** https://github.com/jlowin/fastmcp
   - **Key Features:**
     - Simple decorator-based registration
     - Type validation from function signatures
     - Multiple transport modes (stdio, sse)
   - 📝 Action: Study FastMCP docs to understand capabilities

2. **`openai`** (OpenAI Python SDK)
   - **Why:** Used for LLM API calls (any OpenAI-compatible)
   - **Usage:** `client.chat.completions.create()`, `client.embeddings.create()`
   - **Key:** Works with non-OpenAI APIs via base_url
   - 📝 Action: Understand how to craft prompts for conversion

3. **`qdrant-client`** (Vector DB)
   - **Why:** RAG for code examples
   - **Usage:** Collections, search, upsert
   - **Key:** Cosine similarity search
   - 📝 Action: Design conversion example schema

4. **`fastapi`** (Web framework)
   - **Why:** REST API backend
   - **Usage:** Routes, dependency injection, validation
   - **Key:** Pydantic models for validation
   - 📝 Action: Add new routes following existing patterns

**Should Understand:**

5. **`httpx`** (HTTP client)
   - **Why:** MCP tools call REST API
   - **Usage:** Async HTTP requests
   - **Key:** Timeout handling

6. **`typer`** (CLI framework)
   - **Why:** CLI commands
   - **Usage:** Decorator-based commands
   - **Key:** Easy to add new commands

7. **`pydantic`** (Data validation)
   - **Why:** Request/response validation
   - **Usage:** BaseModel classes
   - **Key:** Type-safe API contracts

**May Use:**

8. **`ast`** (Python standard library)
   - **Why:** Parse Python code
   - **Usage:** `ast.parse()`, `ast.walk()`
   - **Status:** Built-in
   - 📝 Action: Use for Python code analysis

9. **`astor`** (Python AST tools)
   - **Why:** Better AST manipulation
   - **Status:** Need to add to requirements
   - 📝 Action: Consider adding for Python parsing

10. **`libclang`** (C++ parsing)
    - **Why:** Parse C++ code
    - **Status:** Optional - complex to set up
    - 📝 Action: Consider simpler alternatives (regex patterns, LLM-based parsing)

---

## 9. Next Steps & Recommendations

### Phase 1: Foundation (Week 1-2)

**Priority: Critical**

1. ✅ **Set Up Development Environment**
   - Run RustCoder locally with Docker
   - Test all existing MCP tools
   - Verify LLM API connectivity
   - Test vector search functionality

2. ✅ **Create Conversion Example Dataset**
   - Collect 10-20 Python→Rust examples
   - Collect 10-20 C++→Rust examples
   - Format as JSON with source + target + explanation
   - Include common patterns: classes, functions, async, file I/O

3. ✅ **Design Conversion Prompt Templates**
   - Create `templates/python_to_rust.txt`
   - Create `templates/cpp_to_rust.txt`
   - Include: context, patterns, idiomatic Rust guidelines
   - Test with LLM to refine

4. ✅ **Implement Basic Code Analyzer**
   - Create `app/code_analyzer.py`
   - Implement Python AST parsing
   - Implement C++ pattern detection (regex-based for now)
   - Extract: functions, classes, imports, structure

---

### Phase 2: Core Conversion (Week 3-4)

**Priority: Critical**

5. ✅ **Add Backend Endpoints**
   - `POST /analyze-for-conversion` in `app/main.py`
   - `POST /convert-to-rust` in `app/main.py`
   - Test with Postman/curl
   - Validate end-to-end flow

6. ✅ **Add MCP Tools**
   - `analyze_for_conversion()` in `app/mcp_tools.py`
   - `convert_to_rust()` in `app/mcp_tools.py`
   - Test with `cmcp` CLI
   - Verify Claude Desktop integration

7. ✅ **Implement Conversion Logic**
   - Create `app/conversion_prompts.py`
   - Integrate code analyzer with prompt generation
   - Use vector search for similar conversion examples
   - Test conversion quality with sample Python/C++ code

8. ✅ **Add Vector Collections for Conversion**
   - Load conversion examples into Qdrant
   - Test similarity search for patterns
   - Verify RAG improves conversion quality

---

### Phase 3: Advanced Features (Week 5-6)

**Priority: High**

9. ⚠️ **Implement Migration Strategy Suggester**
   - Create `app/migration_planner.py`
   - Add `POST /suggest-migration-strategy` endpoint
   - Add MCP tool `suggest_migration_strategy()`
   - Analyze project structure and suggest order

10. ⚠️ **Add Interop Scaffolding Generation**
    - Create PyO3 binding templates
    - Create FFI binding templates
    - Add `include_interop` flag to conversion
    - Generate both Rust code and bindings

11. ⚠️ **Add CLI Commands**
    - `convert` command in `cli/main.py`
    - `analyze` command
    - `migrate` command
    - Test full CLI workflow

12. ⚠️ **Improve Error Handling**
    - Handle invalid source code gracefully
    - Better error messages for conversion failures
    - Suggest fixes for unconvertible patterns

---

### Phase 4: Testing & Polish (Week 7-8)

**Priority: Medium**

13. ⚠️ **Test with Real Projects**
    - Convert small Python libraries
    - Convert C++ utilities
    - Document conversion success rate
    - Identify common failure patterns

14. ⚠️ **Create Documentation**
    - Usage guide for conversion workflow
    - Claude Code integration guide
    - Conversion pattern reference
    - Migration best practices

15. ⚠️ **Add Tests**
    - Unit tests for code analyzer
    - Integration tests for conversion endpoints
    - MCP tool tests
    - Example-based validation tests

16. ⚠️ **Performance Optimization**
    - Cache analysis results
    - Parallel LLM calls for large projects
    - Optimize vector search queries

---

### Quick Wins (Do First)

1. ✅ **Reuse Existing Infrastructure**
   - LLM client, compiler, parser all work as-is
   - MCP tool registration is trivial
   - FastAPI endpoints are easy to add

2. ✅ **Start with Python (Easier than C++)**
   - Python AST parsing is built-in
   - Python patterns are simpler
   - More conversion examples available online

3. ✅ **Use Simple File Format**
   - Existing `[filename: ...]` format works perfectly
   - No need for complex file I/O
   - Consistent with existing tools

4. ✅ **Leverage Vector Search**
   - RAG infrastructure ready
   - Just add conversion examples
   - Dramatically improves conversion quality

---

### Gaps (Need to Build)

1. ❌ **Code Analysis Module**
   - No Python AST parser
   - No C++ parser
   - No dependency extraction
   - **Effort:** Medium (Python), High (C++)

2. ❌ **Conversion Prompt System**
   - No conversion templates
   - No pattern-specific prompts
   - **Effort:** Low-Medium

3. ❌ **Conversion Examples**
   - No Python→Rust examples
   - No C++→Rust examples
   - **Effort:** Medium (research + collection)

4. ❌ **Interop Scaffolding**
   - No PyO3 templates
   - No FFI templates
   - **Effort:** Medium-High

5. ❌ **Migration Planner**
   - No project analysis
   - No dependency ordering
   - **Effort:** High

---

### Risks & Challenges

1. ⚠️ **LLM Conversion Quality**
   - **Risk:** LLM may generate incorrect Rust code
   - **Mitigation:** Use compiler feedback loop (already exists!)
   - **Mitigation:** Use RAG with good examples
   - **Mitigation:** Iterative fixing (already implemented)

2. ⚠️ **C++ Parsing Complexity**
   - **Risk:** C++ is hard to parse correctly
   - **Mitigation:** Start with Python, add C++ later
   - **Mitigation:** Use regex for common patterns, not full parsing
   - **Mitigation:** Let LLM handle complex C++ understanding

3. ⚠️ **Idiomatic Rust**
   - **Risk:** Converted code may not be idiomatic
   - **Mitigation:** Include idiom examples in prompts
   - **Mitigation:** Use vector search for Rust patterns
   - **Mitigation:** Rely on compiler errors to force correctness

4. ⚠️ **Unconvertible Patterns**
   - **Risk:** Some code can't be directly converted
   - **Mitigation:** Provide analysis of what can't be converted
   - **Mitigation:** Suggest refactoring strategies
   - **Mitigation:** Generate interop bindings for gradual migration

5. ⚠️ **API Costs**
   - **Risk:** LLM API calls can be expensive
   - **Mitigation:** Support local LLMs (already supported!)
   - **Mitigation:** Cache analysis results
   - **Mitigation:** Batch operations

---

### Recommended Focus Order

**Immediate (This Week):**
1. Set up dev environment and test existing system
2. Create 10-20 Python→Rust conversion examples
3. Design Python→Rust prompt template
4. Build basic Python AST analyzer

**Next (Week 2-3):**
5. Implement `convert_to_rust` endpoint + MCP tool
6. Test end-to-end Python→Rust conversion
7. Add conversion examples to vector DB
8. Refine prompts based on results

**Then (Week 4-5):**
9. Add `analyze_for_conversion` tool
10. Implement interop scaffolding (PyO3)
11. Add C++ support (basic patterns)
12. Test with real Python projects

**Finally (Week 6+):**
13. Add migration strategy suggester
14. Improve C++ support
15. Add CLI commands
16. Documentation and tests

---

### Success Metrics

**Minimum Viable Product (MVP):**
- ✅ Can convert simple Python functions to Rust
- ✅ MCP tool works in Claude Desktop
- ✅ Generated Rust code compiles
- ✅ 50%+ of conversions succeed without manual fixes

**Full Feature Set:**
- ✅ Converts Python and C++ code
- ✅ Generates PyO3/FFI bindings
- ✅ Suggests migration strategies
- ✅ 80%+ of conversions compile
- ✅ Idiomatic Rust output

**Stretch Goals:**
- ✅ Handles complex Python (async, metaclasses)
- ✅ Handles complex C++ (templates, smart pointers)
- ✅ Automated testing of converted code
- ✅ Performance comparison tools

---

## 10. Conclusion

### Key Takeaways

1. **RustCoder is Python-based** - Not TypeScript! Uses FastAPI + FastMCP.

2. **Architecture is Well-Designed** - Clean separation between MCP layer and business logic.

3. **Extension is Straightforward** - Add 3 endpoints, 3 MCP tools, and supporting modules.

4. **Reusable Infrastructure** - LLM client, compiler wrapper, vector search all work as-is.

5. **Main Work is New Logic** - Need to build: code analyzer, conversion prompts, examples.

6. **RAG is Key** - Conversion quality depends on good examples in vector DB.

7. **Start Simple** - Begin with Python, add C++ later. Focus on common patterns first.

### Implementation Path

```
Week 1-2: Foundation
    ↓
Week 3-4: Core Conversion (Python)
    ↓
Week 5-6: Advanced Features (C++, Interop)
    ↓
Week 7-8: Testing & Polish
```

### Files to Create/Modify

**Create (6 new files):**
- `app/code_analyzer.py` - Code analysis
- `app/conversion_prompts.py` - Conversion prompts
- `templates/python_to_rust.txt` - Prompt template
- `templates/cpp_to_rust.txt` - Prompt template
- `data/conversion_examples/` - Example data
- (Optional) `app/migration_planner.py` - Migration strategies

**Modify (3 files):**
- `app/main.py` - Add 3 endpoints
- `app/mcp_tools.py` - Add 3 MCP tools
- (Optional) `cli/main.py` - Add CLI commands

**Total New Code:** ~500-800 lines (excluding examples)

---

**Document Version:** 1.0  
**Last Updated:** October 10, 2025  
**Next Review:** After Phase 1 completion

