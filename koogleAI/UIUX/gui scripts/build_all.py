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

The two finished .exe files are written OUTSIDE the MOECSO folder entirely -
directly into MOECSO's own parent folder (a sibling of MOECSO, not nested
inside it). PyInstaller's intermediate junk (the build/ cache, .spec files)
goes into a _pyinstaller_build folder next to them, out of the way.

Requires: pyinstaller (which you already have) + rich, for the progress bar
    pip install rich

Run from anywhere - MOECSO_DIR is found automatically (see find_moecso_dir
below), it does not depend on your current working directory:
    python build_all.py

Edit BUILDS below if you rename scripts, add --icon, change --name, etc.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()


def find_moecso_dir() -> Path:
    """Locate the MOECSO project folder by walking UP from wherever this
    script actually lives, instead of a hardcoded machine-specific path
    like C:\\Users\\idowe\\.... This way the exact same code works on any
    PC/username, as long as the file sits somewhere inside a "MOECSO"
    folder, wherever that is."""
    here = Path(__file__).resolve()
    for folder in [here] + list(here.parents):
        if folder.name == "MOECSO":
            return folder
        sibling = folder / "MOECSO"
        if sibling.is_dir():
            return sibling
    raise FileNotFoundError(
        f"Could not find a 'MOECSO' folder above, or next to, {here}. "
        "Make sure build_all.py lives inside MOECSO, or right beside it."
    )


# ---------------------------------------------------------------------------
# Config - anchored to MOECSO_DIR (found automatically above, not hardcoded)
# so this works no matter where you launch it from (PyCharm's working
# directory, a shortcut, a different terminal cwd, or even a different PC)
# - everything below it keeps the same sub-path structure your project
# already uses.
# ---------------------------------------------------------------------------
MOECSO_DIR = find_moecso_dir()
GUI_SCRIPTS_DIR = MOECSO_DIR / "koogleAI" / "UIUX" / "gui scripts"

# The finished .exe files land OUTSIDE MOECSO entirely - directly in
# MOECSO's own parent folder (a sibling of MOECSO, not a subfolder of it).
# PyInstaller's intermediate junk (the build/ cache and the .spec file) is
# kept out of the way in its own hidden-ish subfolder next to the exes,
# instead of cluttering either MOECSO or its parent.
EXE_DIR = MOECSO_DIR.parent
BUILD_CACHE_DIR = EXE_DIR / "_pyinstaller_build"

# Data files each exe looks for beside itself at runtime (see resolve_asset()
# in budget_gui.py/hub_gui.py) - copied into EXE_DIR after a successful build
# so the whole EXE_DIR folder is one self-contained, movable unit: copy it
# (or the two .exe files + these) anywhere and it keeps working, with no
# dependency on MOECSO_DIR at runtime.
ASSETS_TO_COPY = [
    MOECSO_DIR / "koogleAI" / "budget_estimation" / "budget_model_bundle.joblib",
    MOECSO_DIR / "koogleAI" / "UIUX" / "logos" / "koogle_glasses_gray_bg.png",
    MOECSO_DIR / "koogleAI" / "UIUX" / "logos" / "koogle_logo_beige_bg.png",
]

BUILDS = [
    {
        "name": "BudgetEstimatorV2",
        "script": GUI_SCRIPTS_DIR / "budget_gui.py",
        "args": [
            "--onefile", "--windowed",
            "--collect-all", "sklearn",
            "--collect-all", "mord",
            "--collect-all", "scipy",
            "--distpath", str(EXE_DIR),
            "--workpath", str(BUILD_CACHE_DIR),
            "--specpath", str(BUILD_CACHE_DIR),
            "--name", "BudgetEstimatorV2",
        ],
    },
    {
        "name": "koogleAI",
        "script": GUI_SCRIPTS_DIR / "hub_gui.py",
        "args": [
            "--onefile", "--windowed",
            "--distpath", str(EXE_DIR),
            "--workpath", str(BUILD_CACHE_DIR),
            "--specpath", str(BUILD_CACHE_DIR),
            "--name", "koogleAI",
        ],
    },
]


def build_one(build: dict, progress: Progress, overall_task, step_task) -> bool:
    """Run one PyInstaller build as a subprocess, streaming its output into
    the progress bar's description line instead of printing it raw."""
    script_path: Path = build["script"]
    if not script_path.exists():
        progress.console.print(f"[red]Could not find {script_path} - skipping.[/red]")
        return False

    # Run PyInstaller with cwd = the script's own folder, and pass just the
    # filename - this way dist/build always land next to the source scripts
    # (GUI_SCRIPTS_DIR), no matter what directory build_all.py was launched
    # from (PyCharm's run-config cwd, a shortcut, a different terminal, ...).
    cmd = [sys.executable, "-m", "PyInstaller", *build["args"], script_path.name]

    proc = subprocess.Popen(
        cmd,
        cwd=script_path.parent,
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
        exe_path = EXE_DIR / f"{build['name']}.exe"
        progress.console.print(f"[green]✓ {build['name']}.exe built[/green] -> {exe_path}")
    else:
        progress.console.print(f"[red]✗ {build['name']} failed (exit code {proc.returncode})[/red]")
        progress.console.print(f"  last output line: {last_line}")

    return ok


def print_resolved_paths():
    """Print exactly what this run computed for MOECSO_DIR and every build's
    script path, BEFORE anything else runs - so if a path is wrong on a
    given machine, it's obvious immediately instead of hiding behind a
    generic "not found" during the progress bar."""
    console.print(f"[bold]MOECSO_DIR[/bold]: {MOECSO_DIR}")
    console.print(f"[bold]GUI_SCRIPTS_DIR[/bold]: {GUI_SCRIPTS_DIR}")
    console.print(f"[bold]EXE_DIR[/bold] (where the .exe files will be written): {EXE_DIR}")
    for build in BUILDS:
        script_path: Path = build["script"]
        mark = "[green]found[/green]" if script_path.exists() else "[red]MISSING[/red]"
        console.print(f"  {build['name']}: {script_path}  -  {mark}")
    console.print()


def copy_assets():
    """Copy each data file the exes look for beside themselves into
    EXE_DIR, so the finished folder is fully self-contained. Non-fatal if a
    source file is missing - just warns, since these are looked up with a
    MOECSO-based fallback anyway (see resolve_asset() in the GUI scripts)."""
    console.print("\n[bold]Copying data files next to the exes:[/bold]")
    for src in ASSETS_TO_COPY:
        dst = EXE_DIR / src.name
        if not src.exists():
            console.print(f"  [yellow]skipped[/yellow] {src.name} - not found at {src}")
            continue
        shutil.copy2(src, dst)
        console.print(f"  [green]copied[/green] {src.name} -> {dst}")


def main():
    print_resolved_paths()
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
        copy_assets()
        console.print(f"\n[green bold]All builds succeeded.[/green bold] Everything is in: {EXE_DIR}")
        console.print("That whole folder (the two .exe files + the data files just copied in) "
                       "can now be moved anywhere as one self-contained unit.")
        sys.exit(0)
    else:
        console.print("\n[red bold]One or more builds failed[/red bold] - scroll up for the full PyInstaller log.")
        sys.exit(1)


if __name__ == "__main__":
    main()