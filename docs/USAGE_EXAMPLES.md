# RustCoder Usage Examples

**Practical examples for using RustCoder with Claude Desktop**

---

## 🚀 Getting Started

### Check Available Tools

**Ask Claude:**
```
What MCP tools do you have from RustCoder?
```

**Expected Response:**
```
I have these RustCoder tools:
- analyze_python_project
- convert_python_to_rust
- convert_python_file_to_rust
- set_model
- get_current_model
- generate
- compile
- compile_and_fix
```

---

## 🔧 Model Management

### Check Current Model

**Ask Claude:**
```
What model is RustCoder currently using?
```

**Claude will use:** `get_current_model` tool

**Response:**
```
Current Model Configuration:

Active Model: local
Full Name: Qwen2.5-Coder-3B-Instruct

Available Models:
  - claude-sonnet
  - claude-opus
  - gemini
  - local
```

---

### Switch to Claude Sonnet

**Ask Claude:**
```
Set RustCoder to use Claude Sonnet for better conversion quality
```

**Claude will use:** `set_model(model="claude-sonnet")`

**Response:**
```
✓ Model set successfully!

Model: claude-sonnet
Full Name: claude-sonnet-4-5

This model will be used for all future conversions.
```

---

### Switch to Local Model (Faster)

**Ask Claude:**
```
Switch RustCoder back to the local model for faster conversions
```

**Claude will use:** `set_model(model="local")`

---

## 📊 Python Project Analysis

### Simple Analysis

**Ask Claude:**
```
Analyze my Python project at /Users/me/calculator
```

**Claude will use:** `analyze_python_project`

**Response:**
```
Python Project Analysis
==================================================

Project: /Users/me/calculator
Total Files: 3
Total Functions: 12
Total Classes: 2

Dependencies:
  - argparse
  - typing

Recommended Rust Crates:
  - argparse → clap = "4.0"
  - typing → # Use Rust's built-in type system

Ready for conversion: Yes
```

---

### Detailed Analysis Before Conversion

**Conversation:**
```
User: I have a Flask web application at /Users/me/myapp. 
      Can you analyze it and tell me if it's suitable for Rust conversion?

Claude: [Uses analyze_python_project]

      Your Flask app has 5 files, 18 functions, and 3 classes.
      
      Dependencies:
      - flask → actix-web or axum
      - sqlalchemy → diesel or sqlx
      - pytest → built-in Rust tests
      
      It should convert well to Rust! Ready to proceed?

User: Yes, convert it using Actix-web

Claude: [Uses convert_python_to_rust with description]
```

---

## 🦀 Python to Rust Conversion

### Convert Full Project

**Ask Claude:**
```
Convert my Python project at /Users/me/calculator to Rust.

The project is a command-line calculator that:
- Accepts two numbers and an operation (add, subtract, multiply, divide)
- Uses argparse for CLI arguments
- Has error handling for division by zero
- Includes unit tests
```

**Claude will use:** `convert_python_to_rust`

**Response:**
```
[filename: Cargo.toml]
[package]
name = "calculator"
version = "0.1.0"
edition = "2021"

[dependencies]
clap = { version = "4.0", features = ["derive"] }
anyhow = "1.0"

[filename: src/main.rs]
use clap::Parser;
use anyhow::Result;

#[derive(Parser)]
struct Args {
    operation: String,
    a: f64,
    b: f64,
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    let result = match args.operation.as_str() {
        "add" => args.a + args.b,
        "subtract" => args.a - args.b,
        "multiply" => args.a * args.b,
        "divide" => {
            if args.b == 0.0 {
                anyhow::bail!("Cannot divide by zero");
            }
            args.a / args.b
        },
        _ => anyhow::bail!("Unknown operation"),
    };
    
    println!("Result: {}", result);
    Ok(())
}

[filename: README.md]
# Converted Python to Rust Calculator
...
```

---

### Convert Single File

**Ask Claude:**
```
Convert this Python file to Rust: /Users/me/utils.py

It contains helper functions for:
- Parsing CSV files
- Data validation
- Simple statistics (mean, median, mode)
```

**Claude will use:** `convert_python_file_to_rust`

---

### Conversion with Specific Framework

**Ask Claude:**
```
Convert /Users/me/api.py to Rust using Axum web framework.

The file is a Flask REST API with:
- GET /users endpoint
- POST /users endpoint  
- JSON serialization
- Basic authentication
```

**Claude includes the description in the conversion request**

---

## 🔄 Iterative Conversion

### Strategy 1: Analyze, Review, Convert

**Conversation:**
```
User: I want to convert /Users/me/myapp but I'm not sure if it will work

Claude: Let me analyze it first
        [Uses analyze_python_project]
        
        Your project uses:
        - asyncio (will use tokio)
        - aiohttp (will use reqwest)
        - dataclasses (will use structs)
        
        This should convert well! Shall I proceed?

User: Yes, please use Claude Opus for best quality

Claude: [Uses set_model with claude-opus]
        [Then uses convert_python_to_rust]
```

---

### Strategy 2: Convert and Iterate

**Conversation:**
```
User: Convert /Users/me/script.py but make it use idiomatic Rust patterns

Claude: [Uses convert_python_to_rust with detailed description]

User: The error handling isn't quite right. Can you regenerate with better Result types?

Claude: [Uses convert_python_file_to_rust again with improved description]
```

---

## 🎯 Advanced Usage

### Comparing Models

