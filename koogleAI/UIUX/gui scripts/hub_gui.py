"""
Koogle Suite - tool launcher hub (v1)
=======================================
A clean, card-based launcher matching the approved mockup: the Koogle logo
on the left, and four tool cards on the right. Only "Budget Estimation" is
wired up - it launches budget_gui.py as a separate process. The other three
are visual placeholders ("Coming soon") for tools that don't exist yet.

Run:
    python hub_gui.py

Requires: pillow (for the logo image)
    pip install pillow

Package as a standalone .exe later the same way as budget_gui.py:
    pyinstaller --onefile --windowed --name koogleAI hub_gui.py
"""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from PIL import Image, ImageTk

# ---------------------------------------------------------------------------
# Config - edit these for your machine
# ---------------------------------------------------------------------------
LOGO_PATH = Path(r"C:\Users\idowe\MyProjects\MOECSO\koogleAI\UIUX\logos\koogle_logo_beige_bg.png")

# Where budget_gui.py lives when running this hub from source (python hub_gui.py).
BUDGET_TOOL_SCRIPT = Path(r"C:\Users\idowe\MyProjects\MOECSO\koogleAI\UIUX\gui scripts\budget_gui.py")

# Where the PACKAGED budget estimator .exe lives, for when THIS hub is itself
# packaged into an .exe. This must be a full path to the .exe FILE itself
# (not just its folder) - point it at wherever you put BudgetEstimatorV2.exe
# after building it (see budget_gui.py's docstring for that build command).
# The line below assumes you'll drop it in the same "gui scripts" folder as
# this hub - change it if you put it somewhere else.
BUDGET_TOOL_EXE = Path(r"C:\Users\idowe\MyProjects\MOECSO\koogleAI\UIUX\gui scripts\BudgetEstimatorV2.exe")

# True only inside a PyInstaller-built .exe - sys.executable then points at
# THIS exe, not at a Python interpreter, so it can't be used to run a .py file.
IS_FROZEN = getattr(sys, "frozen", False)

# ---------------------------------------------------------------------------
# Palette - lifted from the Koogle logo (warm orange/red/cream), per the mockup
# ---------------------------------------------------------------------------
BG_MAIN = "#FFFFFF"
BG_LEFT_PANEL = "#F5F1EB"
BG_TITLEBAR = "#F7F5F1"
BORDER = "#E4E0D8"

TEXT_DARK = "#1A1512"
TEXT_MUTED = "#8B857D"

ORANGE = "#D9631F"
ORANGE_DARK = "#B84E15"
CARD_ACTIVE_BG = "#FDF0DD"
CARD_ACTIVE_BORDER = "#E0662A"
ICON_ACTIVE_BG = "#D9631F"

CARD_INACTIVE_BG = "#F7F6F3"
CARD_INACTIVE_BORDER = "#EAE7E0"
ICON_INACTIVE_BG = "#DEDAD2"
BADGE_INACTIVE_BG = "#EFEDE8"

TOOLS = [
    {"icon": "\U0001F50D", "title": "Search Engine",
     "subtitle": "Full-text search across the organization", "active": False},
    {"icon": "\U0001F4B0", "title": "Budget Estimation",
     "subtitle": "Estimate a call-for-proposals budget tier", "active": True},
    {"icon": "\U0001F5FA", "title": "Knowledge Map",
     "subtitle": "Explore relationships between research topics", "active": False},
    {"icon": "\U0001F91D", "title": "Knowledge Brokering",
     "subtitle": "Solutions for matching expertise to needs", "active": False},
]


