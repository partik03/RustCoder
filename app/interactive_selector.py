"""Interactive UI for user to choose from LLM-suggested crates."""

from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()


class InteractiveCrateSelector:
    """Present LLM suggestions to user for selection."""
    
    def select_from_suggestions(
        self,
        suggestions: Dict[str, List[Dict]],
        auto_mode: bool = False
    ) -> Dict[str, Dict]:
        """
        Let user select from LLM suggestions.
        
        Args:
            suggestions: Dict from DynamicCrateSuggester
            auto_mode: If True, auto-select recommended options
        
        Returns:
            Selected crates mapping: {python_lib: {name, version, reason, ...}}
        """
        
        selections = {}
        
        if auto_mode:
            # Auto-select recommended options
            for dep, options in suggestions.items():
                recommended = next(
                    (opt for opt in options if opt.get("recommended")),
                    options[0] if options else None
                )
                if recommended:
                    selections[dep] = recommended
            return selections
        
        # Interactive mode
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🔍 Crate Selection[/bold cyan]\n"
            "LLM has analyzed your dependencies and suggests these Rust crates:",
            border_style="cyan"
        ))
        
        for dep, options in suggestions.items():
            console.print(f"\n[bold yellow]Python: {dep}[/bold yellow]")
            
            if not options:
                console.print("[red]  No suggestions available[/red]")
                continue
            
            # Check if needs research
            if options[0].get("needs_research"):
                console.print(f"[yellow]  ⚠️  {options[0]['reason']}[/yellow]")
                selections[dep] = options[0]
                continue
            
            # Display options
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Crate", style="green")
            table.add_column("Version", style="blue", width=8)
            table.add_column("Reason")
            table.add_column("⭐", width=3)
            
            for i, option in enumerate(options, 1):
                table.add_row(
                    str(i),
                    option.get("name", "?"),
                    option.get("version", "?"),
                    option.get("reason", "")[:60] + "..." if len(option.get("reason", "")) > 60 else option.get("reason", ""),
                    "✓" if option.get("recommended") else ""
                )
            
            console.print(table)
            
            # Get user choice
            if len(options) == 1:
                selections[dep] = options[0]
                console.print(f"[dim]  Using {options[0]['name']} (only option)[/dim]")
            else:
                default_idx = next(
                    (i for i, o in enumerate(options, 1) if o.get("recommended")),
                    1
                )
                
                choice = Prompt.ask(
                    f"  Select crate for [bold]{dep}[/bold]",
                    choices=[str(i) for i in range(1, len(options) + 1)],
                    default=str(default_idx)
                )
                
                selected = options[int(choice) - 1]
                selections[dep] = selected
                console.print(f"[green]  ✓ Selected {selected['name']}[/green]")
        
        return selections
    
    def format_for_cargo(self, selections: Dict[str, Dict]) -> str:
        """
        Format selected crates for Cargo.toml [dependencies] section.
        
        Args:
            selections: Dict of python_lib -> crate_info
        
        Returns:
            Formatted dependency lines for Cargo.toml
        """
        
        lines = []
        
        for python_lib, crate_info in selections.items():
            name = crate_info.get("name", "")
            version = crate_info.get("version", "")
            
            if crate_info.get("needs_research"):
                lines.append(f"# TODO: Find Rust crate for {python_lib}")
                continue
            
            # Dynamic feature detection based on crate name
            if "reqwest" in name.lower():
                lines.append(f'{name} = {{ version = "{version}", features = ["json"] }}')
            elif "clap" in name.lower():
                lines.append(f'{name} = {{ version = "{version}", features = ["derive"] }}')
            elif "tokio" in name.lower():
                lines.append(f'{name} = {{ version = "{version}", features = ["full"] }}')
            elif "serde" in name.lower() and not name.startswith("serde_"):
                lines.append(f'{name} = {{ version = "{version}", features = ["derive"] }}')
            elif "actix-web" in name.lower():
                lines.append(f'{name} = "{version}"')
            elif "axum" in name.lower():
                lines.append(f'{name} = "{version}"')
            else:
                # Default format
                lines.append(f'{name} = "{version}"')
        
        return "\n".join(lines)
    
    def format_summary(self, selections: Dict[str, Dict]) -> str:
        """
        Format a human-readable summary of selections.
        
        Args:
            selections: Dict of python_lib -> crate_info
        
        Returns:
            Formatted summary text
        """
        
        summary = "Selected Rust Crates:\n"
        summary += "=" * 50 + "\n\n"
        
        for python_lib, crate_info in selections.items():
            name = crate_info.get("name", "?")
            version = crate_info.get("version", "?")
            reason = crate_info.get("reason", "")
            
            summary += f"• {python_lib} → {name} v{version}\n"
            summary += f"  {reason}\n\n"
        
        return summary

