"""
Koogle Suite - tool launcher hub (v2, "soft" redesign + loading splash)
=======================================================================
A soft, light launcher: white, sky blue, soft orange and lilac. The Koogle
logo and the Chief Scientist Office logo sit in a lilac sidebar on the left,
and four tool cards on the right. Two tools are wired up, each launched as a
separate process:
    Search Engine      -> koggle_search_engine.exe (beside this script/exe)
    Budget Estimation  -> budget_gui.py (from source) or BudgetEstimatorV2.exe
                          (when packaged)
The other two are "Coming soon" placeholders.

Budget Estimation is a heavy exe (sklearn/scipy), so clicking it opens a
loading window over the hub. It tracks the real launch (process started ->
loading -> the estimator's window appears on screen) and closes as soon as
the estimator is up. The bar paces itself by how long the estimator took
last time on this PC (kept in %LOCALAPPDATA%\\KoogleSuite\\launch_times.json).

koggle_search_engine.exe is large and is NOT kept in git - copy it by hand
into the folder this hub runs from (add it to .gitignore).

While the hub prepares itself, a small borderless loading window is shown:
the Koogle logo floats on a white card, a progress bar follows the real
loading steps (Fonts -> Logos -> Tools), and it ends with an "All set!"
state before the launcher appears.

All rounded shapes, soft shadows and line icons are rendered with Pillow at
3x and downsampled, so edges stay smooth (Tkinter's own canvas shapes are
not anti-aliased). Text is drawn by Tk on top of those images.

Run:
    python hub_gui.py

Requires: pillow
    pip install pillow

Assets - any image extension (.png/.jpg/...). Looked up beside this
script/exe, inside the exe bundle (build_all.py embeds them), then in
MOECSO/koogleAI/UIUX/logos and MOECSO/koogleAI/UIUX/gui scripts:
    koogleAI_logo2.*           - Koogle logo (its flat background is removed
                                 automatically so it sits on a white card)
    chief-scientist-logo.*     - Chief Scientist Office logo
    fonts/*.ttf  (optional)    - e.g. Rubik-Regular.ttf, Rubik-Medium.ttf,
                                 Rubik-SemiBold.ttf from Google Fonts. On
                                 Windows they are loaded privately (no install
                                 needed). Without them the app uses Segoe UI.

Package as a standalone .exe: use build_all.py (in this same folder), which
builds this AND budget_gui.py together. Keep both .exe files - and ideally
the two logo PNGs and the fonts folder - in the same folder as each other.
"""

from __future__ import annotations

import functools
import json
import math
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

# True only inside a PyInstaller-built .exe - sys.executable then points at
# THIS exe, not at a Python interpreter, so it can't be used to run a .py file.
IS_FROZEN = getattr(sys, "frozen", False)

# The folder THIS file (or, if frozen, this .exe) actually sits in right now.
# The budget-tool exe is always looked up here, beside this one, so both
# exes can be moved anywhere together.
APP_DIR = Path(sys.executable if IS_FROZEN else __file__).resolve().parent

APP_VERSION = "2.0"

# The loading window stays up at least this long, so it never just flickers.
MIN_SPLASH_SECONDS = 1.6
# How long the "All set!" state is shown before the launcher appears.
READY_HOLD_MS = 900

# Loading window shown while a heavy tool (the budget estimator) starts up.
# It closes as soon as the tool's own window appears on screen.
TOOL_READY_HOLD_MS = 700          # "Ready!" shown this long before closing
TOOL_LAUNCH_TIMEOUT = 120.0       # give up waiting for the tool's window (s)
DEFAULT_LAUNCH_SECONDS = 12.0     # first-run guess of how long a tool takes
# Remembers how long each tool took to open last time, so the progress bar
# paces itself realistically on this PC.
LAUNCH_TIMES_FILE = (Path(os.environ.get("LOCALAPPDATA") or Path.home())
                     / "KoogleSuite" / "launch_times.json")


def find_moecso_dir() -> Path | None:
    """Best-effort only: locate the MOECSO project folder starting from
    APP_DIR, checking at every level going up whether THIS folder is named
    "MOECSO" or a "MOECSO" folder sits right next to it. Returns None
    (never raises) if it can't be found - MOECSO is only a fallback for
    optional assets when running from source."""
    for folder in [APP_DIR] + list(APP_DIR.parents):
        if folder.name == "MOECSO":
            return folder
        sibling = folder / "MOECSO"
        if sibling.is_dir():
            return sibling
    return None


MOECSO_DIR = find_moecso_dir()


# Inside a PyInstaller --onefile exe, files added with --add-data are
# unpacked here at runtime (build_all.py bundles both logos this way).
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def resolve_asset(stems: tuple[str, ...]) -> Path | None:
    """Find an image by name, whatever its extension (.png / .jpg / ...).
    Looks, in order: beside this script/exe, inside the exe bundle, then
    the MOECSO logos and gui-scripts folders. Returns None if not found -
    the UI then shows a text placeholder instead of the logo."""
    folders = [APP_DIR, BUNDLE_DIR]
    if MOECSO_DIR is not None:
        ui_dir = MOECSO_DIR / "koogleAI" / "UIUX"
        folders += [ui_dir / "logos", ui_dir / "gui scripts"]
    for folder in folders:
        for stem in stems:
            for ext in IMAGE_EXTS:
                candidate = folder / f"{stem}{ext}"
                if candidate.is_file():
                    return candidate
    return None


# ---------------------------------------------------------------------------
# Config - file names WITHOUT extension; the first name found wins
# ---------------------------------------------------------------------------
LOGO_PATH = resolve_asset(("koogleAI_logo2", "koogle_logo_beige_bg"))
CSO_LOGO_PATH = resolve_asset(("chief-scientist-logo", "cso_logo"))
FONTS_DIR = APP_DIR / "fonts"

BUDGET_TOOL_SCRIPT = APP_DIR / "budget_gui.py"
BUDGET_TOOL_EXE = APP_DIR / "BudgetEstimatorV2.exe"

# The search engine ships as a prebuilt exe that lives in the run folder,
# beside this script/exe (too large for git - it is copied there by hand).
SEARCH_ENGINE_EXE = APP_DIR / "koggle_search_engine.exe"

# ---------------------------------------------------------------------------
# Palette - white, sky, soft orange, lilac
# ---------------------------------------------------------------------------
BG_MAIN = "#FFFFFF"
BG_SIDEBAR = "#F6F3FC"
BG_FOOTER = "#FBFAFE"
LINE = "#ECE9F4"
LINE_SOFT = "#F1EEF7"

INK = "#2A2840"
MUTED = "#615E78"

LILAC_PILL_BG = "#E9E1F8"
LILAC_PILL_TEXT = "#5B4396"
LILAC_SOFT = "#EEE7FA"
LILAC_DOT = "#E4DBF6"
LILAC_TRACK = "#F1ECFA"

SKY_CHIP_BG = "#E3F2FB"
SKY_CHIP_TEXT = "#1F6F9E"
SKY_DOT = "#4FA8D8"
SKY_CIRCLE = "#DCEFFB"
PEACH_CIRCLE = "#FFE4D2"
PEACH_SOFT = "#FFF1E7"

CARD_BG = "#FFFFFF"
CARD_BORDER = "#ECE9F4"
BADGE_BG = "#F3F1F8"

ACTIVE_BG = "#FFF6EF"
ACTIVE_BORDER = "#F5BE9C"
ACTIVE_SHADOW = "#E8875A"
ACTIVE_SUBTITLE = "#5E5468"
OPEN_BG = "#F9CBAE"
OPEN_BG_HOVER = "#F6B893"
OPEN_TEXT = "#7A3110"

DOT_SKY = "#7EC4E8"
DOT_PEACH = "#F2A27A"
DOT_LILAC = "#A88BDA"

