import sys
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Internal imports
from axp.core.chain import execute_caller_only, run_creative_chain
from axp.core.validator import validate_json_schema  # Assuming this exists
from axp.utils.config_loader import load_shapes

# Init Rich Console
console = Console()
load_dotenv()
BASE_DIR = Path(__file__).parent

def main():
    console.print(Panel.fit("[bold cyan]AxPrototype v3.0[/bold cyan]\nCreative Domain Governance Engine", border_style="cyan"))

    # 1. Initialization
    session_id = str(uuid.uuid4())[:8]
    console.print(f"[dim]Session ID: {session_id}[/dim]")

    try:
        shapes = load_shapes(BASE_DIR / "config" / "role_shapes.json")
    except FileNotFoundError:
        console.print("[red]Error: role_shapes.json not found.[/red]")
        sys.exit(1)

    # 2. The Caller Interaction (Sparring Partner)
    user_input = console.input("\n[bold green]>> Enter Request:[/bold green] ")

    with console.status("[bold yellow]Caller is analyzing (OPS)...[/bold yellow]"):
        caller_result = execute_caller_only(
            user_prompt=user_input,
            base_dir=BASE_DIR,
            session_id=session_id,
            validator_func=validate_json_schema,
            shapes_config=shapes
        )

    # 3. The Truth > Obedience Choice
    console.print("\n[bold magenta]--- AxP Insight ---[/bold magenta]")
    console.print(f"[italic]{caller_result.get('axp_insight', 'No insight generated.')}[/italic]")

    console.print("\n[bold magenta]--- Optimized Prompt Suggestion (OPS) ---[/bold magenta]")
    console.print(Markdown(caller_result.get('ops', 'No OPS generated.')))

    choice = console.input("\n[bold yellow]Use OPS? (y/n):[/bold yellow] ").strip().lower()

    if choice == 'y':
        final_objective = caller_result.get('ops')
        console.print("[dim]Using OPS...[/dim]")
    else:
        final_objective = user_input
        console.print("[dim]Using Original Input...[/dim]")

    # 4. The Engine Loop (Builder -> Critic)
    with console.status("[bold cyan]Running Creative Chain (Builder -> Critic)...[/bold cyan]"):
        result = run_creative_chain(
            final_objective=final_objective,
            user_context={},  # No previous context for fresh run
            config={},
            base_dir=BASE_DIR,
            session_id=session_id,
            validator_func=validate_json_schema,
            shapes_config=shapes
        )

    # 5. Final Output Display
    console.print("\n[bold green]--- Final Artifact ---[/bold green]")
    console.print(Markdown(result['artifact']))

    console.print(Panel(
        f"TAES Score: {result['taes_score']}\n"
        f"Status: {result['governance_status']}\n"
        f"Critic Feedback: {result['critic_feedback']}",
        title="Governance Log",
        border_style="red" if result['governance_status'] != "approved" else "green"
    ))


if __name__ == "__main__":
    main()
