import json
import os
import sys
import time
from typing import Optional

import requests
import typer
from rich import print as rprint
from rich.console import Console
from rich.json import JSON
from rich.table import Table

app = typer.Typer(add_completion=False, no_args_is_help=True, help="RustCoder CLI - talk to the API and manage jobs")


def get_server_url(server: Optional[str]) -> str:
    env_url = os.getenv("RUSTCODER_SERVER", "").strip()
    url = (server or env_url or "http://localhost:8000").rstrip("/")
    return url


@app.callback()
def global_options(
    ctx: typer.Context,
    server: Optional[str] = typer.Option(None, "--server", help="Base URL of RustCoder API (env: RUSTCODER_SERVER)")
):
    ctx.obj = {"server": get_server_url(server)}


@app.command()
def version(json_out: bool = typer.Option(False, "--json", help="Output as JSON")):
    """Show CLI and API endpoint info."""
    data = {
        "cli": "rustcoder-cli",
        "python": sys.version.split()[0],
    }
    if json_out:
        rprint(JSON.from_data(data))
    else:
        table = Table(title="RustCoder CLI")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value")
        for k, v in data.items():
            table.add_row(k, str(v))
        Console().print(table)


@app.command()
def completions(shell: Optional[str] = typer.Argument(None, help="Shell type: bash|zsh|fish|powershell")):
    """Print shell completion script."""
    # Typer provides completion via Click; rely on `--help` guidance for now
    rprint("[yellow]Note:[/yellow] Completions via Typer/Click are typically installed by your environment. Use: python -m typer cli.main utils completion [shell]")


