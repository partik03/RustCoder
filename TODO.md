# RustCoder Enhancement TODO
## Python/C++ to Rust Conversion Feature

**Project Goal:** Add Claude Code integration for converting Python/C++ projects to Rust

**Status:** Planning Phase  
**Last Updated:** October 10, 2025

---

## 🎯 Quick Wins (Easy to Implement)

### Infrastructure (Already Built - Just Use Them!)

- [x] ✅ **LLM Client Infrastructure**
  - Already supports OpenAI-compatible APIs
  - Has fallback mechanisms
  - Can be used as-is for conversion prompts
  - **Location:** `app/llm_client.py`

- [x] ✅ **MCP Server Framework**
  - FastMCP makes tool registration trivial (`@mcp.tool()`)
  - Just add new functions with type hints
  - **Location:** `app/mcp_tools.py`
  - **Action:** Add 3 new tool functions (15-30 minutes each)

- [x] ✅ **FastAPI REST Backend**
  - Easy to add new endpoints
  - Existing pattern to follow
  - **Location:** `app/main.py`
  - **Action:** Add 3 new endpoints (30-60 minutes each)

- [x] ✅ **Response Parser**
  - `[filename: ...]` format works for Rust output
  - Multi-level fallback parsing is robust
  - **Location:** `app/response_parser.py`
  - **Action:** No changes needed!

- [x] ✅ **Compiler Wrapper**
  - Can compile converted Rust code
  - Error extraction works
  - **Location:** `app/compiler.py`
  - **Action:** No changes needed!

- [x] ✅ **Vector Search / RAG**
  - Qdrant infrastructure ready
  - Just need to add new collections
  - **Location:** `app/vector_store.py`
  - **Action:** Add 2 new collections (10 minutes)

- [x] ✅ **Iterative Error Fixing**
  - Already implemented in `compile_and_fix`
  - Will work for converted code too
  - **Action:** Just reuse existing logic

---

### Low-Hanging Fruit (Quick Implementations)

- [ ] 🟢 **Add Basic MCP Tools** (Effort: 2-3 hours)
  ```python
  @mcp.tool()
  async def convert_to_rust(source_code: str, source_language: str) -> str:
      # Forward to REST API
  ```
  - **Files to modify:** `app/mcp_tools.py` (add 3 functions)
  - **Complexity:** Low - just HTTP forwarding
  - **Blockers:** None

- [ ] 🟢 **Create Conversion Prompt Templates** (Effort: 3-4 hours)
  - **Files to create:** 
    - `templates/python_to_rust.txt`
    - `templates/cpp_to_rust.txt`
  - **Content:** System message + examples + instructions
  - **Complexity:** Low - mostly writing/research
  - **Blockers:** None

- [ ] 🟢 **Add REST Endpoints** (Effort: 4-6 hours)
  ```python
  @app.post("/convert-to-rust")
  async def convert_to_rust(request: dict):
      # Business logic here
  ```
  - **Files to modify:** `app/main.py` (add 3 endpoints)
  - **Complexity:** Medium - follow existing patterns
  - **Blockers:** Need conversion prompts ready

- [ ] 🟢 **Python AST Analyzer** (Effort: 4-6 hours)
  ```python
  import ast
  
  def analyze_python(code: str) -> dict:
      tree = ast.parse(code)
      # Extract functions, classes, imports
  ```
  - **Files to create:** `app/code_analyzer.py`
  - **Complexity:** Low-Medium - use built-in `ast` module
  - **Blockers:** None

---

## 🔴 Gaps (Need to Build from Scratch)

### Critical Path Items

- [ ] 🔴 **Code Analyzer Module** (Effort: 10-15 hours)
  - **Status:** Doesn't exist
  - **What it needs:**
    - Python AST parser (extract functions, classes, imports)
    - C++ pattern detector (regex-based for MVP)
    - Dependency extractor
    - Pattern identifier
  - **Files to create:** `app/code_analyzer.py` (200-300 lines)
  - **Priority:** HIGH - Required for conversion
  - **Approach:**
    ```python
    class CodeAnalyzer:
        def analyze_python(self, code: str) -> dict
        def analyze_cpp(self, code: str) -> dict
        def extract_dependencies(self, code: str, language: str) -> List[str]
        def identify_patterns(self, analysis: dict) -> List[str]
    ```

- [ ] 🔴 **Conversion Prompt System** (Effort: 8-12 hours)
  - **Status:** Doesn't exist
  - **What it needs:**
    - Template loader for conversion prompts
    - Context builder (include analysis, examples)
    - Pattern-specific prompt variations
  - **Files to create:** `app/conversion_prompts.py` (150-200 lines)
  - **Priority:** HIGH - Required for quality conversion
  - **Approach:**
    ```python
    class ConversionPromptGenerator:
        def python_to_rust_prompt(self, code: str, analysis: dict) -> str
        def cpp_to_rust_prompt(self, code: str, analysis: dict) -> str
        def add_pattern_examples(self, prompt: str, patterns: List[str]) -> str
    ```