LOGO_SHADOW = "#6F55B5"
SOFT_SHADOW = "#2A2840"

# Look of an available (clickable) tool card, one per colour family
THEME_PEACH = {"bg": ACTIVE_BG, "border": ACTIVE_BORDER, "shadow": ACTIVE_SHADOW,
               "subtitle": ACTIVE_SUBTITLE, "btn": OPEN_BG, "btn_hover": OPEN_BG_HOVER,
               "btn_text": OPEN_TEXT}
THEME_SKY = {"bg": "#F3FAFE", "border": "#A9D8F2", "shadow": "#4FA8D8",
             "subtitle": "#4E5A6E", "btn": "#CDE9F8", "btn_hover": "#B7DFF5",
             "btn_text": "#164F72"}

# Each tool has its own soft colour identity (icon tile background, icon stroke).
# "launch" names the tool to start when the card is clicked (None = coming soon).
TOOLS = [
    {"icon": "search", "title": "Search Engine",
     "subtitle": "Full-text search across the organization",
     "tile": "#CFE8F7", "stroke": "#1F6F9E", "active": True,
     "launch": "search", "theme": THEME_SKY},
    {"icon": "database", "title": "Budget Estimation",
     "subtitle": "Estimate a call-for-proposals budget tier",
     "tile": "#FBD3B8", "stroke": "#9A4318", "active": True,
     "launch": "budget", "theme": THEME_PEACH,
     # heavy exe (sklearn/scipy) - show a loading window until it opens.
     # Set "loading_window": True on any other tool to give it one too.
     "loading_window": True, "loading_label": "Loading the estimator"},
    {"icon": "map", "title": "Knowledge Map",
     "subtitle": "Explore relationships between research topics",
     "tile": "#EEE7FA", "stroke": "#6F55B5", "active": False},
    {"icon": "users", "title": "Knowledge Brokering",
     "subtitle": "Solutions for matching expertise to needs",
     "tile": "#E6EEFA", "stroke": "#4A63B0", "active": False},
]

SS = 3  # supersampling factor for anti-aliased shapes


# ---------------------------------------------------------------------------
# Platform setup (must run before tk.Tk())
# ---------------------------------------------------------------------------
def setup_platform() -> None:
    if sys.platform != "win32":
        return
    import ctypes

    # Crisp rendering on high-DPI screens instead of blurry bitmap scaling.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    # Load bundled fonts privately for this process only (no install needed).
    if FONTS_DIR.is_dir():
        FR_PRIVATE = 0x10
        for ttf in list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.otf")):
            try:
                ctypes.windll.gdi32.AddFontResourceExW(str(ttf), FR_PRIVATE, 0)
            except Exception:
                pass


def animations_enabled() -> bool:
    """Respect Windows' "Show animations in Windows" setting (off = still)."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        value = ctypes.c_int(1)
        SPI_GETCLIENTAREAANIMATION = 0x1042
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(value), 0)
        return bool(value.value)
    except Exception:
        return True


def round_window_corners(win: tk.Misc) -> None:
    """Native rounded corners + soft shadow for a borderless window on
    Windows 11. Silently does nothing elsewhere (the window stays square)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
        DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND = 33, 2
        pref = ctypes.c_int(DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(pref), ctypes.sizeof(pref))
    except Exception:
        pass


def _process_tree(root_pid: int) -> set[int]:
    """root_pid plus all its descendants (Windows). A PyInstaller --onefile
    exe starts a child process that owns the real window, so the window's
    PID is usually NOT the one Popen returned."""
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]

    k32 = ctypes.windll.kernel32
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not snap or snap == wintypes.HANDLE(-1).value:
        return {root_pid}
    children: dict[int, list[int]] = {}
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        ok = k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            children.setdefault(entry.th32ParentProcessID, []).append(entry.th32ProcessID)
            ok = k32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    tree, stack = {root_pid}, [root_pid]
    while stack:
        for child in children.get(stack.pop(), []):
            if child not in tree:
                tree.add(child)
                stack.append(child)
    return tree


