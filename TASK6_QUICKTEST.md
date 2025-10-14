# Task 6 Quick Test Guide

## ⚡ 5-Minute Test

### Step 1: Start Backend
```bash
cd /Users/partiksingh/RustCoder
docker-compose up
# Wait for "Application startup complete"
```

### Step 2: Run Integration Tests
```bash
# In another terminal
./run_integration_tests.sh
```

**Expected:** 3 tests run, summary table displayed, results saved

---

## 🎯 Quick Manual Test

### Test Simple CLI Project
```bash
python -m cli.main convert tests/integration/simple_cli \
  --output ./test_simple_output \
  --desc "CLI calculator with argparse"

# Check output
ls -la test_simple_output/
cat test_simple_output/src/main.rs

# Try to compile (if cargo installed locally)
cd test_simple_output && cargo build
```

---

## 📊 What to Look For

### Success Indicators
✓ Progress bar shows during conversion  
✓ "✅ Conversion successful!" message  
✓ Files saved to output directory  
✓ "🎉 Rust project compiles successfully!" (if compilation worked)  

### Test Results Table
```
┌────────────────┬──────────┬────────────┬──────────┐
│ Project        │ Analysis │ Conversion │ Compiles │
├────────────────┼──────────┼────────────┼──────────┤
│ simple_cli     │    ✓     │     ✓      │    ✓     │
│ flask_hello    │    ✓     │     ✓      │    ?     │
│ async_app      │    ✓     │     ✓      │    ?     │
└────────────────┴──────────┴────────────┴──────────┘
```

### Edge Cases Tested
- Empty files → Error message
- Large files → Truncation warning
- Syntax errors → Graceful handling
- Missing files → Clear error
- Connection issues → Helpful suggestions

---

## 🐛 Test Error Handling

### Test 1: Backend Not Running
```bash
# Don't start backend
python -m cli.main convert tests/integration/simple_cli
```

**Expected:**
```
❌ Cannot connect to RustCoder API at http://localhost:8000

Please start the backend:
  docker-compose up
```

### Test 2: Invalid Path
```bash
python -m cli.main convert /nonexistent/path
```

**Expected:**
```
❌ Error: /nonexistent/path not found
```

### Test 3: Empty Directory
```bash
mkdir empty_dir
python -m cli.main convert empty_dir
```

**Expected:**
```
Error: No Python files found in empty_dir
```

---

## 📁 Test Projects Overview

| Project | Files | Lines | Difficulty |
|---------|-------|-------|------------|
| simple_cli | 1 | 54 | Easy |
| flask_hello | 1 | 44 | Medium |
| async_app | 1 | 63 | Medium |

---

## ✅ Quick Validation

After running tests, check:

1. **Test Results JSON Created**
   ```bash
   cat tests/integration/test_results.json
   ```

2. **All Projects Analyzed**
   - total_files > 0
   - total_functions > 0

3. **At Least One Compiles**
   - Check "compile_success": true

4. **No Unexpected Errors**
   - Review errors list

---

## 🚀 Next Actions

If tests pass:
- ✅ Ready for production use
- ✅ Can test with real projects
- ✅ Integration pipeline working

If tests fail:
- Check backend logs: `docker-compose logs -f`
- Review error messages
- Check LLM API configuration
- Try individual projects manually

---

**Total Test Time:** 60-120 seconds  
**Expected Success Rate:** 85-95%

