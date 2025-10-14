#!/usr/bin/env python3
"""Integration tests for Python to Rust conversion."""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()

# Test projects
TEST_PROJECTS = [
    {
        "name": "simple_cli",
        "path": "tests/integration/simple_cli",
        "description": "CLI calculator with argparse - uses only standard library",
        "expected_crates": ["clap", "anyhow"],
    },
    {
        "name": "flask_hello",
        "path": "tests/integration/flask_hello",
        "description": "Minimal Flask web app with routes and JSON responses",
        "expected_crates": ["actix-web", "serde", "serde_json"],
    },
    {
        "name": "async_app",
        "path": "tests/integration/async_app",
        "description": "Async application using asyncio and aiohttp",
        "expected_crates": ["tokio", "reqwest"],
    },
]

API_BASE_URL = os.getenv("RUSTCODER_API_URL", "http://localhost:8000")


def check_api_available() -> bool:
    """Check if the RustCoder API is available."""
    try:
        response = httpx.get(f"{API_BASE_URL}/docs", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


def analyze_project(project_path: str) -> Tuple[bool, Dict]:
    """Analyze a Python project."""
    try:
        response = httpx.post(
            f"{API_BASE_URL}/analyze-python",
            json={"project_path": str(Path(project_path).absolute())},
            timeout=30.0
        )
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, {"error": str(e)}


def convert_project(project_path: str, description: str, max_fix_attempts: int = 5) -> Tuple[bool, Dict]:
    """Convert a Python project to Rust."""
    try:
        response = httpx.post(
            f"{API_BASE_URL}/convert-python-to-rust",
            json={
                "project_path": str(Path(project_path).absolute()),
                "description": description,
                "max_fix_attempts": max_fix_attempts
            },
            timeout=180.0
        )
        response.raise_for_status()
        return True, response.json()
    except httpx.TimeoutException:
        return False, {"error": "Conversion timed out"}
    except Exception as e:
        return False, {"error": str(e)}


def verify_rust_compiles(rust_files: Dict[str, str], output_dir: Path) -> Tuple[bool, str]:
    """Write Rust files and check if they compile."""
    try:
        # Write files
        for filename, content in rust_files.items():
            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Try to compile
        result = subprocess.run(
            ["cargo", "build"],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.returncode == 0, result.stderr + result.stdout
    except subprocess.TimeoutExpired:
        return False, "Cargo build timed out"
    except Exception as e:
        return False, str(e)


def run_test(project: Dict) -> Dict:
    """Run a single conversion test."""
    result = {
        "name": project["name"],
        "description": project["description"],
        "analysis_success": False,
        "conversion_success": False,
        "compile_success": False,
        "fix_attempts": 0,
        "errors": [],
        "warnings": [],
        "duration": 0,
    }
    
    start_time = time.time()
    
    try:
        # Step 1: Analyze
        console.print(f"\n[cyan]Testing {project['name']}...[/cyan]")
        console.print(f"  Description: {project['description']}")
        
        with console.status("[bold green]Analyzing Python code..."):
            analysis_success, analysis = analyze_project(project["path"])
        
        if not analysis_success:
            result["errors"].append(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
            return result
        
        result["analysis_success"] = True
        result["analysis"] = analysis.get("analysis", {})
        
        console.print(f"  ✓ Analysis: {result['analysis'].get('total_files', 0)} files, "
                     f"{result['analysis'].get('total_functions', 0)} functions, "
                     f"{result['analysis'].get('total_classes', 0)} classes")
        
        # Step 2: Convert
        with console.status("[bold green]Converting to Rust..."):
            conversion_success, conversion = convert_project(
                project["path"],
                project["description"],
                max_fix_attempts=5
            )
        
        if not conversion_success:
            result["errors"].append(f"Conversion failed: {conversion.get('error', 'Unknown error')}")
            return result
        
        result["conversion_success"] = conversion.get("success", False)
        result["fix_attempts"] = conversion.get("fix_attempts", 0)
        result["build_output"] = conversion.get("build_output", "")
        
        if not result["conversion_success"]:
            result["errors"].append("Conversion reported failure")
            return result
        
        console.print(f"  ✓ Conversion successful (fix attempts: {result['fix_attempts']})")
        
        # Step 3: Verify compilation
        files = conversion.get("files", {})
        if not files:
            result["errors"].append("No files returned from conversion")
            return result
        
        # Check for expected crates in Cargo.toml
        cargo_toml = files.get("Cargo.toml", "")
        if cargo_toml:
            for expected_crate in project.get("expected_crates", []):
                if expected_crate in cargo_toml:
                    result["warnings"].append(f"✓ Found expected crate: {expected_crate}")
        
        # Check if it compiled during conversion
        build_output = result.get("build_output", "")
        if "successfully" in build_output.lower() or "finished" in build_output.lower():
            result["compile_success"] = True
            console.print(f"  ✓ [green]Rust code compiles successfully![/green]")
        else:
            result["compile_success"] = False
            if build_output:
                result["errors"].append(f"Compilation issues: {build_output[:200]}...")
                console.print(f"  ✗ [yellow]Compilation issues detected[/yellow]")
        
    except Exception as e:
        result["errors"].append(f"Test exception: {str(e)}")
    
    result["duration"] = time.time() - start_time
    return result


def print_results_summary(results: List[Dict]):
    """Print a summary table of test results."""
    console.print("\n[bold cyan]Test Results Summary[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Project", style="cyan", width=20)
    table.add_column("Analysis", justify="center", width=10)
    table.add_column("Conversion", justify="center", width=12)
    table.add_column("Compiles", justify="center", width=10)
    table.add_column("Fix Attempts", justify="center", width=12)
    table.add_column("Duration", justify="right", width=10)
    
    for result in results:
        analysis = "✓" if result["analysis_success"] else "✗"
        conversion = "✓" if result["conversion_success"] else "✗"
        compiles = "✓" if result["compile_success"] else "✗"
        
        # Color coding
        analysis_colored = f"[green]{analysis}[/green]" if result["analysis_success"] else f"[red]{analysis}[/red]"
        conversion_colored = f"[green]{conversion}[/green]" if result["conversion_success"] else f"[red]{conversion}[/red]"
        compiles_colored = f"[green]{compiles}[/green]" if result["compile_success"] else f"[yellow]{compiles}[/yellow]"
        
        table.add_row(
            result["name"],
            analysis_colored,
            conversion_colored,
            compiles_colored,
            str(result["fix_attempts"]),
            f"{result['duration']:.1f}s"
        )
    
    console.print(table)
    
    # Overall statistics
    total = len(results)
    analysis_success = sum(1 for r in results if r["analysis_success"])
    conversion_success = sum(1 for r in results if r["conversion_success"])
    compile_success = sum(1 for r in results if r["compile_success"])
    
    console.print(f"\n[bold]Overall Statistics:[/bold]")
    console.print(f"  Analysis Success Rate:   {analysis_success}/{total} ({analysis_success/total*100:.1f}%)")
    console.print(f"  Conversion Success Rate: {conversion_success}/{total} ({conversion_success/total*100:.1f}%)")
    console.print(f"  Compilation Success Rate: {compile_success}/{total} ({compile_success/total*100:.1f}%)")
    
    avg_fix_attempts = sum(r["fix_attempts"] for r in results) / max(total, 1)
    console.print(f"  Average Fix Attempts:    {avg_fix_attempts:.1f}")
    
    total_duration = sum(r["duration"] for r in results)
    console.print(f"  Total Duration:          {total_duration:.1f}s")


def print_detailed_errors(results: List[Dict]):
    """Print detailed error information."""
    console.print("\n[bold red]Detailed Errors and Warnings:[/bold red]\n")
    
    for result in results:
        if result["errors"] or result["warnings"]:
            console.print(f"[cyan]{result['name']}:[/cyan]")
            
            if result["errors"]:
                console.print("  [red]Errors:[/red]")
                for error in result["errors"]:
                    console.print(f"    - {error}")
            
            if result["warnings"]:
                console.print("  [yellow]Warnings:[/yellow]")
                for warning in result["warnings"]:
                    console.print(f"    - {warning}")
            
            console.print()


def save_results(results: List[Dict], output_file: str = "test_results.json"):
    """Save test results to JSON file."""
    output_path = Path(__file__).parent / output_file
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    console.print(f"\n[green]Results saved to: {output_path}[/green]")


def main():
    """Run all integration tests."""
    console.print("[bold cyan]RustCoder Integration Tests[/bold cyan]")
    console.print("=" * 60)
    
    # Check API availability
    console.print("\n[bold]Checking API availability...[/bold]")
    if not check_api_available():
        console.print(f"[red]✗ API not available at {API_BASE_URL}[/red]")
        console.print("[yellow]Please start the RustCoder backend:[/yellow]")
        console.print("  docker-compose up")
        sys.exit(1)
    
    console.print(f"[green]✓ API available at {API_BASE_URL}[/green]")
    
    # Run tests
    results = []
    
    for project in TEST_PROJECTS:
        try:
            result = run_test(project)
            results.append(result)
        except KeyboardInterrupt:
            console.print("\n[yellow]Tests interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Unexpected error testing {project['name']}: {e}[/red]")
            results.append({
                "name": project["name"],
                "errors": [str(e)],
                "analysis_success": False,
                "conversion_success": False,
                "compile_success": False,
                "fix_attempts": 0,
                "duration": 0,
            })
    
    # Print results
    print_results_summary(results)
    print_detailed_errors(results)
    
    # Save results
    save_results(results)
    
    # Exit code based on results
    all_success = all(r["conversion_success"] for r in results)
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()