@app.command()
def generate(
    description: str = typer.Option(..., "--description", help="Project description"),
    requirements: Optional[str] = typer.Option(None, "--requirements", help="Requirements text or path to file"),
    sync: bool = typer.Option(False, "--sync", help="Run synchronously and return files"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    ctx: typer.Context = typer.Option(None),
):
    """Generate a Rust project (sync uses /generate-sync, else /generate)."""
    base = ctx.obj["server"]

    req_text = requirements
    if requirements and os.path.exists(requirements):
        with open(requirements, "r") as f:
            req_text = f.read()

    payload = {"description": description, "requirements": req_text}

    if sync:
        url = f"{base}/generate-sync"
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            rprint(JSON.from_data(data))
        else:
            rprint("[green]Generation completed[/green]")
            rprint(data.get("message", ""))
            if "combined_text" in data:
                rprint("\n[bold]Combined files:[/bold]\n")
                sys.stdout.write(data["combined_text"] + "\n")
    else:
        url = f"{base}/generate"
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            rprint(JSON.from_data(data))
        else:
            rprint(f"[green]Started[/green] project_id=[bold]{data.get('project_id')}[/bold]")


@app.command()
def status(
    project: str = typer.Option(..., "--project", help="Project ID"),
    watch: bool = typer.Option(False, "--watch", help="Poll until terminal state"),
    interval: float = typer.Option(2.0, "--interval", help="Watch polling interval seconds"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    ctx: typer.Context = typer.Option(None),
):
    """Get status for an async project."""
    base = ctx.obj["server"]
    url = f"{base}/project/{project}"
    while True:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 404:
            rprint(f"[red]Project not found:[/red] {project}")
            raise typer.Exit(1)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            rprint(JSON.from_data(data))
        else:
            rprint(f"status=[bold]{data.get('status')}[/bold] message={data.get('message', '')}")
            files = data.get("files") or []
            if files:
                rprint(f"files: {', '.join(files)}")
        if not watch or data.get("status") in {"completed", "failed"}:
            break
        time.sleep(interval)


@app.command()
def download(
    project: str = typer.Option(..., "--project", help="Project ID"),
    out: str = typer.Option(None, "--out", help="Output zip path"),
    ctx: typer.Context = typer.Option(None),
):
    """Download a generated project as zip."""
    base = ctx.obj["server"]
    url = f"{base}/project/{project}/download"
    resp = requests.get(url, stream=True, timeout=120)
    if resp.status_code == 404:
        rprint(f"[red]Project not found:[/red] {project}")
        raise typer.Exit(1)
    resp.raise_for_status()
    out_path = out or f"project-{project}.zip"
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    rprint(f"[green]Saved:[/green] {out_path}")


@app.command(name="cat")
def cat_file(
    project: str = typer.Option(..., "--project", help="Project ID"),
    file: str = typer.Option(..., "--file", help="File path inside project"),
    ctx: typer.Context = typer.Option(None),
):
    """Print a single file from a generated project."""
    base = ctx.obj["server"]
    url = f"{base}/project/{project}/files/{file}"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        rprint("[red]File or project not found[/red]")
        raise typer.Exit(1)
    resp.raise_for_status()
    sys.stdout.write(resp.text)


@app.command()
def compile(
    code: Optional[str] = typer.Option(None, "--code", help="Path to multi-file text input in [filename: ] blocks"),
    project: Optional[str] = typer.Option(None, "--project", help="Project ID to compile (fetches files from API)"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    ctx: typer.Context = typer.Option(None),
):
    """Compile a Rust project from multi-file text format via /compile."""
    base = ctx.obj["server"]
    
    if not code and not project:
        rprint("[red]Error: Must specify either --code or --project[/red]")
        raise typer.Exit(1)
    
    if code and project:
        rprint("[red]Error: Cannot specify both --code and --project[/red]")
        raise typer.Exit(1)
    
    if code:
        # Compile from local file
        if not os.path.exists(code):
            rprint(f"[red]File not found:[/red] {code}")
            raise typer.Exit(1)
        with open(code, "r") as f:
            code_text = f.read()
    else:
        # Compile from project ID
        rprint(f"[blue]Fetching project files for:[/blue] {project}")
        
        # Get project status to see available files
        status_url = f"{base}/project/{project}"
        status_resp = requests.get(status_url, timeout=30)
        if status_resp.status_code == 404:
            rprint(f"[red]Project not found:[/red] {project}")
            raise typer.Exit(1)
        status_resp.raise_for_status()
        project_data = status_resp.json()
        
        if project_data.get("status") != "completed":
            rprint(f"[red]Project not ready:[/red] status={project_data.get('status')}")
            raise typer.Exit(1)
        
        files = project_data.get("files", [])
        if not files:
            rprint("[red]No files found in project[/red]")
            raise typer.Exit(1)
        
        # Build combined text from project files
        code_text = ""
        for file_path in files:
            file_url = f"{base}/project/{project}/files/{file_path}"
            file_resp = requests.get(file_url, timeout=30)
            if file_resp.status_code == 200:
                file_content = file_resp.text
                code_text += f"[filename: {file_path}]\n{file_content}\n\n"
            else:
                rprint(f"[yellow]Warning: Could not fetch file:[/yellow] {file_path}")
        
        if not code_text.strip():
            rprint("[red]No file content could be retrieved[/red]")
            raise typer.Exit(1)
    
    # Compile the code
    url = f"{base}/compile"
    resp = requests.post(url, json={"code": code_text}, timeout=120)
    if resp.status_code >= 400:
        rprint(f"[red]Request failed:[/red] {resp.status_code} {resp.text}")
        raise typer.Exit(1)
    data = resp.json()
    if json_out:
        rprint(JSON.from_data(data))
    else:
        if data.get("success"):
            rprint("[green]Build successful[/green]")
            if data.get("run_output"):
                rprint("[bold]Run output:[/bold]")
                sys.stdout.write(str(data["run_output"]) + "\n")
        else:
            rprint("[red]Build failed[/red]")
            if data.get("build_output"):
                sys.stdout.write(str(data["build_output"]) + "\n")


@app.command()
def fix(
    code: Optional[str] = typer.Option(None, "--code", help="Path to multi-file text input in [filename: ] blocks"),
    project: Optional[str] = typer.Option(None, "--project", help="Project ID to fix (fetches files from API)"),
    description: str = typer.Option(..., "--description", help="Project description"),
    max_attempts: int = typer.Option(3, "--max-attempts", min=1, help="Maximum fix attempts"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    ctx: typer.Context = typer.Option(None),
):
    """Compile and auto-fix via /compile-and-fix."""
    base = ctx.obj["server"]
    
    if not code and not project:
        rprint("[red]Error: Must specify either --code or --project[/red]")
        raise typer.Exit(1)
    
    if code and project:
        rprint("[red]Error: Cannot specify both --code and --project[/red]")
        raise typer.Exit(1)
    
    if code:
        # Fix from local file
        if not os.path.exists(code):
            rprint(f"[red]File not found:[/red] {code}")
            raise typer.Exit(1)
        with open(code, "r") as f:
            code_text = f.read()
    else:
        # Fix from project ID
        rprint(f"[blue]Fetching project files for:[/blue] {project}")
        
        # Get project status to see available files
        status_url = f"{base}/project/{project}"
        status_resp = requests.get(status_url, timeout=30)
        if status_resp.status_code == 404:
            rprint(f"[red]Project not found:[/red] {project}")
            raise typer.Exit(1)
        status_resp.raise_for_status()
        project_data = status_resp.json()
        
        if project_data.get("status") != "completed":
            rprint(f"[red]Project not ready:[/red] status={project_data.get('status')}")
            raise typer.Exit(1)
        
        files = project_data.get("files", [])
        if not files:
            rprint("[red]No files found in project[/red]")
            raise typer.Exit(1)
        
        # Build combined text from project files
        code_text = ""
        for file_path in files:
            file_url = f"{base}/project/{project}/files/{file_path}"
            file_resp = requests.get(file_url, timeout=30)
            if file_resp.status_code == 200:
                file_content = file_resp.text
                code_text += f"[filename: {file_path}]\n{file_content}\n\n"
            else:
                rprint(f"[yellow]Warning: Could not fetch file:[/yellow] {file_path}")
        
        if not code_text.strip():
            rprint("[red]No file content could be retrieved[/red]")
            raise typer.Exit(1)
    
    # Fix the code
    url = f"{base}/compile-and-fix"
    payload = {"code": code_text, "description": description, "max_attempts": max_attempts}
    resp = requests.post(url, json=payload, timeout=600)
    if resp.status_code >= 400:
        rprint(f"[red]Request failed:[/red] {resp.status_code} {resp.text}")
        raise typer.Exit(1)
    data = resp.json()
    if json_out:
        rprint(JSON.from_data(data))
    else:
        if data.get("success"):
            rprint("[green]Fixed and compiled successfully[/green]")
            if data.get("combined_text"):
                rprint("\n[bold]Combined files:[/bold]\n")
                sys.stdout.write(data["combined_text"] + "\n")
            if data.get("run_output"):
                rprint("[bold]Run output:[/bold]")
                sys.stdout.write(str(data["run_output"]) + "\n")
        else:
            rprint("[red]Failed to fix after attempts[/red]")
            if data.get("combined_text"):
                rprint("\n[bold]Final files:[/bold]\n")
                sys.stdout.write(data["combined_text"] + "\n")
            if data.get("build_output"):
                rprint("\n[bold]Build output:[/bold]")
                sys.stdout.write(str(data["build_output"]) + "\n")

@app.command()
def analyze(
    project_path: str = typer.Argument(..., help="Path to Python/C++ project"),
    language: str = typer.Option(None, "--language", "-l", help="Source language (python/cpp)"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Analyze a Python or C++ project for Rust conversion."""
    from pathlib import Path
    from app.utils import detect_project_language
    from app.analyzers import PythonAnalyzer, CppAnalyzer
    
    console = Console()
    path = Path(project_path)
    if not path.exists():
        console.print(f"[red]Error: Path {project_path} does not exist[/red]")
        raise typer.Exit(1)
    
    # Detect language if not specified
    if not language:
        language = detect_project_language(path)
        console.print(f"[cyan]Detected language: {language}[/cyan]")
    
    # Analyze project
    console.print(f"[bold]Analyzing {language} project...[/bold]")
    
    if language == "python":
        analyzer = PythonAnalyzer()
    elif language == "cpp":
        analyzer = CppAnalyzer()
    else:
        console.print(f"[red]Unsupported language: {language}[/red]")
        raise typer.Exit(1)
    
    analysis = analyzer.analyze_project(path)
    
    # Display results
    if json_out:
        rprint(JSON.from_data(analysis))
    else:
        console.print("\n[bold green]Analysis Results:[/bold green]")
        console.print(f"  Project: {analysis['project_path']}")
        console.print(f"  Total files: {analysis['total_files']}")
        if 'total_functions' in analysis:
            console.print(f"  Total functions: {analysis['total_functions']}")
        if 'total_classes' in analysis:
            console.print(f"  Total classes: {analysis['total_classes']}")
        if 'dependencies' in analysis and analysis['dependencies']:
            console.print(f"  Dependencies: {', '.join(analysis['dependencies'][:5])}")
            if len(analysis['dependencies']) > 5:
                console.print(f"    ... and {len(analysis['dependencies']) - 5} more")
    
    # Save to file
    output_file = path / f"analysis_{language}.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    console.print(f"\n[green]Analysis saved to: {output_file}[/green]")


@app.command()
def convert(
    ctx: typer.Context,
    source_path: str = typer.Argument(..., help="Path to source project"),
    output_dir: str = typer.Option("./converted", "--output", "-o", help="Output directory"),
    language: str = typer.Option("python", "--language", "-l", help="Source language"),
    description: str = typer.Option("", "--desc", help="Project description"),
    auto: bool = typer.Option(False, "--auto", help="Auto-select recommended crates (no interaction)"),
):
    """Convert Python to Rust with DYNAMIC LLM-driven crate selection."""
    import httpx
    from pathlib import Path
    import json
    
    console = Console()
    
    # Display header with dynamic crate selection info
    from rich.panel import Panel
    console.print(Panel.fit(
        "[bold cyan]🐍 → 🦀 Dynamic Conversion[/bold cyan]\n"
        "LLM will analyze and suggest appropriate Rust crates",
        border_style="cyan"
    ))
    
    console.print(f"📁 Source: {source_path}")
    console.print(f"🎯 Output: {output_dir}")
    console.print(f"🔤 Language: {language}")
    if auto:
        console.print("🤖 Mode: Auto-select (recommended crates)")
    else:
        console.print("🤖 Mode: Interactive (you'll choose crates)")
    
    if language != "python":
        console.print("\n[yellow]⚠️  Only Python conversion is implemented currently[/yellow]")
        console.print("[dim]C++ conversion will be added in a future task[/dim]")
        return
    
    source = Path(source_path)
    if not source.exists():
        console.print(f"\n[red]❌ Error: {source_path} not found[/red]")
        raise typer.Exit(1)
    
    # Get server URL from context
    server_url = ctx.obj.get("server") if ctx.obj else "http://localhost:8000"
    
    # Call the conversion API
    console.print("\n[bold]🔄 Converting...[/bold]")
    
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task1 = progress.add_task("[cyan]Analyzing Python code...", total=None)
            
            # Make the API call
            response = httpx.post(
                f"{server_url}/convert-python-to-rust",
                json={
                    "project_path": str(source.absolute()),
                    "description": description,
                    "max_fix_attempts": 5,
                    "interactive": not auto  # Interactive unless --auto flag
                },
                timeout=300.0  # Increased timeout for LLM crate analysis
            )
            response.raise_for_status()
            result = response.json()
            
            progress.update(task1, completed=True, description="[green]✓ Conversion complete")
        
        if result.get("success"):
            console.print("\n[bold green]✅ Conversion successful![/bold green]")
            
            # Display LLM-selected crates
            selected_crates = result.get("selected_crates", {})
            if selected_crates:
                console.print(f"\n[bold]📦 Rust Crates (LLM-selected):[/bold]")
                for py_lib, crate in selected_crates.items():
                    console.print(f"  • {py_lib} → {crate['name']} v{crate['version']}")
                    console.print(f"    [dim]{crate['reason'][:80]}...[/dim]" if len(crate['reason']) > 80 else f"    [dim]{crate['reason']}[/dim]")
            
            # Display analysis
            analysis = result.get("analysis", {})
            python_files = result.get("python_files", [])
            console.print(f"\n📊 Converted {len(python_files)} Python files:")
            for pf in python_files:
                console.print(f"   - {pf}")
            console.print(f"\n   Functions: {analysis.get('total_functions', 0)}")
            console.print(f"   Classes: {analysis.get('total_classes', 0)}")
            
            # Save output
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            files = result.get("files", {})
            for filename, content in files.items():
                file_path = output_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w') as f:
                    f.write(content)
                
                console.print(f"   ✓ {filename}")
            
            console.print(f"\n💾 Rust project saved to: {output_path}")
            
            # Show build output
            build_output = result.get("build_output", "")
            if "successfully" in build_output.lower():
                console.print("\n[green]🎉 Rust project compiles successfully![/green]")
            elif build_output:
                console.print("\n[yellow]⚠️  Build output:[/yellow]")
                console.print(f"[dim]{build_output[:500]}...[/dim]")
            
            # Show fix attempts
            fix_attempts = result.get("fix_attempts", 0)
            if fix_attempts > 0:
                console.print(f"\n🔧 Fixed compilation errors in {fix_attempts} attempts")
            
        else:
            console.print("\n[red]❌ Conversion failed[/red]")
            error = result.get("error", "Unknown error")
            console.print(f"[dim]{error}[/dim]")
            raise typer.Exit(1)
    
    except httpx.TimeoutException:
        console.print("\n[red]❌ Conversion timed out[/red]")
        console.print("\n[yellow]Suggestions:[/yellow]")
        console.print("  1. Try with a smaller project")
        console.print("  2. Increase timeout in API settings")
        console.print("  3. Run the API server locally for better performance")
        raise typer.Exit(1)
    except httpx.ConnectError as e:
        console.print(f"\n[red]❌ Cannot connect to RustCoder API at {server_url}[/red]")
        console.print("\n[yellow]Please start the backend:[/yellow]")
        console.print("  [cyan]docker-compose up[/cyan]")
        console.print("\n[yellow]Or specify a different server:[/yellow]")
        console.print("  [cyan]python -m cli.main --server http://your-server:8000 convert ...[/cyan]")
        raise typer.Exit(1)
    except httpx.HTTPError as e:
        console.print(f"\n[red]❌ API Error: {e}[/red]")
        if "404" in str(e):
            console.print("\n[yellow]Endpoint not found. Make sure you're running the latest version.[/yellow]")
        elif "500" in str(e):
            console.print("\n[yellow]Server error. Check the backend logs:[/yellow]")
            console.print("  [cyan]docker-compose logs -f[/cyan]")
        else:
            console.print("[dim]Make sure RustCoder backend is running (docker-compose up)[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        console.print("\n[yellow]Debug information:[/yellow]")
        console.print(f"  Source path: {source_path}")
        console.print(f"  Server URL: {server_url}")
        console.print(f"  Error type: {type(e).__name__}")
        raise typer.Exit(1)


@app.command()
def set_model(
    ctx: typer.Context,
    model: str = typer.Argument(..., help="Model name (claude-sonnet, claude-opus, gemini, local)")
):
    """Set the LLM model for conversions."""
    import httpx
    
    console = Console()
    
    # Get server URL from context
    server_url = ctx.obj.get("server") if ctx.obj else "http://localhost:8000"
    
    try:
        response = httpx.get(f"{server_url}/config/model/{model}", timeout=10.0)
        response.raise_for_status()
        result = response.json()
        
        console.print(f"\n[green]✓ {result['message']}[/green]")
        console.print(f"\n[bold]Model Configuration:[/bold]")
        console.print(f"  Model Key: {result['model']}")
        console.print(f"  Full Name: {result['model_name']}")
        console.print("\n[dim]This model will be used for all future conversions.[/dim]")
        
    except httpx.HTTPError as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print("\n[yellow]Available models:[/yellow]")
        console.print("  - claude-sonnet (Claude Sonnet 4.5)")
        console.print("  - claude-opus (Claude Opus 4)")
        console.print("  - gemini (Gemini Pro)")
        console.print("  - local (Local/Gaia model)")
        raise typer.Exit(1)


@app.command()
def show_model(ctx: typer.Context):
    """Show current LLM model configuration."""
    import httpx
    
    console = Console()
    
    # Get server URL from context
    server_url = ctx.obj.get("server") if ctx.obj else "http://localhost:8000"
    
    try:
        response = httpx.get(f"{server_url}/config/model", timeout=10.0)
        response.raise_for_status()
        config_data = response.json()
        
        console.print("\n[bold cyan]Current Model Configuration[/bold cyan]")
        console.print("=" * 50)
        console.print(f"\n[bold]Active Model:[/bold] {config_data['model']}")
        console.print(f"[bold]Full Name:[/bold] {config_data['model_name']}")
        console.print(f"[bold]API Base:[/bold] {config_data.get('api_base', 'N/A')}")
        
        console.print(f"\n[bold]Available Models:[/bold]")
        for model in config_data.get('available_models', []):
            marker = "✓" if model == config_data['model'] else " "
            console.print(f"  {marker} {model}")
        
        console.print("\n[dim]To change model:[/dim]")
        console.print("[dim]  python -m cli.main set-model <model-name>[/dim]")
        console.print()
        
    except httpx.HTTPError as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print("\n[yellow]Make sure RustCoder backend is running:[/yellow]")
        console.print("  [cyan]docker-compose up[/cyan]")
        raise typer.Exit(1)


def main():
    app()

if __name__ == "__main__":
    main()
