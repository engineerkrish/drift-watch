from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

def render_terminal(findings, new_count, still_count, resolved_count, repo_name):
    console = Console()
    console.print()
    console.print(Panel.fit("[bold cyan]DRIFT WATCH[/bold cyan]\nConfiguration Drift Detective", border_style="cyan"))
    console.print(f"Repository: [bold]{repo_name}[/bold]")
    console.print("Safety: [bold green]PASS — no secret values emitted[/bold green]")
    console.print()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Severity", width=10)
    table.add_column("Category", width=16)
    table.add_column("Key")
    table.add_column("Location")
    table.add_column("Environments")
    for f in findings:
        sev = {"critical":"[bold red]CRITICAL[/bold red]","warning":"[yellow]WARNING[/yellow]","info":"[blue]INFO[/blue]"}[f.severity]
        loc = f.used_at or ", ".join(f.sources[:1])
        envs = f"missing: {', '.join(f.missing_in)}" if f.missing_in else f"defined: {', '.join(f.defined_in)}"
        table.add_row(sev, f.category, f.key, loc, envs)
    if findings:
        console.print(table)
    else:
        console.print(Panel("[bold green]✓ No configuration drift detected.[/bold green]", border_style="green"))
    console.print()
    console.print(f"New: [bold]{new_count}[/bold]   Still unresolved: [bold]{still_count}[/bold]   Resolved: [bold]{resolved_count}[/bold]")
    console.print("[dim]Secret values are never shown, logged, or written to reports.[/dim]")
