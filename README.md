# Rust Coder

AI agents could autonomously write and execute software programs in order to accomplish their own tasks and goals. The Rust language is a perfect fit for AI agents -- as the powerful Rust compiler can provide real-time and autonomous feedback to the agent to ensure the validity of the generated code. The Rust Coder project is an open source effort to provide such tools. It consists of API and MCP services that generate fully functional Rust projects from natural language descriptions. These services leverage LLMs to create complete Rust cargo projects, compile Rust source code, and automatically fix compiler errors.

---

## ✨ Features

- **Generate Rust Projects** 📦 - Transform text descriptions into complete Rust projects.
- **Automatic Compilation & Fixing** 🛠 - Detect and resolve errors during compilation.
- **Vector Search** 🔍 - Search for similar projects and errors.
- **Docker Containerization** 🐳 - Easy deployment with Docker.
- **Asynchronous Processing** ⏳ - Handle long-running operations efficiently.
- **Multiple Service Interfaces** 🔄 - REST API and MCP (Model-Compiler-Processor) interface.

---

## 📋 Prerequisites

Ensure you have the following installed:

- **Docker & Docker Compose** 🐳

Or, if you want to run the services directly on your own computer:

- **Python 3.8+** 🐍
- **Rust Compiler and cargo tools** 🦀 

---

## 📦 Install

```bash
git clone https://github.com/WasmEdge/Rust_coder
cd Rust_coder
```

## 🚀 Configure and run

### Using Docker (Recommended)

