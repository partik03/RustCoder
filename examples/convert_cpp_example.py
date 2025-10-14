"""Example: Analyze C++ code (stub for future implementation)."""

from pathlib import Path
from app.analyzers.cpp_analyzer import CppAnalyzer
import json


def main():
    print("=" * 60)
    print("C++ to Rust Conversion Analysis Example")
    print("=" * 60)
    print("\n⚠️  Note: C++ analysis is basic pattern matching for now")
    print("   Full C++ parsing will be added in future versions\n")
    
    # Create a simple test file
    test_code = """
#include <iostream>
#include <string>
#include <vector>

class Calculator {
private:
    int value;
    
public:
    Calculator(int initial) : value(initial) {}
    
    int add(int n) {
        value += n;
        return value;
    }
    
    int get_value() const {
        return value;
    }
};

int main() {
    Calculator calc(10);
    std::cout << calc.add(5) << std::endl;
    return 0;
}
"""
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(test_code)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        analyzer = CppAnalyzer()
        result = analyzer.analyze_file(temp_path)
        
        print("\n📊 C++ Code Analysis:")
        print("-" * 60)
        print(json.dumps(result, indent=2))
        
        print("\n\n🦀 Detected Patterns:")
        print("-" * 60)
        if result.get("classes"):
            print(f"  Classes: {', '.join(result['classes'])}")
        if result.get("has_pointers"):
            print("  ⚠️  Uses pointers - will need careful Rust translation")
        if result.get("has_templates"):
            print("  ⚠️  Uses templates - map to Rust generics")
        
        print("\n✅ Basic analysis complete!")
        print("   Full C++ support coming in future updates")
        
    finally:
        temp_path.unlink()


if __name__ == "__main__":
    main()