def rounded_rect(canvas: tk.Canvas, x0, y0, x1, y1, radius, **kwargs):
    """Draw a rounded rectangle on a Canvas (Tkinter has no native primitive
    for this) using a smoothed polygon."""
    points = [
        x0 + radius, y0, x1 - radius, y0, x1, y0, x1, y0 + radius,
        x1, y1 - radius, x1, y1, x1 - radius, y1, x0 + radius, y1,
        x0, y1, x0, y1 - radius, x0, y0 + radius, x0, y0,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class ToolCard(tk.Canvas):
    """One rounded, card-style button: icon square, title, subtitle, badge.
    Only clickable when `active` is True. Redraws itself to the actual
    available width on every resize, instead of using a fixed pixel width -
    otherwise it clips (or leaves empty space) whenever the window isn't
    exactly the size it was designed at."""

    HEIGHT = 78
    MIN_WIDTH = 360  # never draw narrower than this, to keep text legible

    def __init__(self, parent, tool: dict, on_open=None):
        super().__init__(parent, height=self.HEIGHT, bg=BG_MAIN, highlightthickness=0)
        self.tool = tool
        self.on_open = on_open
        self._last_width = None
        self.bind("<Configure>", self._on_resize)
        if tool["active"]:
            self.bind("<Button-1>", lambda e: self.on_open())
            self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
            self.bind("<Leave>", lambda e: self.config(cursor=""))

    def _on_resize(self, event):
        width = max(event.width, self.MIN_WIDTH)
        if width == self._last_width:
            return  # avoid redundant redraws when height-only changes fire
        self._last_width = width
        self._draw(width)

    def _draw(self, width: int):
        self.delete("all")
        active = self.tool["active"]
        bg = CARD_ACTIVE_BG if active else CARD_INACTIVE_BG
        border = CARD_ACTIVE_BORDER if active else CARD_INACTIVE_BORDER
        rounded_rect(self, 2, 2, width - 2, self.HEIGHT - 2, 14,
                     fill=bg, outline=border, width=2 if active else 1)

        # icon square
        icon_size = 50
        icon_x0, icon_y0 = 16, (self.HEIGHT - icon_size) // 2
        icon_bg = ICON_ACTIVE_BG if active else ICON_INACTIVE_BG
        rounded_rect(self, icon_x0, icon_y0, icon_x0 + icon_size, icon_y0 + icon_size, 10,
                     fill=icon_bg, outline="")
        self.create_text(icon_x0 + icon_size / 2, icon_y0 + icon_size / 2,
                          text=self.tool["icon"], font=("Segoe UI Emoji", 18),
                          fill="white" if active else "#8B857D")

        # badge (right side) - drawn before the title so we know how much
        # width is left for the title/subtitle text to wrap into
        if active:
            bw, bh = 78, 30
            badge_text, badge_fill, badge_outline = "Open  \u2192", ORANGE, ""
        else:
            bw, bh = 96, 26
            badge_text, badge_fill, badge_outline = "Coming soon", BADGE_INACTIVE_BG, CARD_INACTIVE_BORDER
        bx1 = width - 18
        bx0 = bx1 - bw
        by0 = (self.HEIGHT - bh) / 2
        rounded_rect(self, bx0, by0, bx0 + bw, by0 + bh, bh / 2,
                     fill=badge_fill, outline=badge_outline)
        self.create_text(bx0 + bw / 2, by0 + bh / 2, text=badge_text,
                          font=("Segoe UI", 10 if active else 9, "bold" if active else "normal"),
                          fill="white" if active else TEXT_MUTED)

        # title + subtitle - width-limited so long subtitles wrap instead of
        # running under the badge
        text_x = icon_x0 + icon_size + 18
        title_color = TEXT_DARK if active else TEXT_MUTED
        available = max(bx0 - 16 - text_x, 80)
        self.create_text(text_x, self.HEIGHT / 2 - 12, text=self.tool["title"],
                          font=("Segoe UI", 13, "bold"), fill=title_color, anchor="w",
                          width=available)
        self.create_text(text_x, self.HEIGHT / 2 + 10, text=self.tool["subtitle"],
                          font=("Segoe UI", 9), fill=TEXT_MUTED, anchor="w",
                          width=available)


class KoogleSuiteHub(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("koogleAI")
        self.geometry("1000x680")
        self.configure(bg=BG_MAIN)
        self.minsize(900, 600)
        self._build_layout()

    # ------------------------------------------------------------------
    def _build_layout(self):
        # --- Left panel: logo ---
        left = tk.Frame(self, bg=BG_LEFT_PANEL, width=320)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        logo_holder = tk.Frame(left, bg=BG_LEFT_PANEL)
        logo_holder.pack(expand=True)

        self._logo_photo = self._load_logo(size=220)
        if self._logo_photo is not None:
            tk.Label(logo_holder, image=self._logo_photo, bg=BG_LEFT_PANEL).pack()
        else:
            placeholder = tk.Frame(logo_holder, bg="#EDE6DA", width=220, height=220)
            placeholder.pack()
            placeholder.pack_propagate(False)
            tk.Label(placeholder, text="Koogle", bg="#EDE6DA", fg=ORANGE,
                     font=("Segoe UI", 16, "bold")).pack(expand=True)

        tk.Label(logo_holder, text="Internal tools, in one place", bg=BG_LEFT_PANEL,
                 fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(pady=(18, 2))
        tk.Label(logo_holder, text="koogleAI \u00b7 Version 1.0", bg=BG_LEFT_PANEL,
                 fg=TEXT_MUTED, font=("Segoe UI", 9)).pack()

        # --- Right panel: tool cards ---
        right = tk.Frame(self, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)

        content = tk.Frame(right, bg=BG_MAIN)
        content.pack(fill="both", expand=True, padx=48, pady=48)

        tk.Label(content, text="Choose a tool", bg=BG_MAIN, fg=TEXT_DARK,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(content, text="Pick where you'd like to start. More tools are on the way.",
                 bg=BG_MAIN, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 24))

        for tool in TOOLS:
            card = ToolCard(content, tool, on_open=self._open_budget_tool)
            card.pack(fill="x", pady=(0, 16))

    # ------------------------------------------------------------------
    def _load_logo(self, size: int):
        if not LOGO_PATH.exists():
            return None
        try:
            img = Image.open(LOGO_PATH).convert("RGBA")
            img.thumbnail((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _open_budget_tool(self):
        if IS_FROZEN:
            # This hub is itself a packaged .exe - sys.executable would just
            # relaunch THIS exe, so we have to launch the OTHER packaged exe.
            if not BUDGET_TOOL_EXE.exists():
                messagebox.showerror(
                    "Not found",
                    f"Could not find:\n{BUDGET_TOOL_EXE}\n\n"
                    "Build it first with PyInstaller (see budget_gui.py's docstring), "
                    "and make sure BUDGET_TOOL_EXE at the top of this file points to it.",
                )
                return
            try:
                subprocess.Popen([str(BUDGET_TOOL_EXE)])
            except Exception as exc:
                messagebox.showerror("Could not open Budget Estimation", str(exc))
        else:
            # Running from source (python hub_gui.py) - sys.executable IS a
            # real Python interpreter here, so this launches the .py directly.
            if not BUDGET_TOOL_SCRIPT.exists():
                messagebox.showerror(
                    "Not found",
                    f"Could not find:\n{BUDGET_TOOL_SCRIPT}\n\n"
                    "Make sure budget_gui.py is in the same folder as this hub.",
                )
                return
            try:
                subprocess.Popen([sys.executable, str(BUDGET_TOOL_SCRIPT)])
            except Exception as exc:
                messagebox.showerror("Could not open Budget Estimation", str(exc))


if __name__ == "__main__":
    app = KoogleSuiteHub()
    app.mainloop()