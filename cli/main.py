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

def main():
    app()

if __name__ == "__main__":
    main()