- [ ] 🔴 **Conversion Examples Dataset** (Effort: 12-20 hours)
  - **Status:** Doesn't exist
  - **What it needs:**
    - 15-20 Python → Rust examples
    - 15-20 C++ → Rust examples
    - JSON format with source + target + explanation
    - Cover common patterns:
      - Functions & parameters
      - Classes & methods
      - File I/O
      - Async/await
      - Data structures (lists, dicts, etc.)
      - Error handling
  - **Files to create:** `data/conversion_examples/` (40+ JSON files)
  - **Priority:** HIGH - RAG depends on this
  - **Format:**
    ```json
    {
      "python_code": "def add(a, b): return a + b",
      "rust_code": "fn add(a: i32, b: i32) -> i32 { a + b }",
      "explanation": "Python functions map to Rust fn",
      "patterns": ["function", "parameters", "return"],
      "difficulty": "easy"
    }
    ```

- [ ] 🟡 **Interop Scaffolding Generator** (Effort: 10-15 hours)
  - **Status:** Doesn't exist
  - **What it needs:**
    - PyO3 binding templates
    - FFI binding templates
    - Cargo.toml configuration for interop
  - **Files to create:** 
    - `app/interop_generator.py` (150-200 lines)
    - `templates/pyo3_bindings.txt`
    - `templates/ffi_bindings.txt`
  - **Priority:** MEDIUM - For gradual migration
  - **Approach:** Generate bindings that allow calling Rust from Python/C++

- [ ] 🟡 **Migration Strategy Planner** (Effort: 15-20 hours)
  - **Status:** Doesn't exist
  - **What it needs:**
    - Project structure analyzer
    - Dependency graph builder
    - Conversion order suggester
    - Risk assessment
  - **Files to create:** `app/migration_planner.py` (250-300 lines)
  - **Priority:** MEDIUM - Nice to have
  - **Approach:** Analyze project, suggest which modules to convert first

---

### Optional Enhancements

- [ ] 🟡 **C++ Parser (Advanced)** (Effort: 20-30 hours)
  - **Status:** Not needed for MVP
  - **What it needs:** libclang integration for real C++ parsing
  - **Priority:** LOW - Start with regex patterns
  - **Approach:** Use simple pattern matching for MVP, add real parsing later

- [ ] 🟡 **CLI Commands** (Effort: 4-6 hours)
  - **Status:** Not critical (MCP tools work)
  - **Files to modify:** `cli/main.py`
  - **Priority:** LOW - Nice to have
  - **Commands:** `convert`, `analyze`, `migrate`

- [ ] 🟡 **Crate Recommendation System** (Effort: 8-12 hours)
  - **Status:** Doesn't exist
  - **What it needs:** Map Python/C++ libraries to Rust crates
  - **Priority:** LOW - Can use LLM knowledge instead
  - **Approach:** Database of library mappings (e.g., requests → reqwest)

---

## ⚠️ Risks & Mitigations

### Technical Risks

1. **🔥 RISK: LLM Conversion Quality**
   - **Problem:** LLM might generate incorrect or non-idiomatic Rust
   - **Impact:** High - Poor conversion quality = unusable tool
   - **Probability:** Medium
   - **Mitigation:**
     - ✅ Use RAG with high-quality examples (vector search)
     - ✅ Leverage existing error-fixing loop (already implemented!)
     - ✅ Include Rust idiom examples in prompts
     - ✅ Compile and fix iteratively until code works
   - **Fallback:** Manual review prompts with suggested improvements

2. **🔥 RISK: C++ Parsing Complexity**
   - **Problem:** C++ is notoriously hard to parse correctly
   - **Impact:** Medium - May not handle complex C++ code
   - **Probability:** High
   - **Mitigation:**
     - ✅ Start with Python (easier to parse)
     - ✅ Use regex for common C++ patterns (good enough for MVP)
     - ✅ Let LLM understand complex C++ semantics (not parser)
     - ⏱️ Add real C++ parser later if needed (libclang)
   - **Fallback:** Support only simple C++ for MVP

3. **⚠️ RISK: Unconvertible Code Patterns**
   - **Problem:** Some Python/C++ patterns have no direct Rust equivalent
   - **Impact:** Medium - Can't convert 100% of code
   - **Probability:** Medium
   - **Examples:**
     - Python metaclasses
     - C++ multiple inheritance
     - Dynamic typing features
   - **Mitigation:**
     - ✅ Provide analysis tool that flags unconvertible patterns
     - ✅ Generate interop bindings for gradual migration
     - ✅ Suggest refactoring strategies in analysis
   - **Fallback:** Document limitations clearly

