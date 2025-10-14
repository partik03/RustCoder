"""Example: Analyze and prepare Python project for conversion."""

from pathlib import Path
from app.analyzers.python_analyzer import PythonAnalyzer
from app.mappings.python_to_rust import get_rust_crate
import json


def main():
    print("=" * 60)
    print("Python to Rust Conversion Analysis Example")
    print("=" * 60)
    
    # Analyze a Python file
    analyzer = PythonAnalyzer()
    
    # Create a simple test file
    test_code = """
import requests
import click

@click.command()
def hello(name):
    '''Greet someone using an API.'''
    response = requests.get(f"https://api.example.com/greet/{name}")
    print(response.text)

if __name__ == "__main__":
    hello()
"""
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        # Analyze
        result = analyzer.analyze_file(temp_path)
        
        print("\n📊 Python Code Analysis:")
        print("-" * 60)
        print(json.dumps(result, indent=2))
        
        print("\n\n🦀 Rust Crate Recommendations:")
        print("-" * 60)
        for imp in result.get("imports", []):
            crate = get_rust_crate(imp)
            print(f"  {imp:15s} → {crate}")
        
        print("\n\n💡 Conversion Notes:")
        print("-" * 60)
        print("  • @click.command() → clap derive macros")
        print("  • requests.get() → reqwest::get().await")
        print("  • Will need async runtime (tokio)")
        print("  • String formatting uses format!() macro")
        
        print("\n✅ Analysis complete!")
        print(f"   Analyzed file: {temp_path}")
        
    finally:
        temp_path.unlink()


if __name__ == "__main__":
    main()