def process_has_visible_window(root_pid: int) -> bool | None:
    """True once the process (or one of its children) shows a visible,
    titled top-level window. None where this can't be checked (non-Windows)."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        pids = _process_tree(root_pid)
        found = [False]
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def on_window(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in pids:
                    found[0] = True
                    return False  # stop enumerating
            return True

        user32.EnumWindows(WNDENUMPROC(on_window), 0)
        return found[0]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Pillow rendering helpers (all sizes in device pixels)
# ---------------------------------------------------------------------------
def rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


@functools.lru_cache(maxsize=1024)
def _rrect_mask(w: int, h: int, r: float, inset: float = 0.0) -> Image.Image:
    W, H = max(1, w * SS), max(1, h * SS)
    m = Image.new("L", (W, H), 0)
    i = inset * SS
    ImageDraw.Draw(m).rounded_rectangle(
        (i, i, W - 1 - i, H - 1 - i), radius=max(0.0, (r - inset) * SS), fill=255)
    return m.resize((max(1, w), max(1, h)), Image.LANCZOS)


def _paint(img: Image.Image, color: str, mask: Image.Image, dest=(0, 0)) -> None:
    layer = Image.new("RGBA", mask.size, rgb(color) + (0,))
    layer.putalpha(mask)
    img.alpha_composite(layer, dest=dest)


def render_box(w: int, h: int, r: float, fill: str, border: str | None = None,
               bw: float = 1.0, shadow: tuple | None = None) -> tuple[Image.Image, int]:
    """Rounded rectangle with optional border and soft drop shadow.
    shadow = (color, alpha 0..1, blur_px, offset_y_px).
    Returns (RGBA image, pad) - draw it at (x - pad, y - pad)."""
    pad = 0
    if shadow:
        _, _, blur, dy = shadow
        pad = int(math.ceil(blur + abs(dy))) + 2
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow:
        color, alpha, blur, dy = shadow
        sm = Image.new("L", img.size, 0)
        sm.paste(_rrect_mask(w, h, r).point(lambda v: int(v * alpha)), (pad, pad + int(dy)))
        sm = sm.filter(ImageFilter.GaussianBlur(blur / 2))
        layer = Image.new("RGBA", img.size, rgb(color) + (0,))
        layer.putalpha(sm)
        img.alpha_composite(layer)
    if border:
        _paint(img, border, _rrect_mask(w, h, r), (pad, pad))
        _paint(img, fill, _rrect_mask(w, h, r, bw), (pad, pad))
    else:
        _paint(img, fill, _rrect_mask(w, h, r), (pad, pad))
    return img, pad


@functools.lru_cache(maxsize=256)
def render_circle(d: int, color: str) -> Image.Image:
    d = max(1, d)
    m = Image.new("L", (d * SS, d * SS), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * SS - 1, d * SS - 1), fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    img = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    _paint(img, color, m)
    return img


@functools.lru_cache(maxsize=128)
def render_star(size: int, color: str) -> Image.Image:
    """Four-point sparkle on a 24-unit grid."""
    size = max(2, size)
    W = size * SS
    k = W / 24
    pts = [(12, 2), (14.2, 9.8), (22, 12), (14.2, 14.2), (12, 22),
           (9.8, 14.2), (2, 12), (9.8, 9.8)]
    m = Image.new("L", (W, W), 0)
    ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in pts], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    _paint(img, color, m)
    return img


def render_icon(name: str, size: int, color: str, stroke: float = 1.8) -> Image.Image:
    """Line icons on a 24-unit grid (same shapes as the mockup)."""
    W = size * SS
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = W / 24
    sw = max(1, int(round(stroke * k)))
    col = rgb(color) + (255,)

    def P(x, y):
        return (x * k, y * k)

    def cap(x, y):
        cx, cy = P(x, y)
        r = sw / 2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)

    def line(*pts):
        d.line([P(*p) for p in pts], fill=col, width=sw, joint="curve")
        cap(*pts[0])
        cap(*pts[-1])

    def ellipse(cx, cy, rx, ry):
        d.ellipse([P(cx - rx, cy - ry), P(cx + rx, cy + ry)], outline=col, width=sw)

    def arc(cx, cy, rx, ry, a0, a1):
        d.arc([P(cx - rx, cy - ry), P(cx + rx, cy + ry)], a0, a1, fill=col, width=sw)
        for a in (a0, a1):
            t = math.radians(a)
            cap(cx + rx * math.cos(t), cy + ry * math.sin(t))

    if name == "search":
        ellipse(11, 11, 7, 7)
        line((16.2, 16.2), (20, 20))
    elif name == "database":
        ellipse(12, 5.5, 7.5, 2.8)
        arc(12, 11.5, 7.5, 2.8, 0, 180)
        arc(12, 17.5, 7.5, 2.8, 0, 180)
        line((4.5, 5.5), (4.5, 17.5))
        line((19.5, 5.5), (19.5, 17.5))
    elif name == "map":
        line((9, 4), (3, 6), (3, 20), (9, 18), (15, 20), (21, 18), (21, 4), (15, 6), (9, 4))
        line((9, 4), (9, 18))
        line((15, 6), (15, 20))
    elif name == "users":
        ellipse(9, 8, 3.5, 3.5)
        arc(9, 20, 6.5, 5.5, 180, 360)
        ellipse(17, 9, 2.6, 2.6)
        arc(17, 19.5, 4.6, 5.0, 270, 355)
    elif name == "arrow":
        line((5, 12), (19, 12))
        line((13, 6), (19, 12), (13, 18))
    elif name == "check":
        line((5, 12.5), (9.5, 17), (19, 7.5))
    return img.resize((size, size), Image.LANCZOS)


def remove_flat_background(img: Image.Image, tolerance: int = 22) -> Image.Image:
    """Make the logo's flat beige background transparent by flood-filling
    from the corners only, so light colours INSIDE the logo are kept."""
    img = img.convert("RGBA")
    probe = img.convert("RGB")
    sentinel = (255, 0, 255)
    w, h = probe.size
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if probe.getpixel(corner) != sentinel:
            ImageDraw.floodfill(probe, corner, sentinel, thresh=tolerance)
    r, g, b = probe.split()
    is_bg = ImageChops.multiply(
        ImageChops.multiply(r.point(lambda v: 255 if v == 255 else 0),
                            g.point(lambda v: 255 if v == 0 else 0)),
        b.point(lambda v: 255 if v == 255 else 0))
    keep = ImageChops.invert(is_bg).filter(ImageFilter.GaussianBlur(0.6))
    img.putalpha(ImageChops.multiply(img.getchannel("A"), keep))
    return img


def load_koogle_logo(max_px: int | None = None) -> Image.Image | None:
    """Koogle logo with its background removed, cropped to the artwork.
    max_px shrinks it first (fast path for the loading window)."""
    if LOGO_PATH is None:
        return None
    try:
        img = Image.open(LOGO_PATH).convert("RGBA")
        if max_px:
            img.thumbnail((max_px * 2, max_px * 2), Image.LANCZOS)
        img = remove_flat_background(img)
        img = img.crop(img.getbbox() or (0, 0, *img.size))
        if max_px:
            img.thumbnail((max_px, max_px), Image.LANCZOS)
        return img
    except Exception:
        return None


def load_cso_logo() -> Image.Image | None:
    if CSO_LOGO_PATH is None:
        return None
    try:
        return Image.open(CSO_LOGO_PATH).convert("RGBA")
    except Exception:
        return None


def ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def wave(t: float, period: float) -> float:
    """0 -> 1 -> 0 smoothly over one period (like CSS ease-in-out keyframes)."""
    return 0.5 - 0.5 * math.cos(2 * math.pi * t / period)


# ---------------------------------------------------------------------------
# Fonts shared by the loading window and the launcher
# ---------------------------------------------------------------------------
class FontKit:
    def __init__(self, root: tk.Misc, scale: float):
        self.root = root
        self.S = scale
        families = set(tkfont.families(root))

        def first(*names, default=""):
            for n in names:
                if n in families:
                    return n
            return default

        self.regular = first("Rubik", "Segoe UI Variable Text", "Segoe UI", "Helvetica Neue",
                             "Helvetica", "DejaVu Sans", default="Arial")
        self.semi = first("Rubik SemiBold", "Rubik Medium", "Segoe UI Semibold",
                          "Segoe UI Variable Display Semib")
        self._cache: dict = {}

    def get(self, size: float, weight: str = "regular") -> tkfont.Font:
        key = (size, weight)
        if key not in self._cache:
            px = -int(round(size * self.S))
            if weight == "regular":
                f = tkfont.Font(self.root, family=self.regular, size=px)
            elif self.semi:
                f = tkfont.Font(self.root, family=self.semi, size=px)
            else:
                f = tkfont.Font(self.root, family=self.regular, size=px, weight="bold")
            self._cache[key] = f
        return self._cache[key]


# ---------------------------------------------------------------------------
# Loading window
# ---------------------------------------------------------------------------
class SplashScreen:
    """Small borderless loading window (480 x 480 logical px).

    The app drives it with:
        set_step(key, label, start_pct, end_pct)  - a step begins
        finish_step(key, end_pct)                 - that step is done
        show_ready()                              - "All set!" state
        close(on_closed)                          - fade out and destroy
    """

    W = H = 480
    STEPS = [  # key, chip label, done bg, done text
        ("fonts", "Fonts", SKY_CHIP_BG, SKY_CHIP_TEXT),
        ("logos", "Logos", LILAC_SOFT, LILAC_PILL_TEXT),
        ("tools", "Tools", PEACH_SOFT, OPEN_TEXT),
    ]
    TOOL_STEPS = [  # used while launching a tool
        ("start", "Starting", SKY_CHIP_BG, SKY_CHIP_TEXT),
        ("load", "Loading", LILAC_SOFT, LILAC_PILL_TEXT),
        ("window", "Window", PEACH_SOFT, OPEN_TEXT),
    ]
    # Logo "stage" (156 x 150) and the progress bar, in logical px
    STAGE_X, STAGE_Y = 162, 36
    BAR_X, BAR_Y, BAR_W, BAR_H = 80, 306, 320, 10

    def __init__(self, root: tk.Misc, scale: float, fonts: FontKit, animate: bool = True, *,
                 title: str = "Koogle Suite", subtitle: str = "Getting your tools ready",
                 status: str = "Starting up", steps: list | None = None,
                 badge_icon: str | None = None,
                 center_over: tuple[int, int, int, int] | None = None):
        self.root = root
        self.S = scale
        self.fonts = fonts
        self.animate = animate
        self.steps = steps or self.STEPS
        self._title_text, self._subtitle_text, self._status_text = title, subtitle, status
        self.badge_icon = badge_icon  # tool icon shown on the logo card while loading
        p = self.px

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg=BG_MAIN)
        w, h = p(self.W), p(self.H)
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        if center_over:  # (x, y, w, h) of a window to centre on
            ox, oy, ow, oh = center_over
            x = min(max(0, ox + (ow - w) // 2), max(0, sw - w))
            y = min(max(0, oy + (oh - h) // 2), max(0, sh - h))
        else:
            x, y = (sw - w) // 2, max(0, (sh - h) // 2 - p(20))
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        try:
            self.win.attributes("-topmost", True)
        except tk.TclError:
            pass

        self.c = tk.Canvas(self.win, width=w, height=h, bg=BG_MAIN,
                           highlightthickness=0, bd=0)
        self.c.pack(fill="both", expand=True)

        self.target = 0.0      # where the bar is heading (0..100)
        self.creep_to = 0.0    # the bar drifts up to here while a step runs
        self.shown = 0.0       # what the bar currently displays
        self.states = {key: "pending" for key, *_ in self.steps}
        self.ready_at: float | None = None
        self._refs: list = []  # keep PhotoImages alive
        self._sized: dict = {}  # PhotoImages for animated sizes
        self._job = None
        self._closing = False

        self._build()
        round_window_corners(self.win)
        self.t0 = time.monotonic()
        self._tick()
        self.win.update()

    # ---------------- helpers ----------------
    def px(self, v: float) -> int:
        return int(round(v * self.S))

    def _photo(self, pil: Image.Image) -> ImageTk.PhotoImage:
        ph = ImageTk.PhotoImage(pil)
        self._refs.append(ph)
        return ph

    def _sized_photo(self, key, factory) -> ImageTk.PhotoImage:
        if key not in self._sized:
            self._sized[key] = ImageTk.PhotoImage(factory())
        return self._sized[key]

    def _stage(self, x: float, y: float) -> tuple[int, int]:
        """Logical stage coords -> device canvas coords."""
        return self.px(self.STAGE_X + x), self.px(self.STAGE_Y + y)

    # ---------------- static layout ----------------
    def _build(self):
        c, p, f = self.c, self.px, self.fonts.get
        W, H = p(self.W), p(self.H)

        # soft background circles + tiny lilac dot behind the logo card
        self.sky = c.create_image(*self._stage(2 + 43, 0 + 43), anchor="center",
                                  image=self._photo(render_circle(p(86), SKY_CIRCLE)))
        self.peach = c.create_image(*self._stage(88 + 34, 76 + 34), anchor="center",
                                    image=self._photo(render_circle(p(68), PEACH_CIRCLE)))
        c.create_image(*self._stage(124 + 7, 10 + 7), anchor="center",
                       image=self._photo(render_circle(p(14), LILAC_DOT)))

        # sparkles (only shown in the "ready" state)
        self.stars = []
        for cx, cy, size, color, delay in ((3, 115, 18, DOT_LILAC, 0.0),
                                           (141, 9, 14, DOT_SKY, 0.5),
                                           (154.5, 51.5, 11, DOT_PEACH, 1.0)):
            item = c.create_image(*self._stage(cx, cy), anchor="center", state="hidden")
            self.stars.append((item, size, color, delay))

        # white logo card with soft shadow + the logo itself (one image)
        card, pad = render_box(p(120), p(120), p(34), BG_MAIN,
                               shadow=(LOGO_SHADOW, 0.14, p(30), p(12)))
        logo = load_koogle_logo(p(96))
        if logo is not None:
            card.alpha_composite(logo, (pad + (p(120) - logo.width) // 2,
                                        pad + (p(120) - logo.height) // 2))
        self.card_center = self._stage(18 + 60, 12 + 60)
        self.card = c.create_image(*self.card_center, anchor="center", image=self._photo(card))
        if logo is None:
            c.create_text(*self.card_center, text="Koogle", font=f(18, "semi"), fill=ACTIVE_SHADOW)

        # badge on the card's corner: the tool's icon while loading (if any),
        # replaced by a check mark that pops in on "ready"
        self.badge_center = self._stage(114 + 17, 108 + 17)
        self.badge = c.create_image(*self.badge_center, anchor="center", state="hidden")
        if self.badge_icon:
            self.c.itemconfig(self.badge, state="normal", image=self._sized_photo(
                ("badge", self.badge_icon, p(42)), lambda: self._badge_image(p(42), self.badge_icon)))

        # title + subtitle
        cx = W // 2
        self.title = c.create_text(cx, p(200), text=self._title_text, font=f(22, "semi"),
                                   fill=INK, anchor="n")
        self.subtitle = c.create_text(cx, p(230), text=self._subtitle_text,
                                      font=f(14), fill=MUTED, anchor="n")

        # status line: label + hopping dots, percentage on the right
        row_y = p(self.BAR_Y - 20)
        self.status = c.create_text(p(self.BAR_X), row_y, text=self._status_text,
                                    font=f(13, "semi"), fill=INK, anchor="w")
        self.dots = []
        for color in (DOT_SKY, DOT_PEACH, DOT_LILAC):
            item = c.create_image(0, row_y, anchor="center",
                                  image=self._photo(render_circle(p(5), color)))
            self.dots.append(item)
        self.pct = c.create_text(p(self.BAR_X + self.BAR_W), row_y, text="0%",
                                 font=f(12, "semi"), fill=MUTED, anchor="e")
        self._place_dots()

        # progress bar: one fixed-size image, repainted every frame
        bw, bh = p(self.BAR_W), p(self.BAR_H)
        self._track = render_box(bw, bh, bh / 2, LILAC_TRACK)[0]
        self.bar_photo = ImageTk.PhotoImage(self._track)
        c.create_image(p(self.BAR_X), p(self.BAR_Y), anchor="nw", image=self.bar_photo)

        # step chips
        self.chip_y = p(self.BAR_Y + self.BAR_H + 18)
        self._draw_chips()

        # footer: "Developed for" + Chief Scientist Office logo
        fy = p(404)
        c.create_rectangle(0, fy, W, H, fill=BG_FOOTER, outline="")
        c.create_line(0, fy, W, fy, fill=LINE_SOFT)
        label_font = f(10, "semi")
        label = "DEVELOPED FOR"
        cso = load_cso_logo()
        if cso is not None:
            cso.thumbnail((p(200), p(46)), Image.LANCZOS)
            flat = Image.new("RGBA", cso.size, rgb(BG_FOOTER) + (255,))
            flat.alpha_composite(cso)
            # multiply onto the footer tint so the logo's white box disappears
            flat = ImageChops.multiply(flat.convert("RGB"),
                                       Image.new("RGB", cso.size, rgb(BG_FOOTER)))
            total = label_font.measure(label) + p(14) + flat.width
            x0 = (W - total) // 2
            mid = fy + p(14) + flat.height // 2
            c.create_text(x0, mid, text=label, font=label_font, fill=MUTED, anchor="w")
            c.create_image(x0 + label_font.measure(label) + p(14), fy + p(14),
                           anchor="nw", image=self._photo(flat))
        else:
            c.create_text(W // 2, fy + p(38),
                          text="Developed for the Chief Scientist Office · Ministry of Education",
                          font=f(11), fill=MUTED)

        # 1px outline (Windows 11 rounds the corners natively)
        c.create_rectangle(0, 0, W - 1, H - 1, outline=LINE)

    def _place_dots(self, t: float = 0.0):
        bbox = self.c.bbox(self.status)
        if not bbox:
            return
        x = bbox[2] + self.px(8) + self.px(2.5)
        base_y = self.px(self.BAR_Y - 20)
        for i, item in enumerate(self.dots):
            dy = 0.0
            if self.animate:
                ph = ((t - i * 0.15) % 1.2) / 1.2
                if ph < 0.8:
                    dy = -4 * math.sin(math.pi * ph / 0.8)
            self.c.coords(item, x + i * self.px(8), base_y + self.px(dy))

    def _chip_image(self, key: str, state: str, label: str, done_bg: str, done_fg: str):
        p, f = self.px, self.fonts.get(12, "semi")
        h = p(28)
        if state == "done":
            w = p(12) + p(13) + p(6) + f.measure(label) + p(12)
            img, _ = render_box(w, h, h / 2, done_bg)
            ic = render_icon("check", p(13), done_fg, stroke=2.6)
            img.alpha_composite(ic, (p(12), (h - ic.height) // 2))
            return img, w, p(12) + p(13) + p(6), done_fg
        if state == "active":
            w = p(12) + p(6) + p(7) + f.measure(label) + p(12)
            img, _ = render_box(w, h, h / 2, PEACH_SOFT, ACTIVE_BORDER, bw=max(1.0, self.S))
            return img, w, p(12) + p(6) + p(7), OPEN_TEXT
        w = p(12) + f.measure(label) + p(12)
        img, _ = render_box(w, h, h / 2, BADGE_BG)
        return img, w, p(12), MUTED

    def _draw_chips(self):
        c, p = self.c, self.px
        c.delete("chip")
        built = []
        for key, label, bg, fg in self.steps:
            img, w, text_x, color = self._chip_image(key, self.states[key], label, bg, fg)
            built.append((key, label, img, w, text_x, color))
        gap = p(8)
        total = sum(b[3] for b in built) + gap * (len(built) - 1)
        x = (p(self.W) - total) // 2
        y = self.chip_y
        self.pulse_item = None
        self.pulse_pos = None
        for key, label, img, w, text_x, color in built:
            c.create_image(x, y, anchor="nw", image=self._photo(img), tags="chip")
            c.create_text(x + text_x, y + p(14), text=label, font=self.fonts.get(12, "semi"),
                          fill=color, anchor="w", tags="chip")
            if self.states[key] == "active":
                self.pulse_pos = (x + p(12) + p(3), y + p(14))
                self.pulse_item = c.create_image(*self.pulse_pos, anchor="center", tags="chip")
            x += w + gap
        self._update_pulse(0.0)

    def _update_pulse(self, t: float):
        if self.pulse_item is None:
            return
        scale = 1 + 0.35 * wave(t, 1.4) if self.animate else 1.0
        d = max(2, self.px(6 * scale))
        ph = self._sized_photo(("pulse", d), lambda: render_circle(d, ACTIVE_SHADOW))
        self.c.itemconfig(self.pulse_item, image=ph)

    def _render_bar(self, value: float, phase: float) -> Image.Image:
        p = self.px
        bw, bh = p(self.BAR_W), p(self.BAR_H)
        img = self._track.copy()
        fw = int(round(bw * value / 100))
        if fw <= 0:
            return img
        fw = max(fw, bh)  # never thinner than a dot
        layer = Image.new("RGBA", (fw, bh), rgb(OPEN_BG_HOVER) + (255,))
        if self.animate and value < 99.5 and self.ready_at is None:
            sw = max(2, int(fw * 0.4))
            sx = int(sw * (-1 + 3.6 * phase))
            sheen = Image.new("RGBA", (fw, bh), (0, 0, 0, 0))
            ImageDraw.Draw(sheen).rounded_rectangle((sx, 0, sx + sw, bh - 1), radius=bh / 2,
                                                    fill=(255, 255, 255, 115))
            layer.alpha_composite(sheen)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), _rrect_mask(fw, bh, bh / 2)))
        img.alpha_composite(layer)
        return img

    # ---------------- animation loop ----------------
    def _tick(self):
        if self._closing:
            return
        t = time.monotonic() - self.t0
        p = self.px

        # progress: drift while a step works, then ease toward the target
        if self.target < self.creep_to:
            self.target = min(self.creep_to, self.target + 0.12)
        self.shown += (self.target - self.shown) * 0.14
        if abs(self.target - self.shown) < 0.05:
            self.shown = self.target
        self.c.itemconfig(self.pct, text=f"{int(round(self.shown))}%")
        self.bar_photo.paste(self._render_bar(self.shown, (t % 1.8) / 1.8))

        if self.animate:
            fy = -7 * wave(t, 3.2)
            self.c.coords(self.card, self.card_center[0], self.card_center[1] + p(fy))
            a = wave(t, 4.5)
            self.c.coords(self.sky, *self._stage(45 + 4 * a, 43 + 5 * a))
            b = wave(t, 5.0)
            self.c.coords(self.peach, *self._stage(122 - 5 * b, 110 - 3 * b))
            self._place_dots(t)
            self._update_pulse(t)

        if self.ready_at is not None:
            self._animate_ready(time.monotonic() - self.ready_at, t)

        self._job = self.win.after(25, self._tick)

    @staticmethod
    def _badge_image(d: int, icon: str) -> Image.Image:
        """Peach circle with a white ring and a line icon (check / tool icon)."""
        ring = render_circle(d, BG_MAIN).copy()
        inner_d = max(2, int(d * 34 / 42))
        o = (d - inner_d) // 2
        ring.alpha_composite(render_circle(inner_d, OPEN_BG), (o, o))
        is_check = icon == "check"
        ic_d = max(2, int(d * (18 if is_check else 20) / 42))
        ring.alpha_composite(render_icon(icon, ic_d, OPEN_TEXT, stroke=2.8 if is_check else 2.2),
                             ((d - ic_d) // 2, (d - ic_d) // 2))
        return ring

    def _animate_ready(self, since: float, t: float):
        p = self.px
        x = min(1.0, since / 0.6) if self.animate else 1.0
        scale = (0.6 + 0.4 * ease_out_back(x)) if self.animate else 1.0
        d = max(4, int(p(42) * scale))
        self.c.itemconfig(self.badge, state="normal", image=self._sized_photo(
            ("badge", "check", d), lambda: self._badge_image(d, "check")))
        for item, size, color, delay in self.stars:
            s = (0.7 + 0.3 * wave(t - delay, 1.6)) if self.animate else 1.0
            sd = max(2, p(size * s))
            self.c.itemconfig(item, state="normal",
                              image=self._sized_photo(("star", color, sd),
                                                      lambda: render_star(sd, color)))

    # ---------------- API used by the app ----------------
    def set_step(self, key: str, label: str, start: float, end: float, creep: bool = True):
        """creep=False: the bar only moves when set_target() is called."""
        self.states[key] = "active"
        self.target = max(self.target, start)
        self.creep_to = max(self.target, end - 4) if creep else self.target
        self.c.itemconfig(self.status, text=label)
        self._place_dots()
        self._draw_chips()

    def finish_step(self, key: str, end: float):
        self.states[key] = "done"
        self.target = max(self.target, end)
        self.creep_to = self.target
        self._draw_chips()

    def set_target(self, value: float):
        """Move the bar toward `value` (never backwards)."""
        self.target = max(self.target, min(100.0, value))
        self.creep_to = max(self.creep_to, self.target)

    def progress_settled(self) -> bool:
        return self.shown >= self.target - 0.5

    def show_ready(self, title: str = "All set!", subtitle: str = "Opening Koogle Suite"):
        for key in self.states:
            self.states[key] = "done"
        self.target = self.creep_to = self.shown = 100.0
        self.c.itemconfig(self.title, text=title)
        self.c.itemconfig(self.subtitle, text=subtitle)
        self.c.itemconfig(self.status, text="Ready")
        for item in self.dots:
            self.c.itemconfig(item, state="hidden")
        self._draw_chips()
        self.ready_at = time.monotonic()

    def close(self, on_closed=None):
        """Fade out (where supported), then destroy."""
        steps = 6 if self.animate else 1

        def fade(i=steps):
            if i <= 0:
                self._closing = True
                if self._job is not None:
                    try:
                        self.win.after_cancel(self._job)
                    except tk.TclError:
                        pass
                self.win.destroy()
                if on_closed:
                    on_closed()
                return
            try:
                self.win.attributes("-alpha", i / steps)
            except tk.TclError:
                pass
            self.win.after(28, fade, i - 1)

        fade(steps - 1 if steps > 1 else 0)


# ---------------------------------------------------------------------------
# The launcher
# ---------------------------------------------------------------------------
class KoogleSuiteHub(tk.Tk):
    SIDEBAR_W = 320
    CONTENT_MAX_W = 760

    def __init__(self):
        super().__init__()
        self.withdraw()  # stays hidden until loading is finished
        self.title("Koogle Suite")
        self.configure(bg=BG_MAIN)

        self.S = max(1.0, self.winfo_fpixels("1i") / 96.0)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self._initial_size = (min(self.px(1200), int(sw * 0.92)),
                              min(self.px(780), int(sh * 0.88)))
        w, h = self._initial_size
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 20)}")
        self.minsize(min(self.px(940), sw), min(self.px(700), sh))

        self.fonts = FontKit(self, self.S)
        self._koogle: Image.Image | None = None
        self._cso: Image.Image | None = None
        self._photos: dict = {}       # cache of rendered PhotoImages
        self._hit_boxes: list = []    # [((x0, y0, x1, y1), tool), ...] clickable cards
        self._hover: str | None = None    # title of the card under the mouse
        self._opening: set[str] = set()   # titles of tools being launched right now
        self._redraw_job = None
        self.canvas: tk.Canvas | None = None

        try:
            self.splash: SplashScreen | None = SplashScreen(
                self, self.S, self.fonts, animate=animations_enabled())
        except Exception:
            self.splash = None  # never let the loading window block the app
        self._t_start = time.monotonic()
        self.after(60, self._step_fonts)

    # ---------------- loading sequence ----------------
    def _splash(self, method: str, *args):
        if self.splash is not None:
            try:
                getattr(self.splash, method)(*args)
            except Exception:
                pass

    def _step_fonts(self):
        self._splash("set_step", "fonts", "Loading fonts", 4, 25)
        self.after(30, self._do_fonts)

    def _do_fonts(self):
        try:
            for size, weight in ((11, "semi"), (12, "regular"), (12, "semi"), (14, "regular"),
                                 (15, "semi"), (16, "regular"), (17, "semi"), (18, "semi"),
                                 (22, "semi"), (40, "semi")):
                self.font(size, weight).measure("Koogle")
        except Exception:
            pass
        self._splash("finish_step", "fonts", 25)
        self._splash("set_step", "logos", "Preparing logos", 25, 65)
        # image work runs off the UI thread so the loading window keeps moving
        worker = threading.Thread(target=self._load_logo_images, daemon=True)
        worker.start()
        self._wait_for(worker, self._after_logos)

    def _load_logo_images(self):
        """Pillow only - safe to run in a background thread."""
        self._koogle = load_koogle_logo()
        self._cso = load_cso_logo()

    def _wait_for(self, worker: threading.Thread, then):
        if worker.is_alive():
            self.after(40, self._wait_for, worker, then)
        else:
            then()

    def _after_logos(self):
        if self._koogle is not None:
            try:
                icon = self._koogle.copy()
                icon.thumbnail((64, 64), Image.LANCZOS)
                self._window_icon = ImageTk.PhotoImage(icon)
                self.iconphoto(True, self._window_icon)
            except Exception:
                pass
        self._splash("finish_step", "logos", 65)
        self._splash("set_step", "tools", "Drawing tool cards", 65, 100)
        self.after(30, self._do_tools)

    def _do_tools(self):
        self._build_canvas()
        try:
            # Render everything once at the starting window size, so the
            # launcher appears fully drawn (the images are cached).
            self._draw_all(*self._initial_size)
        except Exception:
            pass
        self._splash("finish_step", "tools", 100)
        self._wait_until_ready()

    def _wait_until_ready(self):
        if self.splash is None:
            self._reveal()
            return
        elapsed = time.monotonic() - self._t_start
        if not self.splash.progress_settled() or elapsed < MIN_SPLASH_SECONDS:
            self.after(40, self._wait_until_ready)
            return
        self._splash("show_ready")
        self.after(READY_HOLD_MS, self._reveal)

    def _reveal(self):
        self.deiconify()
        self.update_idletasks()
        self.lift()
        try:
            self.focus_force()
        except tk.TclError:
            pass
        if self.splash is not None:
            splash, self.splash = self.splash, None
            try:
                splash.close()
            except Exception:
                pass

    # ---------------- sizing / fonts ----------------
    def px(self, v: float) -> int:
        return int(round(v * self.S))

    def font(self, size: float, weight: str = "regular") -> tkfont.Font:
        return self.fonts.get(size, weight)

    def elide(self, text: str, font: tkfont.Font, max_w: int) -> str:
        if font.measure(text) <= max_w:
            return text
        while text and font.measure(text + "…") > max_w:
            text = text[:-1]
        return text.rstrip() + "…"

    def photo(self, key, factory) -> ImageTk.PhotoImage:
        if key not in self._photos:
            self._photos[key] = ImageTk.PhotoImage(factory())
        return self._photos[key]

    # ---------------- composite renders ----------------
    def _render_logo_block(self) -> tuple[Image.Image, int]:
        """Koogle logo on a white card, with soft sky + peach circles behind."""
        p = self.px
        size, margin = p(236), p(48)
        img = Image.new("RGBA", (size + 2 * margin, size + 2 * margin), (0, 0, 0, 0))
        o = margin
        img.alpha_composite(render_circle(p(132), SKY_CIRCLE), (o - p(18), o - p(10)))
        c2 = p(104)
        img.alpha_composite(render_circle(c2, PEACH_CIRCLE), (o + size + p(14) - c2, o + size + p(6) - c2))
        card_w = size - 2 * p(12)
        card, pad = render_box(card_w, card_w, p(40), BG_MAIN,
                               shadow=(LOGO_SHADOW, 0.12, p(32), p(12)))
        img.alpha_composite(card, (o + p(12) - pad, o + p(12) - pad))
        if self._koogle is not None:
            logo = self._koogle.copy()
            logo.thumbnail((p(176), p(176)), Image.LANCZOS)
            lx = o + (size - logo.width) // 2
            ly = o + (size - logo.height) // 2
            img.alpha_composite(logo, (lx, ly))
        return img, margin

    def _render_cso_card(self) -> tuple[Image.Image, int, int, int]:
        p = self.px
        logo = self._cso.copy()
        logo.thumbnail((p(168), p(168)), Image.LANCZOS)
        w, h = p(256), logo.height + 2 * p(16)
        card, pad = render_box(w, h, p(20), BG_MAIN, shadow=(SOFT_SHADOW, 0.06, p(20), p(6)))
        card.alpha_composite(logo, (pad + (w - logo.width) // 2, pad + p(16)))
        return card, pad, w, h

    def _render_pill(self, w: int, h: int, fill: str, dot: str | None = None,
                     arrow: tuple | None = None) -> Image.Image:
        img, _ = render_box(w, h, h / 2, fill)
        if dot:
            d = self.px(6)
            img.alpha_composite(render_circle(d, dot), (self.px(12), (h - d) // 2))
        if arrow:
            x, color = arrow
            a = render_icon("arrow", self.px(16), color, stroke=2.0)
            img.alpha_composite(a, (x, (h - a.height) // 2))
        return img

    def _render_card(self, w: int, h: int, tool: dict) -> tuple[Image.Image, int]:
        p = self.px
        if tool["active"]:
            th = tool["theme"]
            img, pad = render_box(w, h, p(22), th["bg"], th["border"], bw=1.5 * self.S,
                                  shadow=(th["shadow"], 0.16, p(36), p(14)))
            t, r, ic = p(56), p(18), p(24)
        else:
            img, pad = render_box(w, h, p(22), CARD_BG, CARD_BORDER, bw=max(1.0, self.S))
            t, r, ic = p(52), p(16), p(22)
        tile, _ = render_box(t, t, r, tool["tile"])
        icon = render_icon(tool["icon"], ic, tool["stroke"])
        tile.alpha_composite(icon, ((t - ic) // 2, (t - ic) // 2))
        img.alpha_composite(tile, (pad + p(20), pad + (h - t) // 2))
        return img, pad

    # ---------------- layout ----------------
    def _build_canvas(self):
        if self.canvas is not None:
            return
        self.canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._schedule_redraw)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))
        self.canvas.bind("<Button-1>", self._on_click)
        self.bind("<Return>", self._on_return)

    def _schedule_redraw(self, _event=None):
        if self._redraw_job is not None:
            self.after_cancel(self._redraw_job)
        self._redraw_job = self.after(16, self._redraw)

    def _redraw(self):
        self._redraw_job = None
        if self.canvas is None:
            return
        W, H = self.canvas.winfo_width(), self.canvas.winfo_height()
        if W < 10 or H < 10:
            return
        self._draw_all(W, H)

    def _draw_all(self, W: int, H: int):
        self.canvas.delete("all")
        self._hit_boxes = []
        sb = self.px(self.SIDEBAR_W)
        self._draw_sidebar(sb, H)
        self._draw_main(sb, W, H)

    def _draw_sidebar(self, sb: int, H: int):
        c, p = self.canvas, self.px
        c.create_rectangle(0, 0, sb, H, fill=BG_SIDEBAR, outline="")
        c.create_line(sb - 1, 0, sb - 1, H, fill=LINE)
        cx = sb // 2

        # bottom: "Developed for" + CSO logo card
        bottom = H - p(32)
        if self._cso is not None:
            card_img, pad, cw, ch = self._render_cso_card()
            ph = self.photo(("cso", self.S), lambda: card_img)
            card_top = bottom - ch
            c.create_image(cx - cw // 2 - pad, card_top - pad, image=ph, anchor="nw")
            label_y = card_top - p(10)
        else:
            c.create_text(cx, bottom, text="The Chief Scientist Office · Ministry of Education",
                          font=self.font(12), fill=MUTED, anchor="s", width=sb - p(48),
                          justify="center")
            label_y = bottom - p(36)
        c.create_text(cx, label_y, text="DEVELOPED FOR", font=self.font(11, "semi"),
                      fill=MUTED, anchor="s")
        bottom_block_top = label_y - p(16)

        # top: logo block + name + tagline + version pill (centred in the space above)
        logo_size = p(236)
        name_h, tag_h, pill_h = p(28), p(20), p(24)
        group_h = logo_size + p(24) + name_h + p(6) + tag_h + p(12) + pill_h
        top = max(p(40), (bottom_block_top - group_h) // 2)

        block, margin = self._render_logo_block()
        ph = self.photo(("logo_block", self.S), lambda: block)
        c.create_image(cx - logo_size // 2 - margin, top - margin, image=ph, anchor="nw")
        if self._koogle is None:
            c.create_text(cx, top + logo_size // 2, text="Koogle", font=self.font(26, "semi"),
                          fill=ACTIVE_SHADOW)

        y = top + logo_size + p(24)
        c.create_text(cx, y, text="Koogle Suite", font=self.font(22, "semi"), fill=INK, anchor="n")
        y += name_h + p(6)
        c.create_text(cx, y, text="Internal tools, in one place", font=self.font(14),
                      fill=MUTED, anchor="n")
        y += tag_h + p(12)
        f = self.font(12, "semi")
        label = f"version {APP_VERSION}"
        pw = f.measure(label) + 2 * p(12)
        pill = self.photo(("vpill", pw, pill_h), lambda: self._render_pill(pw, pill_h, LILAC_PILL_BG))
        c.create_image(cx - pw // 2, y, image=pill, anchor="nw")
        c.create_text(cx, y + pill_h // 2, text=label, font=f, fill=LILAC_PILL_TEXT)

    def _draw_main(self, sb: int, W: int, H: int):
        c, p = self.canvas, self.px
        side_pad = p(72) if W - sb > p(760) else p(40)
        x0 = sb + side_pad
        cw = max(p(420), min(p(self.CONTENT_MAX_W), W - x0 - side_pad))
        y = max(p(36), min(p(64), (H - p(650)) // 2 + p(36)))

        # chip
        f = self.font(12, "semi")
        chip_text = "Chief Scientist Office · Ministry of Education"
        chip_h = p(26)
        chip_w = p(12) + p(6) + p(8) + f.measure(chip_text) + p(12)
        chip = self.photo(("chip", chip_w, chip_h),
                          lambda: self._render_pill(chip_w, chip_h, SKY_CHIP_BG, dot=SKY_DOT))
        c.create_image(x0, y, image=chip, anchor="nw")
        c.create_text(x0 + p(26), y + chip_h // 2, text=chip_text, font=f,
                      fill=SKY_CHIP_TEXT, anchor="w")
        y += chip_h + p(14)

        # heading
        c.create_text(x0 - p(2), y, text="Choose a tool", font=self.font(40, "semi"),
                      fill=INK, anchor="nw")
        y += p(50) + p(10)
        c.create_text(x0, y, text="Pick where you’d like to start. More tools are on the way.",
                      font=self.font(16), fill=MUTED, anchor="nw")
        y += p(24) + p(32)

        # cards - active ones first so their shadows sit underneath the others
        layout = []
        yy = y
        for tool in TOOLS:
            h = p(100) if tool["active"] else p(88)
            layout.append((tool, yy, h))
            yy += h + p(14)
        cards_bottom = yy - p(14)
        for tool, ty, h in sorted(layout, key=lambda t: not t[0]["active"]):
            self._draw_card(tool, x0, ty, cw, h)

        # footer
        available = sum(1 for t in TOOLS if t["active"])
        footer = f"{available} of {len(TOOLS)} tools available · Koogle Suite · version {APP_VERSION}"
        fy = max(H - p(40), cards_bottom + p(28))
        c.create_text(x0, fy, text=footer, font=self.font(12), fill=MUTED, anchor="sw")

    def _draw_card(self, tool: dict, x: int, y: int, w: int, h: int):
        c, p = self.canvas, self.px
        img = self.photo(("card", tool["title"], w, h), lambda: self._render_card(w, h, tool)[0])
        pad = (img.width() - w) // 2
        c.create_image(x - pad, y - pad, image=img, anchor="nw")

        active = tool["active"]
        tile = p(56) if active else p(52)
        tx = x + p(20) + tile + p(18)
        cy = y + h // 2

        # right side: Open button or "Coming soon" badge
        if active:
            th = tool["theme"]
            opening = tool["title"] in self._opening
            f = self.font(15, "semi")
            label = "Opening…" if opening else "Open"
            bh = p(44)
            tw = f.measure(label)
            bw = p(20) + tw + p(8) + p(16) + p(20)
            bx = x + w - p(20) - bw
            hot = opening or self._hover == tool["title"]
            fill = th["btn_hover"] if hot else th["btn"]
            btn = self.photo(("open", label, fill, bw, bh),
                             lambda: self._render_pill(bw, bh, fill,
                                                       arrow=(p(20) + tw + p(8), th["btn_text"])))
            c.create_image(bx, cy - bh // 2, image=btn, anchor="nw")
            c.create_text(bx + p(20), cy, text=label, font=f, fill=th["btn_text"], anchor="w")
            self._hit_boxes.append(((x, y, x + w, y + h), tool))
            right_edge = bx
        else:
            f = self.font(12, "semi")
            label = "Coming soon"
            bh = p(26)
            bw = f.measure(label) + 2 * p(12)
            bx = x + w - p(20) - bw
            badge = self.photo(("badge", bw, bh), lambda: self._render_pill(bw, bh, BADGE_BG))
            c.create_image(bx, cy - bh // 2, image=badge, anchor="nw")
            c.create_text(bx + bw // 2, cy, text=label, font=f, fill=MUTED)
            right_edge = bx

        max_text = right_edge - p(16) - tx
        tf = self.font(18 if active else 17, "semi")
        sf = self.font(14)
        c.create_text(tx, cy - p(11), text=self.elide(tool["title"], tf, max_text),
                      font=tf, fill=INK, anchor="w")
        c.create_text(tx, cy + p(13), text=self.elide(tool["subtitle"], sf, max_text),
                      font=sf, fill=tool["theme"]["subtitle"] if active else MUTED, anchor="w")

    # ---------------- interaction ----------------
    def _tool_at(self, x: int, y: int) -> dict | None:
        for (x0, y0, x1, y1), tool in self._hit_boxes:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return tool
        return None

    def _set_hover(self, tool: dict | None):
        title = tool["title"] if tool else None
        if title != self._hover:
            self._hover = title
            self.canvas.config(cursor="hand2" if title else "")
            self._schedule_redraw()

    def _on_motion(self, event):
        self._set_hover(self._tool_at(event.x, event.y))

    def _on_click(self, event):
        tool = self._tool_at(event.x, event.y)
        if tool is not None:
            self._open_tool(tool)

    def _on_return(self, _event=None):
        """Enter opens the card under the mouse, if there is one."""
        for _, tool in self._hit_boxes:
            if tool["title"] == self._hover:
                self._open_tool(tool)
                return

    def _open_tool(self, tool: dict):
        title = tool["title"]
        if title in self._opening:
            return  # ignore double clicks while launching
        launchers = {"budget": self._launch_budget_process,
                     "search": self._launch_search_engine}
        launch = launchers.get(tool.get("launch"))
        proc = launch() if launch else None
        if proc is None:
            return
        self._opening.add(title)
        self._schedule_redraw()

        if tool.get("loading_window") and self._start_tool_loading(tool, proc):
            return  # the loading window clears the "Opening…" state when done

        def done():
            self._opening.discard(title)
            self._schedule_redraw()

        self.after(1800, done)

    # ---------------- loading window while a tool starts ----------------
    def _window_rect(self) -> tuple[int, int, int, int]:
        return (self.winfo_rootx(), self.winfo_rooty(), self.winfo_width(), self.winfo_height())

    @staticmethod
    def _read_launch_times() -> dict:
        try:
            return json.loads(LAUNCH_TIMES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _expected_launch_seconds(self, key: str) -> float:
        try:
            return min(90.0, max(2.0, float(self._read_launch_times()[key])))
        except Exception:
            return DEFAULT_LAUNCH_SECONDS

    def _remember_launch_seconds(self, key: str, seconds: float):
        try:
            times = self._read_launch_times()
            old = times.get(key)
            times[key] = round(seconds if old is None else 0.5 * float(old) + 0.5 * seconds, 2)
            LAUNCH_TIMES_FILE.parent.mkdir(parents=True, exist_ok=True)
            LAUNCH_TIMES_FILE.write_text(json.dumps(times), encoding="utf-8")
        except Exception:
            pass  # remembering timings is a nicety, never an error

    def _start_tool_loading(self, tool: dict, proc: subprocess.Popen) -> bool:
        try:
            splash = SplashScreen(
                self, self.S, self.fonts, animate=animations_enabled(),
                title=tool["title"], subtitle="Starting up — this can take a few seconds",
                status="Starting", steps=SplashScreen.TOOL_STEPS,
                badge_icon=tool["icon"], center_over=self._window_rect())
        except Exception:
            return False
        splash.set_step("start", "Starting", 0, 8, creep=False)
        state = {"tool": tool, "proc": proc, "splash": splash, "t0": time.monotonic(),
                 "expected": self._expected_launch_seconds(tool["launch"]), "loading": False}
        self.after(150, self._watch_tool_launch, state)
        return True

    def _watch_tool_launch(self, state: dict):
        splash: SplashScreen = state["splash"]
        proc: subprocess.Popen = state["proc"]
        elapsed = time.monotonic() - state["t0"]
        expected = state["expected"]

        try:
            if not state["loading"] and elapsed > 0.4:
                state["loading"] = True
                splash.finish_step("start", 10)
                splash.set_step("load", state["tool"].get("loading_label", "Loading"),
                                10, 14, creep=False)

            # Pace the bar by how long this tool took last time; past that,
            # keep inching forward without ever claiming 100%.
            if elapsed <= expected:
                splash.set_target(10 + 80 * (elapsed / expected))
            else:
                splash.set_target(90 + 6 * (1 - math.exp(-(elapsed - expected) / expected)))

            has_window = process_has_visible_window(proc.pid)
            exit_code = proc.poll()
            if has_window or (has_window is None and elapsed >= max(4.0, expected)):
                # has_window is None = can't detect windows here (not Windows):
                # assume it is up after the usual time.
                self._finish_tool_launch(state, "ready", elapsed)
            elif exit_code is not None:
                self._finish_tool_launch(state, "exited", elapsed, exit_code)
            elif elapsed > TOOL_LAUNCH_TIMEOUT:
                self._finish_tool_launch(state, "timeout", elapsed)
            else:
                self.after(150, self._watch_tool_launch, state)
        except tk.TclError:
            pass  # the hub was closed meanwhile

    def _finish_tool_launch(self, state: dict, outcome: str, elapsed: float,
                            exit_code: int | None = None):
        tool, splash = state["tool"], state["splash"]
        title = tool["title"]

        def clear_opening():
            self._opening.discard(title)
            self._schedule_redraw()

        if outcome == "ready":
            self._remember_launch_seconds(tool["launch"], elapsed)
            splash.show_ready("Ready!", f"{title} is open")
            self.after(TOOL_READY_HOLD_MS, lambda: splash.close(clear_opening))
            return

        splash.close(clear_opening)
        if outcome == "exited" and exit_code not in (0, None):
            messagebox.showerror(
                f"Could not open {title}",
                f"{title} closed before its window appeared (exit code {exit_code}).",
            )

    def _launch_search_engine(self) -> subprocess.Popen | None:
        if not SEARCH_ENGINE_EXE.exists():
            messagebox.showerror(
                "Search Engine not found",
                f"Could not find:\n{SEARCH_ENGINE_EXE}\n\n"
                "koggle_search_engine.exe is not kept in git. Copy it into the "
                "same folder as this app and try again.",
            )
            return None
        try:
            return subprocess.Popen([str(SEARCH_ENGINE_EXE)], cwd=str(SEARCH_ENGINE_EXE.parent))
        except Exception as exc:
            messagebox.showerror("Could not open Search Engine", str(exc))
            return None

    def _launch_budget_process(self) -> subprocess.Popen | None:
        if IS_FROZEN:
            # This hub is itself a packaged .exe - launch the OTHER packaged exe.
            if not BUDGET_TOOL_EXE.exists():
                messagebox.showerror(
                    "Not found",
                    f"Could not find:\n{BUDGET_TOOL_EXE}\n\n"
                    "Build it with build_all.py and keep BudgetEstimatorV2.exe "
                    "in the same folder as this app.",
                )
                return None
            cmd = [str(BUDGET_TOOL_EXE)]
        else:
            # Running from source - sys.executable is a real Python interpreter.
            if not BUDGET_TOOL_SCRIPT.exists():
                messagebox.showerror(
                    "Not found",
                    f"Could not find:\n{BUDGET_TOOL_SCRIPT}\n\n"
                    "Make sure budget_gui.py is in the same folder as this hub.",
                )
                return None
            cmd = [sys.executable, str(BUDGET_TOOL_SCRIPT)]
        try:
            return subprocess.Popen(cmd, cwd=str(APP_DIR))
        except Exception as exc:
            messagebox.showerror("Could not open Budget Estimation", str(exc))
            return None


if __name__ == "__main__":
    setup_platform()
    app = KoogleSuiteHub()
    app.mainloop()