4. **⚠️ RISK: API Costs (LLM Calls)**
   - **Problem:** Converting large projects = many LLM API calls = $$$
   - **Impact:** Low-Medium - User cost
   - **Probability:** Medium
   - **Mitigation:**
     - ✅ Support local LLMs (already supported!)
     - ⏱️ Cache analysis results to avoid re-parsing
     - ⏱️ Batch multiple files in one LLM call
   - **Fallback:** Recommend local LLM for large projects

5. **⚠️ RISK: Non-Idiomatic Rust Output**
   - **Problem:** Converted code might work but not be idiomatic
   - **Impact:** Low - Code works but isn't "proper" Rust
   - **Probability:** High
   - **Mitigation:**
     - ✅ Include idiom examples in vector DB
     - ✅ Use prompts that emphasize idiomatic patterns
     - ⏱️ Add Clippy integration to suggest improvements
   - **Fallback:** Document as "functional but may need refinement"

---

### Project Risks

6. **⚠️ RISK: Scope Creep**
   - **Problem:** Too many features = never ship
   - **Impact:** High - Project timeline
   - **Probability:** Medium
   - **Mitigation:**
     - ✅ Define clear MVP (Python conversion only)
     - ✅ Prioritize ruthlessly (see TODO sections)
     - ✅ Ship incremental releases
   - **MVP Scope:**
     - ✅ Python → Rust conversion
     - ✅ Basic MCP tools
     - ✅ Compilation with error fixing
     - ❌ C++ support (Phase 2)
     - ❌ Migration planner (Phase 3)
     - ❌ CLI commands (Phase 3)

7. **⚠️ RISK: Integration Complexity**
   - **Problem:** Claude Code integration might have issues
   - **Impact:** Medium - Affects usability
   - **Probability:** Low
   - **Mitigation:**
     - ✅ Use standard MCP protocol (well-documented)
     - ✅ Test with Claude Desktop first (simpler)
     - ✅ Follow existing RustCoder patterns (proven to work)
   - **Fallback:** Provide REST API and CLI as alternatives

---

## 📋 Implementation Checklist

### Phase 1: Foundation (Week 1-2)

**Setup & Testing:**
- [ ] 1.1 Run RustCoder locally with Docker
- [ ] 1.2 Test existing MCP tools with Claude Desktop
- [ ] 1.3 Verify LLM API connectivity
- [ ] 1.4 Test vector search with existing examples

**Example Collection:**
- [ ] 1.5 Research Python → Rust patterns (survey existing resources)
- [ ] 1.6 Create 10 basic Python → Rust examples (functions, classes)
- [ ] 1.7 Create 10 advanced Python → Rust examples (async, file I/O)
- [ ] 1.8 Format all examples as JSON
- [ ] 1.9 Add explanations and pattern tags

**Prompt Design:**
- [ ] 1.10 Study existing RustCoder prompts
- [ ] 1.11 Draft Python → Rust system message
- [ ] 1.12 Create `templates/python_to_rust.txt`
- [ ] 1.13 Test prompts with LLM manually
- [ ] 1.14 Refine based on output quality

**Code Analyzer:**
- [ ] 1.15 Create `app/code_analyzer.py` file
- [ ] 1.16 Implement Python AST parsing
- [ ] 1.17 Extract functions, classes, imports
- [ ] 1.18 Identify patterns (async, classes, etc.)
- [ ] 1.19 Test with sample Python files

---

### Phase 2: Core Conversion (Week 3-4)

**Backend Implementation:**
- [ ] 2.1 Add `POST /convert-to-rust` endpoint in `app/main.py`
- [ ] 2.2 Integrate code analyzer with endpoint
- [ ] 2.3 Implement conversion logic with LLM
- [ ] 2.4 Add vector search for similar examples
- [ ] 2.5 Test endpoint with Postman/curl

**MCP Integration:**
- [ ] 2.6 Add `convert_to_rust()` tool in `app/mcp_tools.py`
- [ ] 2.7 Add `analyze_for_conversion()` tool
- [ ] 2.8 Test with `cmcp` CLI
- [ ] 2.9 Test with Claude Desktop
- [ ] 2.10 Verify response format

**Vector Database:**
- [ ] 2.11 Create conversion example loader
- [ ] 2.12 Load Python → Rust examples into Qdrant
- [ ] 2.13 Test similarity search
- [ ] 2.14 Verify RAG improves quality

**Testing:**
- [ ] 2.15 Convert 5 simple Python scripts
- [ ] 2.16 Verify generated Rust compiles
- [ ] 2.17 Measure success rate
- [ ] 2.18 Document failures and refine prompts