Create the `.env` file and specify your own LLM API server. The default config assumes that you have a [Gaia node like this](https://github.com/GaiaNet-AI/node-configs/tree/main/qwen-2.5-coder-3b-instruct-gte) running on `localhost` port `8080`. The alternative configuration shown below uses a [public Gaia node for coding assistance](https://docs.gaianet.ai/nodes#coding-assistant-agents).

```
LLM_API_BASE=https://0x9fcf7888963793472bfcb8c14f4b6b47a7462f17.gaia.domains/v1
LLM_MODEL=gemma-3-27b-it-q4_0
LLM_EMBED_MODEL=nomic-embed
LLM_API_KEY=1234ABCD
LLM_EMBED_SIZE=768
```

Start the services.

```bash
docker-compose up -d
```

Stop the services.

```bash
docker-compose stop
```

### Manual Setup

By default, you will need a [Qdrant server](https://qdrant.tech/documentation/quickstart/) running on `localhost` port `6333`. You also need a [local Gaia node](https://github.com/GaiaNet-AI/node-configs/tree/main/qwen-2.5-coder-3b-instruct-gte). Set the following environment variables in your terminal to point to the Qdrant and Gaia instances, as well as your Rust compiler tools.

```
QDRANT_HOST=localhost
QDRANT_PORT=6333
LLM_API_BASE=http://localhost:8080/v1
LLM_MODEL=Qwen2.5-Coder-3B-Instruct
LLM_EMBED_MODEL=nomic-embed
LLM_API_KEY=your_api_key
LLM_EMBED_SIZE=768
CARGO_PATH=/path/to/cargo
RUST_COMPILER_PATH=/path/to/rustc
```

Start the services.

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔥 Usage

The API provides the following endpoints:

### 🎯 Generate a Project

**Endpoint:** `POST /generate-sync`

**Example:**

```bash
  curl -X POST http://localhost:8000/generate-sync \
  -H "Content-Type: application/json" \
  -d '{"description": "A command-line calculator in Rust", "requirements": "Should support addition, subtraction, multiplication, and division"}'
```

#### 📥 Request Body:

```
{
  "description": "A command-line calculator in Rust",
  "requirements": "Should support addition, subtraction, multiplication, and division"
}
```

#### 📤 Response:

The `combined_text` field contains the flat text output of Rust project files that can be used as input for `/compile` and `/compile-and-fix` API calls.

```
{
   "success": true,
   "message":"Project generated successfully",
   "combined_text":"[filename: Cargo.toml]\n[package]\nname = \"calculator\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html\n\n[dependencies]\nclap = { version = \"4.5\", features = [\"derive\"] }\n\n[filename: src/main.rs]\nuse std::io;\nuse clap::Parser;\n\n#[derive(Parser, Debug)]\n#[command(author, version, about, long_about = None)]\nstruct Args {\n    /// The first number\n    #[arg(required = true)]\n    num1: f64,\n    /// Operator (+, -, *, /)\n    #[arg(required = true, value_parser = clap::value_parser!(f64))]\n    operator: String,\n    /// The second number\n    #[arg(required = true)]\n    num2: f64,\n}\n\nfn main() -> Result<(), Box<dyn std::error::Error>> {\n    let args = Args::parse();\n\n    match args.operator.as_str() {\n        \"+\" => {\n            println!(\"{}\", args.num1 + args.num2);\n        }\n        \"-\" => {\n            println!(\"{}\", args.num1 - args.num2);\n        }\n        \"*\" => {\n            println!(\"{}\", args.num1 * args.num2);\n        }\n        \"/\" => {\n            if args.num2 == 0.0 {\n                eprintln!(\"Error: Cannot divide by zero.\");\n                std::process::exit(1);\n            }\n            println!(\"{}\", args.num1 / args.num2);\n        }\n        _ => {\n            eprintln!(\"Error: Invalid operator. Use +, -, *, or /\");\n            std::process::exit(1);\n        }\n    }\n\n    Ok(())\n}\n\n[filename: README.md]\n# Calculator\n\nA simple command-line calculator written in Rust.  Supports addition, subtraction, multiplication, and division.\n\n## Usage\n\nRun the program with two numbers and an operator as arguments:\n\n```bash\ncargo run <num1> <operator> <num2>\n```\n\nWhere `<operator>` is one of `+`, `-`, `*`, or `/`.\n\n**Example:**\n\n```bash\ncargo run 5 + 3\n# Output: 8\n\ncargo run 10 / 2\n# Output: 5\n\ncargo run 7 * 4\n# Output: 28\n```\n\n## Error Handling\n\nThe calculator handles division by zero and invalid operator inputs.  Error messages are printed to standard error, and the program exits with a non-zero exit code in case of an error.\n\n\n# Build succeeded",
   "files":{
      "Cargo.toml":"[package]\nname = \"calculator\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html\n\n[dependencies]\nclap = { version = \"4.5\", features = [\"derive\"] }",
      "src/main.rs":"use std::io;\nuse clap::Parser;\n\n#[derive(Parser, Debug)]\n#[command(author, version, about, long_about = None)]\nstruct Args {\n    /// The first number\n    #[arg(required = true)]\n    num1: f64,\n    /// Operator (+, -, *, /)\n    #[arg(required = true, value_parser = clap::value_parser!(f64))]\n    operator: String,\n    /// The second number\n    #[arg(required = true)]\n    num2: f64,\n}\n\nfn main() -> Result<(), Box<dyn std::error::Error>> {\n    let args = Args::parse();\n\n    match args.operator.as_str() {\n        \"+\" => {\n            println!(\"{}\", args.num1 + args.num2);\n        }\n        \"-\" => {\n            println!(\"{}\", args.num1 - args.num2);\n        }\n        \"*\" => {\n            println!(\"{}\", args.num1 * args.num2);\n        }\n        \"/\" => {\n            if args.num2 == 0.0 {\n                eprintln!(\"Error: Cannot divide by zero.\");\n                std::process::exit(1);\n            }\n            println!(\"{}\", args.num1 / args.num2);\n        }\n        _ => {\n            eprintln!(\"Error: Invalid operator. Use +, -, *, or /\");\n            std::process::exit(1);\n        }\n    }\n\n    Ok(())\n}",
      "README.md":"# Calculator\n\nA simple command-line calculator written in Rust.  Supports addition, subtraction, multiplication, and division.\n\n## Usage\n\nRun the program with two numbers and an operator as arguments:\n\n```bash\ncargo run <num1> <operator> <num2>\n```\n\nWhere `<operator>` is one of `+`, `-`, `*`, or `/`.\n\n**Example:**\n\n```bash\ncargo run 5 + 3\n# Output: 8\n\ncargo run 10 / 2\n# Output: 5\n\ncargo run 7 * 4\n# Output: 28\n```\n\n## Error Handling\n\nThe calculator handles division by zero and invalid operator inputs.  Error messages are printed to standard error, and the program exits with a non-zero exit code in case of an error."
   },
   "build_output":null,
   "build_success":true
}
```

### 🛠 Compile a Project

**Endpoint:** `POST /compile`

**Example:**

```bash
curl -X POST http://localhost:8000/compile \
-H "Content-Type: application/json" \
-d '{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\");\n}"
}'
```

#### 📥 Request Body:

```
{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\");\n}"
}
```

#### 📤 Response:

```
{
  "success": true,
  "files": [
    "Cargo.toml",
    "src/main.rs"
  ],
  "build_output": "Build successful",
  "run_output": "Hello, World!\n"
}
```

### 🩹 Compile and fix errors 

**Endpoint:** `POST /compile-and-fix`

**Example:**

```bash
curl -X POST http://localhost:8000/compile-and-fix \
-H "Content-Type: application/json" \
-d '{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    print \"Hello, World!\" \n}",
  "description": "A simple hello world program",
  "max_attempts": 3
}'
```

#### 📥 Request Body:

```
{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    print \"Hello, World!\" \n}",
  "description": "A simple hello world program",
  "max_attempts": 3
}
```
     
#### 📤 Response:

The `combined_text` field contains the flat text output of Rust project files that is in the same format as the input `code` field.

```
{
   "success": true,
   "message":"Code fixed and compiled successfully",
   "attempts":[
      {
         "attempt":1,
         "success":false,
         "output":"   Compiling hello_world v0.1.0 (/tmp/tmpbgeg4x_e)\nerror: expected one of `!`, `.`, `::`, `;`, `?`, `{`, `}`, or an operator, found `\"Hello, World!\"`\n --> src/main.rs:2:11\n  |\n2 |     print \"Hello, World!\" \n  |           ^^^^^^^^^^^^^^^ expected one of 8 possible tokens\n\nerror: could not compile `hello_world` (bin \"hello_world\") due to 1 previous error\n"
      },
      {
         "attempt":2,
         "success":true,
         "output":null
      }
   ],
   "combined_text":"[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\");\n}\n\n[filename: README.md]\n# Hello World\n\nThis is a simple \"Hello, World!\" program in Rust.  It prints the message \"Hello, World!\" to the console.\n\nTo run it:\n\n1.  Make sure you have Rust installed ([https://www.rust-lang.org/](https://www.rust-lang.org/)).\n2.  Save the code as `src/main.rs`.\n3.  Run `cargo run` in the terminal from the project directory.",
   "files":{
      "Cargo.toml":"[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html\n\n[dependencies]",
      "src/main.rs":"fn main() {\n    println!(\"Hello, World!\");\n}",
      "README.md":"# Hello World\n\nThis is a simple \"Hello, World!\" program in Rust.  It prints the message \"Hello, World!\" to the console.\n\nTo run it:\n\n1.  Make sure you have Rust installed ([https://www.rust-lang.org/](https://www.rust-lang.org/)).\n2.  Save the code as `src/main.rs`.\n3.  Run `cargo run` in the terminal from the project directory."
   },
   "build_output":"Build successful",
   "run_output":"Hello, World!\n",
   "build_success":true
}
```

### 🎯 Generate a Project Async

**Endpoint:** `POST /generate`

**Example:**

```bash
  curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"description": "A command-line calculator in Rust", "requirements": "Should support addition, subtraction, multiplication, and division"}'
