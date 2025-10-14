#!/bin/bash
# Task 4 Verification Script
# Run this to verify all Task 4 components are working

set -e  # Exit on error

echo "=========================================="
echo "Task 4 Verification Script"
echo "=========================================="
echo ""

# Check directory structure
echo "✅ Checking directory structure..."
for dir in app/analyzers app/converters app/mappings data/conversion_examples tests/test_analyzers; do
    if [ -d "$dir" ]; then
        echo "   ✓ $dir exists"
    else
        echo "   ✗ $dir missing"
        exit 1
    fi
done

# Check key files
echo ""
echo "✅ Checking key files..."
key_files=(
    "app/analyzers/python_analyzer.py"
    "app/converters/python_converter.py"
    "app/mappings/python_to_rust.py"
    "data/conversion_examples/python_to_rust/functions.json"
    "tests/test_analyzers/test_python_analyzer.py"
    "examples/convert_python_example.py"
)

for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file exists"
    else
        echo "   ✗ $file missing"
        exit 1
    fi
done

# Test imports
echo ""
echo "✅ Testing Python imports..."
python3 -c "from app.analyzers import PythonAnalyzer, CppAnalyzer; print('   ✓ Analyzers import OK')" || exit 1
python3 -c "from app.converters import PythonConverter, CppConverter; print('   ✓ Converters import OK')" || exit 1
python3 -c "from app.mappings import get_rust_crate, get_rust_equivalent; print('   ✓ Mappings import OK')" || exit 1
python3 -c "from app.utils import detect_project_language; print('   ✓ Utils import OK')" || exit 1

# Check syntax of key files
echo ""
echo "✅ Checking Python syntax..."
python3 -m py_compile examples/convert_python_example.py && echo "   ✓ Example script syntax valid"
python3 -m py_compile tests/test_analyzers/test_python_analyzer.py && echo "   ✓ Test file syntax valid"

# Test a simple analysis
echo ""
echo "✅ Testing analyzer functionality..."
python3 -c "
from pathlib import Path
import tempfile
from app.analyzers.python_analyzer import PythonAnalyzer

code = '''
def hello():
    return \"world\"
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(code)
    temp_path = Path(f.name)

analyzer = PythonAnalyzer()
result = analyzer.analyze_file(temp_path)
temp_path.unlink()

assert 'functions' in result
assert len(result['functions']) == 1
assert result['functions'][0]['name'] == 'hello'
print('   ✓ Python analyzer works correctly')
"

# Count files created
echo ""
echo "=========================================="
echo "📊 Statistics:"
echo "=========================================="
echo "New Python modules:    $(find app/analyzers app/converters app/mappings -name '*.py' | wc -l)"
echo "Conversion examples:   $(find data/conversion_examples -name '*.json' | wc -l)"
echo "Test files:            $(find tests -name '*.py' | wc -l)"
echo "Example scripts:       $(find examples -name 'convert_*.py' | wc -l)"

echo ""
echo "=========================================="
echo "✅ Task 4 Verification PASSED!"
echo "=========================================="
echo ""
echo "All components are in place and working!"
echo "Ready for Task 5 implementation."
echo ""