---

### Phase 3: Advanced Features (Week 5-6)

**C++ Support:**
- [ ] 3.1 Create C++ → Rust examples (10-15)
- [ ] 3.2 Create `templates/cpp_to_rust.txt`
- [ ] 3.3 Add C++ pattern detection to analyzer
- [ ] 3.4 Test C++ conversion
- [ ] 3.5 Load C++ examples into vector DB

**Interop Scaffolding:**
- [ ] 3.6 Create `app/interop_generator.py`
- [ ] 3.7 Create PyO3 binding templates
- [ ] 3.8 Add `include_interop` flag to conversion
- [ ] 3.9 Test generated bindings
- [ ] 3.10 Document interop workflow

**Migration Planner (Optional):**
- [ ] 3.11 Create `app/migration_planner.py`
- [ ] 3.12 Add `POST /suggest-migration-strategy` endpoint
- [ ] 3.13 Add MCP tool
- [ ] 3.14 Test with multi-file projects

**CLI (Optional):**
- [ ] 3.15 Add `convert` command to `cli/main.py`
- [ ] 3.16 Add `analyze` command
- [ ] 3.17 Test full CLI workflow

---

### Phase 4: Polish & Documentation (Week 7-8)

**Real-World Testing:**
- [ ] 4.1 Convert small Python library (e.g., utility functions)
- [ ] 4.2 Convert C++ utility (e.g., data structure)
- [ ] 4.3 Measure conversion success rate
- [ ] 4.4 Document common failure patterns
- [ ] 4.5 Refine prompts based on failures

**Documentation:**
- [ ] 4.6 Write usage guide for conversion workflow
- [ ] 4.7 Create Claude Code integration guide
- [ ] 4.8 Document conversion patterns
- [ ] 4.9 Write migration best practices
- [ ] 4.10 Create video demo

**Testing:**
- [ ] 4.11 Unit tests for code analyzer
- [ ] 4.12 Integration tests for conversion endpoints
- [ ] 4.13 MCP tool tests
- [ ] 4.14 Example-based validation

**Performance:**
- [ ] 4.15 Profile LLM call times
- [ ] 4.16 Optimize vector search queries
- [ ] 4.17 Add caching for analysis results

---

## 🎯 MVP Scope (Minimum Viable Product)

**Must Have:**
- ✅ Convert Python code to Rust
- ✅ MCP tool `convert_to_rust(source_code, "python")`
- ✅ MCP tool `analyze_for_conversion(source_code, "python")`
- ✅ Generated Rust code compiles (via existing error-fixing loop)
- ✅ Works with Claude Desktop
- ✅ 10+ Python → Rust examples in vector DB

**Nice to Have (Can Add Later):**
- ⏱️ C++ support
- ⏱️ Interop scaffolding (PyO3)
- ⏱️ Migration strategy suggestions
- ⏱️ CLI commands
- ⏱️ Crate recommendations

**Success Criteria:**
- Can convert simple Python scripts (functions, classes, file I/O)
- 50%+ of conversions compile without manual fixes
- 80%+ of conversions compile after error-fixing loop
- Output is functional (even if not perfectly idiomatic)

---

## 📊 Progress Tracking

**Overall Progress:** 15% (Analysis & Planning Complete)

**Phase Status:**
- [x] Phase 0: Planning & Analysis - DONE ✅
- [ ] Phase 1: Foundation - NOT STARTED 🔴
- [ ] Phase 2: Core Conversion - NOT STARTED 🔴
- [ ] Phase 3: Advanced Features - NOT STARTED 🔴
- [ ] Phase 4: Polish & Documentation - NOT STARTED 🔴

**Next Action:** Set up development environment and test existing tools

---

## 💡 Notes & Ideas

### Potential Optimizations

1. **Batch Conversion:** Convert multiple files in one LLM call
2. **Caching:** Store analysis results to avoid re-parsing
3. **Incremental:** Only re-analyze changed files
4. **Parallel:** Run multiple LLM calls concurrently

### Future Enhancements

1. **Web UI:** Visual interface for conversion
2. **Git Integration:** Create PR with converted code
3. **Diff View:** Show Python vs Rust side-by-side
4. **Test Generation:** Generate Rust tests from Python tests
5. **Benchmark:** Compare Python vs Rust performance

### Research Resources

- Python → Rust guide: https://github.com/rochacbruno/py2rs
- PyO3 documentation: https://pyo3.rs/
- Rust FFI guide: https://doc.rust-lang.org/nomicon/ffi.html
- Common conversions: https://github.com/luisbg/python_rust

---

**Last Updated:** October 10, 2025  
**Next Review:** After Phase 1 completion  
**Owner:** Partik Singh (LFX Mentorship)

