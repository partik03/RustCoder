# Claude Desktop Setup for RustCoder

**Complete guide to integrating RustCoder with Claude Desktop via MCP**

---

## 🚀 Quick Start

### Step 1: Start RustCoder Backend

```bash
cd /Users/partiksingh/RustCoder
docker-compose up -d
```

**Wait for:** "Application startup complete"

---

### Step 2: Find Your Claude Desktop Config

**Location by OS:**

| OS | Path |
|----|------|
| **Mac** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |

**Create the file if it doesn't exist:**
```bash
# Mac
mkdir -p ~/Library/Application\ Support/Claude/
touch ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
mkdir -p ~/.config/Claude/
touch ~/.config/Claude/claude_desktop_config.json
```

---

### Step 3: Add RustCoder MCP Server

**Edit `claude_desktop_config.json` and add:**

```json
{
  "mcpServers": {
    "rustcoder": {
      "command": "docker",
      "args": [
        "compose",
        "-f",
        "/Users/partiksingh/RustCoder/docker-compose.yml",
        "exec",
        "-T",
        "mcp-server",
        "python",
        "app/mcp_tools.py"
      ],
      "env": {
        "API_HOST": "api",
        "API_PORT": "8000"
      }
    }
  }
}
```

**⚠️ IMPORTANT:** Replace `/Users/partiksingh/RustCoder` with your actual absolute path!

**To find your path:**
```bash
cd /Users/partiksingh/RustCoder
pwd
```

---

### Step 4: Restart Claude Desktop

1. **Quit Claude Desktop completely** (Cmd+Q on Mac)
2. **Restart Claude Desktop**
3. Wait for it to fully load

---

### Step 5: Test Integration

**In Claude Desktop, type:**
```
What MCP tools do you have from RustCoder?
```

**Expected Response:**
```
I have the following RustCoder MCP tools:
- analyze_python_project
- convert_python_to_rust
- convert_python_file_to_rust
- set_model
- get_current_model
- generate
- compile_and_fix
- compile
```

---

## 🛠️ Available Tools

### 1. analyze_python_project
**Purpose:** Analyze Python code structure  
**Use:** Before conversion to understand project

**Example:**
```
Analyze my Python project at /Users/partiksingh/my_app
```

---

### 2. convert_python_to_rust
**Purpose:** Convert entire Python project to Rust  
**Use:** Full project conversion with auto-fixing

**Example:**
```
Convert my Python project at /Users/partiksingh/calculator to Rust.
It's a CLI calculator with add, subtract, multiply, divide operations.
```

---

### 3. convert_python_file_to_rust
**Purpose:** Convert single Python file  
**Use:** Quick conversion of individual files

**Example:**
```
Convert this Python file to Rust: /Users/partiksingh/app.py
It's a simple Flask web server.
```

---

### 4. set_model
**Purpose:** Change LLM model for conversions  
**Use:** Switch between Claude, Gemini, or local models

**Example:**
```
Set RustCoder model to claude-sonnet
```

**Available Models:**
- `claude-sonnet` - Claude Sonnet 4.5 (recommended)
- `claude-opus` - Claude Opus 4 (most capable)
- `gemini` - Gemini Pro
- `local` - Local/Gaia model

---

### 5. get_current_model
**Purpose:** Check active model  
**Use:** See what model is being used

**Example:**
```
What model is RustCoder currently using?
```

---

### 6. generate
**Purpose:** Generate new Rust project from description  
**Use:** Create Rust code from scratch

**Example:**
```
Generate a Rust CLI tool that parses CSV files
```

---

### 7. compile_and_fix
**Purpose:** Compile Rust code with auto-fixing  
**Use:** Fix compilation errors automatically

**Example:**
```
Compile this Rust code and fix any errors: [paste code]
```

---

### 8. compile
**Purpose:** Just compile Rust code  
**Use:** Check if code compiles

**Example:**
```
Check if this Rust code compiles: [paste code]
```

---

## 🎯 Usage Examples

### Example 1: Analyze Before Converting

```
User: I have a Python Flask app at /Users/me/myapp. 
      Can you analyze it first?

Claude: [Uses analyze_python_project]

User: Great! Now convert it to Rust using Actix-web.

Claude: [Uses convert_python_to_rust with the description]
```

---

### Example 2: Convert Single File

```
User: Convert /Users/me/calculator.py to Rust.
      It's a simple calculator with add/subtract functions.

Claude: [Uses convert_python_file_to_rust]
```

---

### Example 3: Switch Models

```
User: Set the conversion model to Claude Opus for better quality.

Claude: [Uses set_model with "claude-opus"]

User: Now convert my complex Flask app.

Claude: [Uses convert_python_to_rust with Claude Opus]
```

---

## 🐛 Troubleshooting

### Issue 1: Tools Not Showing Up

**Symptom:** Claude says "I don't have RustCoder tools"

**Solutions:**
1. Check backend is running: `docker-compose ps`
2. Verify config path is correct (absolute path!)
3. Restart Claude Desktop completely
4. Check logs: `docker-compose logs mcp-server`