```

#### 📥 Request Body:

```json
{
  "description": "A command-line calculator in Rust",
  "requirements": "Should support addition, subtraction, multiplication, and division"
}
```

#### 📤 Response:

```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Project generation started"
}
```

### 📌 Check Project Status

**Endpoint:** `GET /project/{project_id}`

**Example:**

```bash
curl http://localhost:8000/project/123e4567-e89b-12d3-a456-426614174000
```

#### 📤 Response:

```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "message": "Project generated successfully",
  "files": ["Cargo.toml", "src/main.rs", "README.md"],
  "build_output": "...",
  "run_output": "..."
}
```

### 📌 Get Generated Files

**Endpoint:** `GET /project/{project_id}/files/path_to_file`

**Example:**

```bash
curl http://localhost:8000/project/123e4567-e89b-12d3-a456-426614174000/files/src/main.rs
```

#### 📤 Response:

```
fn main() {
    ... ...
}
```

---

## 🖥️ Command Line Interface (CLI)

The RustCoder CLI provides a command-line interface to interact with the API endpoints and manage projects.

### 📦 Installation

Install the CLI dependencies:

```bash
pip install -r requirements.txt
```

### 🚀 Basic Usage

Run the CLI with:

```bash
python -m cli.main --help
```

Set the server URL via environment variable or flag:

```bash
export RUSTCODER_SERVER=http://localhost:8000
# or
python -m cli.main --server http://localhost:8000
```

### 📋 Available Commands

#### 🔍 Project Generation

**Generate a project (async):**
```bash
python -m cli.main generate --description "A command-line calculator in Rust"
```

**Generate a project (sync):**
```bash
python -m cli.main generate --description "A web API with actix" --sync
```

**Generate with requirements file:**
```bash
python -m cli.main generate --description "CLI tool" --requirements requirements.txt
```

#### 📊 Project Management

**Check project status:**
```bash
python -m cli.main status --project <project_id>
```

**Watch project until completion:**
```bash
python -m cli.main status --project <project_id> --watch
```

**Download project as zip:**
```bash
python -m cli.main download --project <project_id> --out my_project.zip
```

**View project file contents:**
```bash
python -m cli.main cat --project <project_id> --file src/main.rs
```

#### 🛠️ Code Compilation & Fixing

**Compile Rust code from file:**
```bash
python -m cli.main compile --code ./artifacts/multifile.txt
```

**Compile Rust code from project ID:**
```bash
python -m cli.main compile --project <project_id>
```

**Auto-fix compilation errors from file:**
```bash
python -m cli.main fix --code ./artifacts/multifile.txt --description "hello world" --max-attempts 5
```

**Auto-fix compilation errors from project ID:**
```bash
python -m cli.main fix --project <project_id> --description "hello world" --max-attempts 5
```



#### ℹ️ Utility Commands

**Show version info:**
```bash
python -m cli.main version
```

**Show version as JSON:**
```bash
python -m cli.main version --json
```

**Get shell completions:**
```bash
python -m cli.main completions
```

### 🔄 Complete Workflow Example

1. **Generate a project:**
   ```bash
   python -m cli.main generate --description "A simple HTTP server" --sync
   ```

2. **Save the output to a file:**
   ```bash
   python -m cli.main generate --description "A simple HTTP server" --sync > project.txt
   ```

3. **Compile the project:**
   ```bash
   python -m cli.main compile --code project.txt
   ```

4. **If compilation fails, auto-fix:**
   ```bash
   python -m cli.main fix --code project.txt --description "A simple HTTP server" --max-attempts 3
   ```

### 📁 Input File Format

The CLI expects multi-file input in the format:

```
[filename: Cargo.toml]
[package]
name = "my_project"
version = "0.1.0"
edition = "2021"

