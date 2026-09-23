"""
build_all.py - builds both budget_gui.py and hub_gui.py into standalone .exe
files with PyInstaller, showing a live progress bar in the terminal instead
of PyInstaller's raw scrolling log output.

PyInstaller doesn't report a clean 0-100% number as it works, so what you
get here is: an overall bar (build 1 of 2, build 2 of 2), and a live
spinner + elapsed time + the last log line for whichever build is running,
so you can see at a glance that it's alive and roughly what it's doing,
without your terminal being flooded by hundreds of "Analyzing/Processing"
lines.

Requires: pyinstaller (which you already have) + rich, for the progress bar
    pip install rich

Run this from the same folder as budget_gui.py and hub_gui.py:
    python build_all.py

Edit BUILDS below if you rename scripts, add --icon, change --name, etc.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()

# ---------------------------------------------------------------------------
# Config - one entry per script to build. Add/remove/edit freely.
# ---------------------------------------------------------------------------
BUILDS = [
    {
        "name": "BudgetEstimatorV2",
        "script": "budget_gui.py",
        "args": [
            "--onefile", "--windowed",
            "--collect-all", "sklearn",
            "--collect-all", "mord",
            "--collect-all", "scipy",
            "--name", "BudgetEstimatorV2",
        ],
    },
    {
        "name": "koogleAI",
        "script": "hub_gui.py",
        "args": [
            "--onefile", "--windowed",
            "--name", "koogleAI",
        ],
    },
]


def build_one(build: dict, progress: Progress, overall_task, step_task) -> bool:
    """Run one PyInstaller build as a subprocess, streaming its output into
    the progress bar's description line instead of printing it raw."""
    script_path = Path(build["script"])
    if not script_path.exists():
        progress.console.print(f"[red]Could not find {script_path} - skipping.[/red]")
        return False

    cmd = [sys.executable, "-m", "PyInstaller", *build["args"], build["script"]]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    last_line = ""
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.strip()
        if not line:
            continue
        last_line = line
        short = (line[:90] + "...") if len(line) > 90 else line
        progress.update(step_task, description=f"[cyan]{build['name']}[/cyan]: {short}")

    proc.wait()
    ok = proc.returncode == 0

    progress.update(
        step_task,
        description=f"[green]{build['name']} done[/green]" if ok else f"[red]{build['name']} failed[/red]",
    )
    progress.advance(overall_task)

    if ok:
        progress.console.print(f"[green]✓ {build['name']}.exe built[/green] -> dist/{build['name']}.exe")
    else:
        progress.console.print(f"[red]✗ {build['name']} failed (exit code {proc.returncode})[/red]")
        progress.console.print(f"  last output line: {last_line}")

    return ok


def main():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        overall_task = progress.add_task("[bold]Overall (0/{})[/bold]".format(len(BUILDS)), total=len(BUILDS))
        results: list[tuple[str, bool]] = []

        for build in BUILDS:
            # total=None -> an indeterminate/pulsing bar, since PyInstaller
            # never tells us a real percentage.
            step_task = progress.add_task(f"Waiting to build {build['name']}...", total=None)
            ok = build_one(build, progress, overall_task, step_task)
            results.append((build["name"], ok))
            done = sum(1 for _, ok_ in results if ok_)
            progress.update(overall_task, description=f"[bold]Overall ({len(results)}/{len(BUILDS)})[/bold]")

    console.print("\n[bold]Summary:[/bold]")
    all_ok = True
    for name, ok in results:
        mark = "[green]OK[/green]" if ok else "[red]FAILED[/red]"
        console.print(f"  {name}: {mark}")
        all_ok = all_ok and ok

    if all_ok:
        console.print("\n[green bold]All builds succeeded.[/green bold] Check the dist/ folder.")
        sys.exit(0)
    else:
        console.print("\n[red bold]One or more builds failed[/red bold] - scroll up for the full PyInstaller log.")
        sys.exit(1)


if __name__ == "__main__":
    main()