---

### Issue 2: Connection Errors

**Symptom:** "Error connecting to RustCoder"

**Solutions:**
1. Ensure backend is running: `docker-compose up -d`
2. Check API is accessible: `curl http://localhost:8000/docs`
3. Verify docker containers are healthy: `docker-compose ps`
4. Check firewall/network settings

---

### Issue 3: Tool Execution Fails

**Symptom:** "Tool execution failed"

**Solutions:**
1. Check backend logs: `docker-compose logs -f`
2. Verify paths are absolute (not relative)
3. Ensure LLM API is configured (check .env)
4. Test manually with MCP client: `cmcp http://localhost:3000 tools/list`

---

### Issue 4: Model Selection Not Working

**Symptom:** "Model change failed"

**Solutions:**
1. Check available models: Use `get_current_model` tool
2. Verify model name is correct (claude-sonnet, not claude-4-sonnet)
3. Ensure API keys are set for commercial models
4. Check config endpoint: `curl http://localhost:8000/config/model`

---

## 📝 Configuration Tips

### Using Multiple MCP Servers

If you have other MCP servers, add RustCoder to the existing config:

```json
{
  "mcpServers": {
    "other-server": {
      "command": "...",
      "args": [...]
    },
    "rustcoder": {
      "command": "docker",
      "args": [
        "compose",
        "-f",
        "/Users/partiksingh/RustCoder/docker-compose.yml",
        "exec",
        "-T",
        "mcp-server",
        "python",
        "app/mcp_tools.py"
      ],
      "env": {
        "API_HOST": "api",
        "API_PORT": "8000"
      }
    }
  }
}
```

---

### Custom Environment Variables

Add custom env vars to the `env` section:

```json
{
  "mcpServers": {
    "rustcoder": {
      "command": "docker",
      "args": [...],
      "env": {
        "API_HOST": "api",
        "API_PORT": "8000",
        "PREFERRED_MODEL": "claude-sonnet",
        "MAX_FIX_ATTEMPTS": "5"
      }
    }
  }
}
```

---

## 🔍 Verification Checklist

Before using RustCoder in Claude Desktop:

- [ ] Backend running: `docker-compose ps` shows all containers up
- [ ] API accessible: `curl http://localhost:8000/docs` returns HTML
- [ ] MCP server responsive: `cmcp http://localhost:3000 tools/list` works
- [ ] Config file has correct absolute path
- [ ] Claude Desktop restarted
- [ ] Tools visible in Claude: Ask "What MCP tools do you have?"

---

## ⚡ Advanced: Direct MCP Connection

If you prefer not to use Docker for the MCP connection:

```json
{
  "mcpServers": {
    "rustcoder": {
      "command": "python",
      "args": [
        "/Users/partiksingh/RustCoder/app/mcp_tools.py"
      ],
      "env": {
        "API_HOST": "localhost",
        "API_PORT": "8000",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**Note:** Backend must still run separately: `docker-compose up api`

---

## 📊 Performance Tips

### 1. Keep Backend Running
```bash
# Start in detached mode
docker-compose up -d

# Check status
docker-compose ps

# Stop when done
docker-compose down
```

### 2. Optimize Docker Resources
In Docker Desktop settings:
- Memory: 4GB minimum
- CPUs: 2+ cores recommended

### 3. Use Local Models for Speed
```
Set model to local for faster conversions
```

---

## 🎓 Best Practices

### 1. Always Use Absolute Paths
❌ Bad: `Analyze ./my_project`  
✅ Good: `Analyze /Users/partiksingh/my_project`

### 2. Provide Context
❌ Bad: `Convert app.py`  
✅ Good: `Convert /Users/me/app.py - it's a Flask REST API with user authentication`

### 3. Start with Analysis
```
1. Analyze the project first
2. Review analysis results
3. Then convert to Rust
```

### 4. Test Generated Code
```
1. Get Rust code from conversion
2. Save to files
3. Run cargo build
4. Fix any remaining issues
```

---

## 🔗 Related Documentation

- **USAGE_EXAMPLES.md** - More detailed examples
- **TASK5_COMPLETE.md** - Full conversion pipeline docs
- **TASK6_RESULTS.md** - Testing and edge cases
- **README_TASKS_5_6.md** - Quick start guide

---

## ✅ Success Checklist

Setup complete when:

- [x] Claude Desktop shows RustCoder tools
- [x] Can analyze Python projects
- [x] Can convert Python to Rust
- [x] Can switch models
- [x] Tools execute without errors
- [x] Generated Rust code is valid

---

## 🎉 You're Ready!

**Try your first conversion:**
```
Convert the test project at /Users/partiksingh/RustCoder/tests/integration/simple_cli to Rust.
It's a CLI calculator with argparse.
```

**Claude will:**
1. Analyze the Python code
2. Generate Rust equivalent
3. Compile and fix errors
4. Return complete Rust project

---

**Questions?** Check troubleshooting section or review the logs.

**Happy converting! 🦀**