**Conversation:**
```
User: Convert /Users/me/complex_app.py twice - once with local model, once with Claude Opus

Claude: Converting with local model first...
        [Uses set_model("local")]
        [Uses convert_python_to_rust]
        
        Here's version 1. Now with Claude Opus...
        [Uses set_model("claude-opus")]
        [Uses convert_python_to_rust]
        
        Here's version 2. The Opus version has:
        - More idiomatic error handling
        - Better type safety
        - More comprehensive comments
```

---

### Framework Migration

**Ask Claude:**
```
I have a Django project at /Users/me/djangoapp with these models:
- User (authentication)
- Post (blog posts)
- Comment (post comments)

Convert it to a Rust web service using Axum and Diesel ORM.
Include database migrations.
```

**Claude will:**
1. Analyze the Django project
2. Use convert with detailed description
3. Generate Axum routes
4. Generate Diesel models and migrations
5. Provide complete Cargo project

---

## 💡 Pro Tips

### 1. Be Specific with Descriptions

❌ **Bad:**
```
Convert /Users/me/app.py
```

✅ **Good:**
```
Convert /Users/me/app.py - it's a FastAPI REST API with:
- User authentication using JWT tokens
- PostgreSQL database with SQLAlchemy
- Async endpoints for data processing
- Websocket support for real-time updates

Use Axum for the web framework and Tokio-Postgres for the database.
```

---

### 2. Always Use Absolute Paths

❌ **Bad:**
```
Convert ./my_project
```

✅ **Good:**
```
Convert /Users/me/projects/my_project
```

---

### 3. Analyze Before Complex Conversions

**Recommended Flow:**
```
1. Analyze the project
2. Review dependencies and complexity
3. Choose appropriate model (Opus for complex, Sonnet for balanced, local for simple)
4. Provide detailed description
5. Convert
6. Review and iterate if needed
```

---

### 4. Specify Output Framework

When converting web apps, specify the Rust framework:
- Flask/FastAPI → **Axum** or **Actix-web**
- Django → **Axum + Diesel**
- Async scripts → **Tokio**

---

### 5. Test Generated Code

Always:
1. Save the generated Rust code
2. Run `cargo build`
3. Fix any remaining compilation errors
4. Run `cargo test`
5. Verify behavior matches Python version

---

## 🔍 Troubleshooting Examples

### Issue: Conversion Failed

**Conversation:**
```
User: Convert /Users/me/app.py failed with an error

Claude: Let me check the configuration
        [Uses get_current_model]
        
        You're using the local model. For better quality, try:
        [Uses set_model("claude-sonnet")]
        
        Now let's try again with more context about your app...
```

---

### Issue: Generated Code Doesn't Compile

**Conversation:**
```
User: The generated Rust code has compilation errors

Claude: Let me help fix that. Please paste the error message.

User: [pastes error]

Claude: [Uses compile_and_fix tool with the code]
        
        Here's the fixed version...
```

---

## 📚 Example Projects

### Example 1: CLI Tool

**Input:** Python argparse CLI  
**Output:** Rust with clap  
**Complexity:** Low  
**Recommended Model:** local or claude-sonnet

**Prompt:**
```
Convert /Users/me/cli_tool.py

It's a CLI tool for parsing log files with:
- Argparse for command-line arguments
- File I/O for reading logs
- Regex for pattern matching  
- CSV output for results
```

---

### Example 2: Web API

**Input:** Flask REST API  
**Output:** Rust with Axum  
**Complexity:** Medium  
**Recommended Model:** claude-sonnet or claude-opus

**Prompt:**
```
Convert /Users/me/api.py to Rust using Axum

It's a REST API with:
- 5 GET endpoints
- 3 POST endpoints
- JSON request/response
- JWT authentication
- PostgreSQL database via SQLAlchemy

Include proper error handling and async/await.
```

---

### Example 3: Data Processing Script

**Input:** Python async script with aiohttp  
**Output:** Rust with Tokio and Reqwest  
**Complexity:** Medium  
**Recommended Model:** claude-sonnet

**Prompt:**
```
Convert /Users/me/processor.py

An async script that:
- Fetches data from multiple APIs concurrently
- Processes JSON responses
- Aggregates results
- Saves to CSV file

Uses aiohttp and asyncio.
```

---

## 🎓 Best Practices Summary

### Before Converting
1. ✅ Analyze the project first
2. ✅ Check dependencies
3. ✅ Choose appropriate model
4. ✅ Use absolute paths

### During Conversion
1. ✅ Provide detailed description
2. ✅ Specify target frameworks
3. ✅ Mention special requirements
4. ✅ Include context about complexity

### After Conversion
1. ✅ Save generated code
2. ✅ Run cargo build
3. ✅ Review for correctness
4. ✅ Test functionality
5. ✅ Iterate if needed

---

## 🚀 Quick Reference

| Task | Claude Prompt |
|------|---------------|
| Check model | `What model is RustCoder using?` |
| Set model | `Set RustCoder to use claude-sonnet` |
| Analyze project | `Analyze /Users/me/project` |
| Convert project | `Convert /Users/me/project to Rust` |
| Convert file | `Convert /Users/me/file.py to Rust` |
| Get help | `What can RustCoder do?` |

---

## 📖 Related Documentation

- **CLAUDE_DESKTOP_SETUP.md** - Setup instructions
- **TASK5_COMPLETE.md** - Technical details
- **TASK6_RESULTS.md** - Testing information
- **README_TASKS_5_6.md** - Quick start guide

---

**Happy converting! 🦀**