[filename: src/main.rs]
fn main() {
    println!("Hello, world!");
}
```

### 🌐 Environment Variables

- `RUSTCODER_SERVER`: Base URL of the RustCoder API (default: `http://localhost:8000`)

### 📝 Output Formats

- **Human-readable**: Default output with colors and formatting
- **JSON**: Use `--json` flag for machine-readable output
- **File redirection**: Pipe output to files or other commands

---

## 🔧 MCP (Model-Compiler-Processor) tools

The MCP server is available via the HTTP SSE transport via the `http://localhost:3000/sse` URL. The MCP server can be accessed using the [cmcp command-line client](https://github.com/RussellLuo/cmcp). To install the `cmcp` tool,

```bash
pip install cmcp
```

### 🎯 Generate a new project

**tool:** `generate`

#### 📥 Request example:

```bash
cmcp http://localhost:3000 tools/call name=generate arguments:='{"description": "A command-line calculator in Rust", "requirements": "Should support addition, subtraction, multiplication, and division"}'
```

#### 📤 Response:

```json
{
  "meta": null,
  "content": [
    {
      "type": "text",
      "text": "[filename: Cargo.toml] ... [filename: src/main.rs] ... ",
      "annotations": null
    }
  ],
  "isError": false
}
```
### 🩹 Compile and Fix Rust Code

**tool:** `compile_and_fix`

#### 📥 Request example:

```bash
cmcp http://localhost:3000 tools/call name=compile_and_fix arguments:='{"code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\" // Missing closing parenthesis \n}" }'
```

#### 📤 Response:

```json
{
  "meta": null,
  "content": [
    {
      "type": "text",
      "text": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\"); \n}",
      "annotations": null
    }
  ],
  "isError": false
}
```

---

## 📂 Project Structure

```
Rust_coder_lfx/
├── app/                  # Application code
│   ├── compiler.py       # Rust compilation handling
│   ├── llm_client.py     # LLM API client
│   ├── llm_tools.py      # Tools for LLM interactions
│   ├── load_data.py      # Data loading utilities
│   ├── main.py           # FastAPI application & endpoints
│   ├── mcp_tools.py      # MCP-specific tools
│   ├── prompt_generator.py # LLM prompt generation
│   ├── response_parser.py # Parse LLM responses into files
│   ├── utils.py          # Utility functions
│   └── vector_store.py   # Vector database interface
├── data/                 # Data storage
│   ├── error_examples/   # Error examples for vector search
│   └── project_examples/ # Project examples for vector search
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker configuration
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

---


## 🧠 How It Works

Vector Search: The system uses Qdrant for storing and searching project examples and error solutions.

LLM Integration: Communicates with LlamaEdge API for code generation and error fixing via `llm_client.py`.

Compilation Feedback Loop: Automatically compiles, detects errors, and fixes them using `compiler.py`.

File Parsing: Converts LLM responses into project files with `response_parser.py`.

### Architecture

REST API Interface (app/main.py): FastAPI application exposing HTTP endpoints for project generation, compilation, and error fixing.

MCP Interface (mcp_server.py, app/mcp_service.py): Server-Sent Events interface for the same functionality.

Vector Database (app/vector_store.py): Qdrant is used for storing and searching similar projects and error examples.

LLM Integration (app/llm_client.py): Communicates with LLM APIs (like Gaia nodes) for code generation and error fixing.

Compilation Pipeline (app/compiler.py): Handles Rust code compilation, error detection, and provides feedback for fixing.

### Process Flow

Project Generation:

* User provides a description and requirements
* System creates a prompt using templates
* LLM generates a complete Rust project
* Response is parsed into individual files (`app/response_parser.py`)
* Project is compiled to verify correctness

Error Fixing:

* System attempts to compile the provided code
* If errors occur, they're extracted and analyzed
* Vector search may find similar past errors
* LLM receives the errors and original code to generate fixes
* Process repeats until successful or max attempts reached

---

## 📊 Advanced: Enhancing Performance with Vector Search

The system uses vector embeddings to find similar projects and error examples, which helps improve code generation quality. Here's how to add your own examples:

### 🔧 Creating Vector Collections

First, you need to create the necessary collections in Qdrant using these `curl` commands:

```bash
# Create project_examples collection with 768 dimensions (default)
curl -X PUT "http://localhost:6333/collections/project_examples" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'

# Create error_examples collection with 768 dimensions (default)
curl -X PUT "http://localhost:6333/collections/error_examples" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'
```

> Note: If you've configured a different embedding size via `LLM_EMBED_SIZE` environment variable, replace 768 with that value.

### 🗂️ Adding Data to Vector Collections

#### Method 1: Using Python API Directly

For Project Examples

```python
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore

# Initialize the components
llm_client = LlamaEdgeClient()
vector_store = QdrantStore()

# Ensure collection exists
vector_store.create_collection("project_examples")

# 1. Prepare your data
project_data = {
    "query": "A command-line calculator in Rust",
    "example": "Your full project example with code here...",
    "project_files": {
        "src/main.rs": "fn main() {\n    println!(\"Hello, calculator!\");\n}",
        "Cargo.toml": "[package]\nname = \"calculator\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]"
    }
}

# 2. Get embedding for the query text
embedding = llm_client.get_embeddings([project_data["query"]])[0]

# 3. Add to vector database
vector_store.add_item(
    collection_name="project_examples",
    vector=embedding,
    item=project_data
)
```

For Error Examples:

```python
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore

# Initialize the components
llm_client = LlamaEdgeClient()
vector_store = QdrantStore()

# Ensure collection exists
vector_store.create_collection("error_examples")

# 1. Prepare your error data
error_data = {
    "error": "error[E0502]: cannot borrow `*self` as mutable because it is also borrowed as immutable",
    "solution": "Ensure mutable and immutable borrows don't overlap by using separate scopes",
    "context": "This error occurs when you try to borrow a value mutably while an immutable borrow exists",
    "example": "// Before (error)\nfn main() {\n    let mut v = vec![1, 2, 3];\n    let first = &v[0];\n    v.push(4); // Error: cannot borrow `v` as mutable\n    println!(\"{}\", first);\n}\n\n// After (fixed)\nfn main() {\n    let mut v = vec![1, 2, 3];\n    {\n        let first = &v[0];\n        println!(\"{}\", first);\n    } // immutable borrow ends here\n    v.push(4); // Now it's safe to borrow mutably\n}"
}

# 2. Get embedding for the error message
embedding = llm_client.get_embeddings([error_data["error"]])[0]

# 3. Add to vector database
vector_store.add_item(
    collection_name="error_examples",
    vector=embedding,
    item=error_data
)
```

### Method 2: Adding Multiple Examples from JSON Files

First, ensure you have the required dependencies:
```bash
pip install qdrant-client openai
```

Place JSON files in the appropriate directories:

* Project examples: `data/project_examples`
* Error examples: `data/error_examples`

Format for project examples (with optional `project_files` field):

```json
{
  "query": "Description of the project",
  "example": "Full example code or description",
  "project_files": {
    "src/main.rs": "// File content here",
    "Cargo.toml": "// File content here"
  }
}
```

Format for error examples:
```json
{
  "error": "Rust compiler error message",
  "solution": "How to fix the error",
  "context": "Additional explanation (optional)",
  "example": "// Code example showing the fix (optional)"
}
```

Then run the data loading script:

```
python -c "from app.load_data import load_project_examples, load_error_examples; load_project_examples(); load_error_examples()"
```

#### Method 3: Using the `parse_and_save_qna.py` Script

For bulk importing from a Q&A format text file:

Place your Q&A pairs in a text file with format similar to `QnA_pair.txt`
Modify the `parse_and_save_qna.py` script to point to your file.
Run the script:

```
python parse_and_save_qna.py
```

## ⚙️ Environment Variables for Vector Search

The `SKIP_VECTOR_SEARCH` environment variable controls whether the system uses vector search:

* `SKIP_VECTOR_SEARCH=true` - Disables vector search functionality
* `SKIP_VECTOR_SEARCH=false` (or not set) - Enables vector search

By default, vector search is disabled. To enable it:

- Change to `SKIP_VECTOR_SEARCH=false` in your `.env` file
- Ensure you have a running Qdrant instance (via Docker Compose or standalone)
- Create the collections as shown above

## 🤝 Contributing

Contributions are welcome! This project uses the Developer Certificate of Origin (DCO) to certify that contributors have the right to submit their code. Follow these steps:

* Fork the repository
* Create your feature branch `git checkout -b feature/amazing-feature`
* Make your changes
* Commit your changes with a sign-off `git commit -s -m 'Add some amazing feature'`
* Push to the branch `git push origin feature/amazing-feature`
* Open a Pull Request

The `-s` flag will automatically add a signed-off-by line to your commit message:

```
Signed-off-by: Your Name <your.email@example.com>
```

This certifies that you wrote or have the right to submit the code you're contributing according to the Developer Certificate of Origin. 

---

## 📜 License

Licensed under [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html).






