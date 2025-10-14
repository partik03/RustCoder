# Dynamic Conversion - Quick Start Guide

**TL;DR:** RustCoder now uses LLM to dynamically suggest Rust crates instead of hardcoded mappings!

---

## 🚀 Quick Usage

### CLI (Recommended)

```bash
# Auto-select recommended crates
python -m cli.main convert ./my_python_project --auto

# Interactive mode (choose crates yourself)
python -m cli.main convert ./my_python_project --desc "Web API"
```

### API

```bash
curl -X POST http://localhost:8000/convert-python-to-rust \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "description": "Flask web app",
    "interactive": false
  }'
```

### Python

```python
from pathlib import Path
from app.converters.python_converter import PythonConverter
from app.llm_client import LlamaEdgeClient

converter = PythonConverter()
llm_client = LlamaEdgeClient()

# Analyze and get crate suggestions
context = converter.analyze_and_prepare_with_crates(
    Path("./my_project"),
    description="CLI tool",
    interactive=False,  # Auto-select
    llm_client=llm_client
)

# Check what was selected
print(context["selected_crates"])
# {
#   "click": {"name": "clap", "version": "4.0", "reason": "...", "recommended": True}
# }

# Generate conversion prompt
prompt = converter.generate_conversion_prompt_dynamic(context, "CLI tool")

# Use with your LLM...
```

---

## 📦 What Happens

### 1. Analysis
```
📊 Analyzing Python project...
```
- Scans all `.py` files
- Detects imports: `flask`, `requests`, etc.

### 2. LLM Suggests Crates
```
🤖 Asking LLM to analyze dependencies and suggest Rust crates...
```
- LLM receives your code + dependencies
- Suggests 2-3 options per dependency
- Provides reasoning for each

### 3. Selection

**Auto Mode (`--auto`):**
```
✓ Auto-selected recommended crates
```

**Interactive Mode:**
```
Python: flask
┌───┬───────────┬─────────┬──────────────────────┬────┐
│ # │ Crate     │ Version │ Reason               │ ⭐ │
├───┼───────────┼─────────┼──────────────────────┼────┤
│ 1 │ axum      │ 0.7     │ Modern, fast         │ ✓  │
│ 2 │ actix-web │ 4.0     │ Mature, performant   │    │
└───┴───────────┴─────────┴──────────────────────┴────┘
Select crate for flask [1]: 
```

### 4. Conversion
```
📝 Generating conversion prompt with LLM-selected crates...
🤖 Converting with LLM...
```
- LLM generates Rust code
- Uses ONLY your selected crates
- Creates proper project structure

### 5. Result
```
✅ Conversion successful!

📦 Rust Crates (LLM-selected):
  • flask → axum v0.7
    Modern async framework built on Tower
  • requests → reqwest v0.11
    Most popular HTTP client

💾 Rust project saved to: ./converted
🎉 Rust project compiles successfully!
```

---

## 🎯 Key Benefits

| Feature | Benefit |
|---------|---------|
| **Dynamic** | No outdated hardcoded mappings |
| **Multiple Options** | Choose what fits your needs |
| **Reasoning** | Understand why each crate suggested |
| **Context-Aware** | LLM considers your specific use case |
| **User Control** | Interactive or auto mode |

---

## 💡 Examples

### Example 1: Simple CLI

**Python:**
```python
import click

@click.command()
def hello():
    click.echo("Hello!")
```

**LLM Suggests:**
- `clap v4.0` (recommended) - "Standard CLI library with derive macros"
- `structopt v0.3` - "Older but stable, built on clap"

**Result (Cargo.toml):**
```toml
[dependencies]
clap = { version = "4.0", features = ["derive"] }
```

### Example 2: Web API

**Python:**
```python
from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/data')
def get_data():
    resp = requests.get('https://api.example.com')
    return jsonify(resp.json())
```

**LLM Suggests:**
- Flask:
  - `axum v0.7` (recommended) - "Modern, composable, Tower-based"
  - `actix-web v4.0` - "Mature, battle-tested, very fast"
- Requests:
  - `reqwest v0.11` (recommended) - "De facto HTTP client"
  - `ureq v2.9` - "Simpler, sync-only"

**Result (Cargo.toml):**
```toml
[dependencies]
axum = "0.7"
reqwest = { version = "0.11", features = ["json"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

---

## 🔧 Flags & Options

### CLI Flags

```bash
python -m cli.main convert <path> [OPTIONS]

Options:
  --desc TEXT      Project description (helps LLM suggest better crates)
  --auto          Auto-select recommended crates (no interaction)
  -o, --output    Output directory [default: ./converted]
  -l, --language  Source language [default: python]
```

### API Parameters

```json
{
  "project_path": "/path/to/project",     // Required
  "description": "Optional description",  // Helps LLM
  "interactive": false,                   // true = user selects, false = auto
  "max_fix_attempts": 3                   // Compilation fix attempts
}
```

---

## ❓ FAQ

### Q: Can I still use hardcoded mappings?
**A:** Yes, but deprecated. Use `--legacy` flag (not implemented yet) or migrate to dynamic approach.

### Q: What if LLM suggests wrong crate?
**A:** In interactive mode, choose a different option. In auto mode, use interactive first time to verify.

### Q: How do I force a specific crate?
**A:** Currently, select in interactive mode. Future: config file or CLI option.

### Q: Does it work offline?
**A:** Needs LLM access. Use local LLM (like Qwen) for offline use.

### Q: What about crate versions?
**A:** LLM suggests versions. Future: auto-update to latest from crates.io.

---

## 🐛 Troubleshooting

### Issue: "LLM analysis failed"
**Solution:** Check LLM connection. Fallback suggestions will be used.

### Issue: "No suggestions for dependency X"
**Solution:** LLM couldn't find Rust equivalent. Manual research needed (marked as TODO in output).

### Issue: "Interactive mode not working"
**Solution:** Use `--auto` flag for non-interactive environments (CI/CD).

---

## 📚 Further Reading

- **Full Documentation:** `TASK8_DYNAMIC_CONVERSION_COMPLETE.md`
- **Code:** `app/crate_suggester.py`, `app/interactive_selector.py`
- **Examples:** `TASK8_DYNAMIC_CONVERSION_COMPLETE.md` (Usage Examples section)

---

**Happy Converting! 🦀**

