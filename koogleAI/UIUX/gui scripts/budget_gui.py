"""
Budget tier estimator - GUI (v1)
=================================
Loads `budget_model_bundle.joblib` (produced by the export cell at the end of
Budget_estimation.ipynb) and lets a user pick the same input ranges used to
train the model, then shows the predicted budget tier + class probabilities.

This is an ASSOCIATIVE BENCHMARK, not a guaranteed price: it reflects the
statistical pattern between proposed methodology and historical call pricing
on a small dataset (see the notebook, section 9). Treat the output as a
reference range for setting a new call's budget, not as ground truth.

Window / taskbar icon: the Koogle logo (koogleAI_logo2.* or
koogle_logo_beige_bg.*, any image extension), looked up beside this
script/exe, inside the exe bundle (build_all.py embeds it), then in
MOECSO/koogleAI/UIUX/logos. Its flat background is removed so the icon is
clean. If an icon.ico sits beside the script/exe it takes priority. If
nothing is found, Tk's default feather icon remains.

Header logo: HEADER_LOGO_PATH below points to an image shown at the top of
the window. Its own background should already match GUI_BG ("#F0F0F0") so it
blends in instead of showing a white square - see koogle_glasses_gray_bg.png.

Run:
    pip install pillow
    python budget_gui.py

Package as a standalone .exe: use build_all.py (in the same folder as this
script), or run PyInstaller directly - see its docstring. The finished .exe
can then be moved anywhere (a network drive, another PC, ...): it always
looks for budget_model_bundle.joblib and koogle_glasses_gray_bg.png right
beside itself first, so just keep those two files in the same folder as the
exe and it's fully self-contained.

    Note: --collect-all sklearn/mord/scipy is required even though this
    script never imports them directly. joblib.load() has to reconstruct the
    saved Pipeline/LogisticAT objects at runtime, which needs those packages
    present - but PyInstaller only bundles what it sees imported in the code,
    so without --collect-all the .exe fails with "No module named 'sklearn'".
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

import joblib
import pandas as pd
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

# sklearn/mord are never called directly in this file - joblib.load() needs
# them internally to unpickle the trained Pipeline/LogisticAT objects, and
# importing them here (in addition to --collect-all below) helps PyInstaller's
# static analysis find them.
import sklearn  # noqa: F401
import mord  # noqa: F401


# The folder THIS file (or, if frozen, this .exe) actually sits in right
# now - wherever that is. Everything this app needs (the model bundle, the
# header logo) is looked up here FIRST. That means you can move
# BudgetEstimatorV2.exe anywhere (a network drive, another PC, a USB stick,
# ...) as long as you bring its data files along with it, and it keeps
# working, with no dependency on a fixed/derived MOECSO path.
APP_DIR = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent

# Inside a PyInstaller --onefile exe, files added with --add-data are
# unpacked here at runtime (build_all.py embeds the Koogle logo this way).
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))

# Give this process its own taskbar identity on Windows, so when it runs
# from source (python.exe) the taskbar shows THIS window's icon instead of
# grouping it under Python's icon. Must run before any window is created.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "MOECSO.KoogleSuite.BudgetEstimator")
    except Exception:
        pass


def find_moecso_dir() -> Path | None:
    """Best-effort only: locate the MOECSO project folder starting from
    APP_DIR, checking at every level going up whether THIS folder is named
    "MOECSO" or a "MOECSO" folder sits right next to it. Returns None
    (never raises) if it can't be found - this is only a fallback for
    running from source during development, never something a deployed
    .exe should be forced to depend on."""
    for folder in [APP_DIR] + list(APP_DIR.parents):
        if folder.name == "MOECSO":
            return folder
        sibling = folder / "MOECSO"
        if sibling.is_dir():
            return sibling
    return None

MOECSO_DIR = find_moecso_dir()

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
# The Koogle logo used for the window/taskbar icon - same names, in the same
# order, as LOGO_PATH in hub_gui.py and KOOGLE_LOGO in build_all.py.
KOOGLE_LOGO_STEMS = ("koogleAI_logo2", "koogle_logo_beige_bg")
ICON_SIZES = (256, 64, 48, 32, 16)


def find_image(stems: tuple[str, ...]) -> Path | None:
    """Find an image by name, whatever its extension. Looks beside this
    script/exe, inside the exe bundle, then in the MOECSO logos and
    gui-scripts folders. Returns None if not found."""
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


def remove_flat_background(img: Image.Image, tolerance: int = 22) -> Image.Image:
    """Make a logo's flat background transparent by flood-filling from the
    corners only, so light colours INSIDE the logo are kept (same as the hub)."""
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
    return img.crop(img.getbbox() or (0, 0, *img.size))


def apply_koogle_icon(window: tk.Tk) -> None:
    """Window + taskbar icon for `window` (and every dialog it opens):
    icon.ico beside the script/exe if present, otherwise the Koogle logo.
    Never raises - worst case the default Tk icon stays."""
    for folder in (APP_DIR, BUNDLE_DIR):
        ico = folder / ICON_FILENAME
        if ico.is_file():
            try:
                window.iconbitmap(default=str(ico))  # .ico only, Windows
                return
            except tk.TclError:
                break  # unreadable .ico - fall through to the Koogle logo

    logo_path = find_image(KOOGLE_LOGO_STEMS)
    if logo_path is None:
        return
    try:
        logo = remove_flat_background(Image.open(logo_path))
        side = max(logo.size)  # pad to a square so the icon isn't stretched
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.alpha_composite(logo, ((side - logo.width) // 2, (side - logo.height) // 2))
        photos = [ImageTk.PhotoImage(square.resize((s, s), Image.LANCZOS), master=window)
                  for s in ICON_SIZES]
        window._koogle_icons = photos  # keep references, or Tk drops the images
        window.iconphoto(True, *photos)
    except Exception:
        pass


def resolve_asset(filename: str, moecso_subpath: tuple[str, ...]) -> Path:
    """Look for `filename` right beside this script/exe first - the
    simplest deployment: copy the exe + its data files into one folder,
    anywhere you like, and it's fully self-contained. Falls back to the
    fixed location inside the MOECSO project structure (if MOECSO could be
    found at all) for running from source."""
    beside = APP_DIR / filename
    if beside.exists():
        return beside
    if MOECSO_DIR is not None:
        return MOECSO_DIR.joinpath(*moecso_subpath)
    return beside  # doesn't exist either, but callers degrade gracefully


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BUNDLE_PATH = resolve_asset(
    "budget_model_bundle.joblib",
    ("koogleAI", "budget_estimation", "budget_model_bundle.joblib"),
)
ICON_FILENAME = "icon.ico"   # optional override; otherwise the Koogle logo is used

# Header logo shown at the top of the window - path to the image with the
# background already matched to GUI_BG (see koogle_glasses_gray_bg.png).
HEADER_LOGO_PATH = resolve_asset(
    "koogle_glasses_gray_bg.png",
    ("koogleAI", "UIUX", "logos", "koogle_glasses_gray_bg.png"),
)
HEADER_LOGO_SIZE = 96  # px, square thumbnail

# Explicit background color for the whole window, so it matches the logo's
# own background exactly instead of relying on whatever gray the OS theme
# happens to use.
GUI_BG = "#F0F0F0"


# Human-readable labels for the raw column names, since the model's feature
# names (e.g. "duration_months_bin") aren't meant for an end user to read.
FIELD_TITLES = {
    "duration_months_bin": "Research duration",
    "subject_count_bin": "Number of subjects / participants",
    "site_count_bin": "Number of sites / participating schools",
    "data_waves_count_bin": "Number of data collection waves",
    "target_populations_count_bin": "Number of target populations",
    "deliverables_level": "Deliverables level",
    "collection_mode": "Data collection mode",
    "tool_development_type": "Tool development type",
}


class BudgetEstimatorApp(tk.Tk):
    def __init__(self, bundle: dict):
        super().__init__()
        self.bundle = bundle
        self.pipeline = bundle["pipeline"]
        self.feature_columns = bundle["feature_columns"]
        self.target_labels = bundle["target_labels"]
        self.ordinal_categories = bundle["ordinal_categories"]
        self.nominal_categories = bundle["nominal_categories"]

        self.title("Call for Proposals - Budget Tier Estimator")
        self.geometry("560x680")
        self.resizable(False, False)
        self.configure(bg=GUI_BG)
        self._set_window_icon()

        self.selections: dict[str, tk.StringVar] = {}
        self._header_photo = None  # keep a reference, or Tkinter garbage-collects it
        self._build_layout()

    # ------------------------------------------------------------------
    def _set_window_icon(self):
        apply_koogle_icon(self)

    # ------------------------------------------------------------------
    def _add_header_logo(self):
        """Show the header image centered at the top of the window, if it's
        present at HEADER_LOGO_PATH. Silently skipped if missing/unreadable,
        so a wrong path never crashes the app - it just shows no logo."""
        if not HEADER_LOGO_PATH.exists():
            return
        try:
            img = Image.open(HEADER_LOGO_PATH).convert("RGBA")
            img.thumbnail((HEADER_LOGO_SIZE, HEADER_LOGO_SIZE), Image.LANCZOS)
            self._header_photo = ImageTk.PhotoImage(img)
        except Exception:
            return
        tk.Label(self, image=self._header_photo, bg=GUI_BG).pack(pady=(14, 2))

    # ------------------------------------------------------------------
    def _build_layout(self):
        pad = {"padx": 16, "pady": 6}

        self._add_header_logo()

        header = tk.Label(
            self,
            text="Estimate the budget tier for a new call for proposals",
            font=("Segoe UI", 13, "bold"),
            bg=GUI_BG,
            wraplength=520,
        )
        header.pack(anchor="w", **pad)

        subheader = ttk.Label(
            self,
            text=(f"Trained on {self.bundle.get('n_train_rows', '?')} proposals across "
                  f"{self.bundle.get('n_train_calls', '?')} independent calls. "
                  "This is an associative benchmark, not a guaranteed price."),
            wraplength=520,
            foreground="#555555",
        )
        subheader.pack(anchor="w", padx=16, pady=(0, 12))

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16)

        # --- Ordinal (binned) inputs: dropdown of the exact bin labels used in training ---
        for feat, categories in self.ordinal_categories.items():
            self._add_dropdown(form, feat, categories)

        # --- Nominal inputs: dropdown of the raw category values used in training ---
        for feat, categories in self.nominal_categories.items():
            self._add_dropdown(form, feat, categories)

        predict_btn = ttk.Button(self, text="Estimate budget tier", command=self._on_predict)
        predict_btn.pack(pady=18)

        self.result_frame = ttk.LabelFrame(self, text="Result")
        self.result_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.result_label = ttk.Label(
            self.result_frame, text="Fill in the fields above and click \"Estimate budget tier\".",
            font=("Segoe UI", 12), wraplength=500, justify="left",
        )
        self.result_label.pack(anchor="w", padx=10, pady=10)

        self.proba_label = ttk.Label(self.result_frame, text="", font=("Segoe UI", 10), justify="left")
        self.proba_label.pack(anchor="w", padx=10, pady=(0, 10))

    def _add_dropdown(self, parent, feature_name: str, categories: list[str]):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)

        label_text = FIELD_TITLES.get(feature_name, feature_name)
        ttk.Label(row, text=label_text, width=34, anchor="w").pack(side="left")

        var = tk.StringVar(value=categories[0])
        combo = ttk.Combobox(row, textvariable=var, values=categories, state="readonly", width=26)
        combo.pack(side="left", fill="x", expand=True)

        self.selections[feature_name] = var

    # ------------------------------------------------------------------
    def _build_feature_row(self) -> pd.DataFrame:
        """Turn the current dropdown selections into a single-row DataFrame
        with columns in exactly the order the trained pipeline expects."""
        row = {col: 0 for col in self.feature_columns}

        # Ordinal features: selected label -> its integer code, i.e. its
        # position in the SAME ordered category list the model was trained on.
        for feat, categories in self.ordinal_categories.items():
            if feat not in self.feature_columns:
                continue
            selected = self.selections[feat].get()
            row[feat] = categories.index(selected)

        # Nominal features: build the one-hot column name and set it to 1.
        # If that particular dummy column was dropped during feature
        # reduction, the row simply stays at 0 for it - the model just can't
        # distinguish that raw value, exactly as it couldn't during training.
        for feat in self.nominal_categories:
            selected = self.selections[feat].get()
            dummy_col = f"{feat}_{selected}"
            if dummy_col in row:
                row[dummy_col] = 1

        return pd.DataFrame([row], columns=self.feature_columns)

    def _on_predict(self):
        try:
            X = self._build_feature_row()
            pred = self.pipeline.predict(X)[0]

            proba_text = ""
            try:
                proba = self.pipeline.predict_proba(X)[0]
                proba_lines = [f"  {label}: {p:.0%}" for label, p in zip(self.target_labels, proba)]
                proba_text = "Estimated probability per tier:\n" + "\n".join(proba_lines)
            except (AttributeError, NotImplementedError):
                pass  # not every ordinal estimator exposes predict_proba - degrade gracefully

            self.result_label.config(text=f"Estimated budget tier:  {pred}")
            self.proba_label.config(text=proba_text)

        except Exception as exc:  # surfaced to the user instead of a silent crash
            messagebox.showerror("Prediction failed", f"Could not compute an estimate:\n\n{exc}")


def fatal_error(title: str, message: str) -> None:
    """Show an error before the main window exists, then exit. Uses a hidden
    root that carries the Koogle icon, so the dialog (and its taskbar entry)
    doesn't show Tk's feather or a stray empty "tk" window."""
    root = tk.Tk()
    root.withdraw()
    apply_koogle_icon(root)
    messagebox.showerror(title, message, parent=root)
    root.destroy()
    sys.exit(1)


def load_bundle(path: Path) -> dict:
    if not path.exists():
        fatal_error(
            "Model file not found",
            f"Could not find the model bundle at:\n{path}\n\n"
            "Run the export cell at the end of Budget_estimation.ipynb first.",
        )
    try:
        return joblib.load(path)
    except Exception as exc:
        # In a --windowed exe an unhandled error would just vanish silently.
        fatal_error(
            "Could not load the model",
            f"The model bundle at:\n{path}\n\ncould not be loaded:\n\n{exc}",
        )


if __name__ == "__main__":
    bundle = load_bundle(BUNDLE_PATH)
    app = BudgetEstimatorApp(bundle)
    app.mainloop()