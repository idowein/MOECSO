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

Run:
    python budget_gui.py

Package as a standalone .exe (once you're happy with it):
    pip install pyinstaller
    pyinstaller --onefile --windowed --name BudgetEstimator budget_gui.py
    -> dist/BudgetEstimator.exe
    (bundle budget_model_bundle.joblib in the same folder as the exe, or see
    the --add-data note near the bottom of this file)
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

import joblib
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BUNDLE_PATH = Path(r"C:\Users\idowe\MyProjects\MOECSO\budget_estimation\budget_model_bundle.joblib")

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
        self.geometry("560x640")
        self.resizable(False, False)

        self.selections: dict[str, tk.StringVar] = {}
        self._build_layout()

    # ------------------------------------------------------------------
    def _build_layout(self):
        pad = {"padx": 16, "pady": 6}

        header = ttk.Label(
            self,
            text="Estimate the budget tier for a new call for proposals",
            font=("Segoe UI", 13, "bold"),
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


def load_bundle(path: Path) -> dict:
    if not path.exists():
        messagebox.showerror(
            "Model file not found",
            f"Could not find the model bundle at:\n{path}\n\n"
            "Run the export cell at the end of Budget_estimation.ipynb first.",
        )
        sys.exit(1)
    return joblib.load(path)


if __name__ == "__main__":
    bundle = load_bundle(BUNDLE_PATH)
    app = BudgetEstimatorApp(bundle)
    app.mainloop()
