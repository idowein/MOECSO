import os
import time
import threading
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np

# --- CONFIGURATION ---
# Path to your master matrix Excel sheet where each column is a PDF file
MATRIX_EXCEL_PATH = r"C:\Users\idowe\MyProjects\MOECSO\koogle\clean data\cleaned_pdf_words_columns.xlsx"
LOGO_IMAGE_NAME = r"C:\Users\idowe\MyProjects\MOECSO\koogle\koogle logo.png"  # Make sure this file is in the same directory as the script

# Manually set the path to the folder containing your actual PDF files here:
PDF_DIRECTORY_PATH = r"C:\Users\idowe\MyProjects\final reports 17.05.2026"

class SmartSearchApp:
    def __init__(self, root):
        self.root = root
        self.df = None
        
        # Hide the main window context while the splash screen layout is active
        self.root.withdraw()
        
        # Phase 1: Launch the Splash Screen Sequence
        self.show_splash_screen()

    def show_splash_screen(self):
        """
        Creates a borderless modern splash window displaying the Koogle logo.
        """
        self.splash = tk.Toplevel()
        self.splash.title("Koogle - Loading")
        self.splash.overrideredirect(True)
        
        splash_width = 500
        splash_height = 380
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (splash_width / 2))
        y_coordinate = int((screen_height / 2) - (splash_height / 2))
        self.splash.geometry(f"{splash_width}x{splash_height}+{x_coordinate}+{y_coordinate}")
        self.splash.configure(bg="#ffffff")

        logo_path = os.path.join(os.path.dirname(__file__) if __file__ else "", LOGO_IMAGE_NAME)
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                target_width = 350
                w_percent = target_width / float(pil_image.size[0])
                target_height = int(float(pil_image.size[1]) * float(w_percent))
                
                resized_pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(resized_pil_image)
                
                logo_label = tk.Label(self.splash, image=self.logo_img, bg="#ffffff")
                logo_label.pack(pady=(40, 10))
            except Exception as img_err:
                print(f"Image resize error: {img_err}")
                tk.Label(self.splash, text="KOOGLE", font=("Segoe UI", 36, "bold"), fg="#4285F4", bg="#ffffff").pack(pady=(60, 20))
        else:
            tk.Label(self.splash, text="KOOGLE", font=("Segoe UI", 36, "bold"), fg="#4285F4", bg="#ffffff").pack(pady=(60, 20))

        self.loading_label = tk.Label(self.splash, text="Initializing Koogle Database Engine... 0%", font=("Segoe UI", 10), fg="#5f6368", bg="#ffffff")
        self.loading_label.pack(pady=(15, 5))

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Koogle.Horizontal.TProgressbar", thickness=10, troughcolor="#f1f3f4", background="#4285F4")
        
        self.progress_bar = ttk.Progressbar(self.splash, style="Koogle.Horizontal.TProgressbar", orient="horizontal", length=350, mode="determinate")
        self.progress_bar.pack(pady=5)

        threading.Thread(target=self.load_dataset_worker, daemon=True).start()

    def update_splash_progress(self, percent, text):
        self.progress_bar['value'] = percent
        self.loading_label.config(text=f"{text} {percent}%")
        self.splash.update_idletasks()

    def load_dataset_worker(self):
            try:
                time.sleep(0.5)
                self.root.after(0, self.update_splash_progress, 15, "Connecting to local file directories...")
                
                if not os.path.exists(MATRIX_EXCEL_PATH):
                    self.root.after(0, self.handle_boot_failure, f"Database file path location not uncovered:\n{MATRIX_EXCEL_PATH}")
                    return

                time.sleep(0.5)
                self.root.after(0, self.update_splash_progress, 35, "Opening Excel binary matrix stream arrays...")
                
                # Load raw dataframe
                loaded_df = pd.read_excel(MATRIX_EXCEL_PATH)
                
                time.sleep(0.5)
                self.root.after(0, self.update_splash_progress, 55, "Optimizing database text layers in memory...")
                
                # --- OPTIMIZATION: Normalize the entire dataframe ONCE ahead of time ---
                # This strips whitespace and lowers cases globally, removing the bottleneck
                self.df = loaded_df.dropna(how='all').astype(str).map(lambda x: x.strip().lower() if pd.notna(x) else x)
                
                time.sleep(0.5)
                self.root.after(0, self.update_splash_progress, 80, "Generating fast TF-IDF mapping dictionary...")
                
                # Trigger the newly optimized ultra-fast weight calculator
                self.calculate_database_idf()
                
                time.sleep(0.5)
                self.root.after(0, self.update_splash_progress, 100, "System database array verification complete!")
                time.sleep(0.4)
                
                self.root.after(0, self.launch_main_application)
                
            except Exception as err:
                self.root.after(0, self.handle_boot_failure, f"An unexpected fatal initialization event occurred:\n{err}")
                
    def handle_boot_failure(self, message):
        messagebox.showerror("Fatal Initialization Error", message)
        if hasattr(self, 'splash'):
            self.splash.destroy()
        self.root.destroy()

    def launch_main_application(self):
        self.splash.destroy()
        self.root.deiconify()
        self.root.title("Koogle - Search Cockpit Engine")
        self.root.geometry("800x550")
        self.create_widgets()

    def create_widgets(self):
        search_frame = ttk.Frame(self.root, padding=15)
        search_frame.pack(fill=tk.X)
        
        label = ttk.Label(search_frame, text="Enter Keywords (separated by space):", font=("Segoe UI", 11))
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = ttk.Entry(search_frame, font=("Segoe UI", 11), width=45)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.execute_keyword_search())
        
        self.search_button = ttk.Button(search_frame, text="Count Keywords", command=self.execute_keyword_search)
        self.search_button.pack(side=tk.LEFT)
        
        results_frame = ttk.Frame(self.root, padding=15)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("rank", "filename", "score")
        self.results_table = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        self.results_table.heading("rank", text="Rank")
        self.results_table.heading("filename", text="Document/PDF Name")
        self.results_table.heading("score", text="Combined Keywords Frequency (Hits)")
        
        self.results_table.column("rank", width=60, anchor=tk.CENTER)
        self.results_table.column("filename", width=540, anchor=tk.W)
        self.results_table.column("score", width=160, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_table.yview)
        self.results_table.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_table.pack(fill=tk.BOTH, expand=True)
        
        # --- NEW FEATURE: BIND DOUBLE CLICK EVENT TO TABLE ROWS ---
        self.results_table.bind("<Double-1>", self.on_row_double_click)
        
        self.status_label = ttk.Label(self.root, text=f"Ready. Double-click any row to open its original PDF file.", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def calculate_database_idf(self):
        """
        Computes the Inverse Document Frequency (IDF) for every unique word 
        across all documents during the splash screen loading phase.

        IDF = ln (Total documents / Document containing keyword)
        weight function
        """
        import numpy as np
        total_docs = len(self.df.columns)
        self.word_idf_mapping = {}
        
        # Step 1: Extract a unique vocabulary set across the entire cleaned matrix
        # Since self.df is already flattened, normalized, and cleaned, this is instant
        all_unique_words = set(self.df.values.flatten())
        
        # Step 2: Convert each column vector into a native Python set for O(1) membership lookups
        # This prevents Pandas from rescanning columns over and over again
        doc_sets = [set(self.df[col].dropna()) for col in self.df.columns]
        
        # Step 3: Count document occurrences using lightning-fast set lookups
        for word in all_unique_words:
            if pd.isna(word) or word == 'nan':
                continue
                
            # Count how many document sets contain this word
            doc_count = sum(1 for d_set in doc_sets if word in d_set)
            
            if doc_count > 0:
                # Apply log-smooth IDF formula
                self.word_idf_mapping[word] = np.log(total_docs / float(doc_count))
            else:
                self.word_idf_mapping[word] = 0.0
                
        print(f"Successfully vectorized and mapped weights for {len(self.word_idf_mapping)} unique tokens instantly.")

    def execute_keyword_search(self):
        for row in self.results_table.get_children():
            self.results_table.delete(row)
            
        raw_input = self.search_entry.get().strip()
        if not raw_input:
            self.status_label.config(text="Warning: Keyword field cannot remain empty.")
            return
            
        target_keywords = [w.strip().lower() for w in raw_input.split() if w.strip()]
        if not target_keywords:
            return
            
        self.status_label.config(text=f"Evaluating intersection match matrix for: {', '.join(target_keywords)}...")
        self.root.update_idletasks()
        
        search_results = []

        for column_name in self.df.columns:
            column_series = self.df[column_name].dropna().astype(str).str.strip().str.lower()
            
            contains_all_keywords = True
            weighted_document_score = 0.0
            
            for keyword in target_keywords:
                keyword_hits = (column_series == keyword).sum()
                
                # Strict intersection check (AND condition) remains active
                if keyword_hits == 0:
                    contains_all_keywords = False
                    break
                
                # --- ADVANCED WEIGHTING LAYER (TF-IDF) ---
                # Retrieve the pre-calculated IDF weight (default to 1.0 if not cached)
                word_idf = self.word_idf_mapping.get(keyword, 1.0)
                
                # Calculate the weighted score for this keyword inside the document
                # Term Frequency (hits) * Inverse Document Frequency (rarity)
                weighted_document_score += (keyword_hits * word_idf)
                
            if contains_all_keywords and weighted_document_score > 0:
                search_results.append({
                    "filename": column_name,
                    "score": weighted_document_score
                })
            
        # Sort files based on their sophisticated weighted score rather than raw frequency count
        sorted_results = sorted(search_results, key=lambda x: x["score"], reverse=True)
        
        # for column_name in self.df.columns:
        #     column_series = self.df[column_name].dropna().astype(str).str.strip().str.lower()
            
        #     contains_all_keywords = True
        #     total_file_hits = 0
            
        #     for keyword in target_keywords:
        #         keyword_hits = (column_series == keyword).sum()
        #         if keyword_hits == 0:
        #             contains_all_keywords = False
        #             break
        #         total_file_hits += keyword_hits
                
        #     if contains_all_keywords and total_file_hits > 0:
        #         search_results.append({
        #             "filename": column_name,
        #             "score": total_file_hits
        #         })
                
        #sorted_results = sorted(search_results, key=lambda x: x["score"], reverse=True)
        
        if not sorted_results:
            self.status_label.config(text="Query executed. Zero matching elements found containing ALL parameters.")
            messagebox.showinfo("Zero Matches", "No individual PDF documents contain ALL specified keywords together.")
            return
            
        for rank_index, item in enumerate(sorted_results):
            row_data = (rank_index + 1, item["filename"], f"{item['score']:,} times")
            self.results_table.insert("", tk.END, values=row_data)
            
        self.status_label.config(text="Search completed. Double-click a file row to open it instantly.")

    def on_row_double_click(self, event):
        """
        Triggered when a user double-clicks a row inside the results table.
        Extracts the filename and opens it via the operating system's default handler.
        """
        # Identify the specific item row index that was double-clicked
        selected_item = self.results_table.selection()
        if not selected_item:
            return
            
        # Extract row metadata values (index 1 contains the filename column)
        item_values = self.results_table.item(selected_item[0], "values")
        if not item_values:
            return
            
        pdf_filename = item_values[1] # The document column name from Excel matrix
        
        # Resolve full operating system file path mapping
        full_pdf_path = os.path.join(PDF_DIRECTORY_PATH, pdf_filename)
        
        # Validate that the file actually exists inside the specified path directory
        if not os.path.exists(full_pdf_path):
            messagebox.showerror(
                "File Not Found", 
                f"Could not locate the PDF file inside your directory.\n\nTarget Path:\n{full_pdf_path}\n\nPlease check your PDF_DIRECTORY_PATH setting."
            )
            return
            
        # Launch the file asynchronously using OS native default applications safely
        try:
            self.status_label.config(text=f"Opening document: {pdf_filename}...")
            print(f"Launching external system process for path: {full_pdf_path}")
            
            # Using os.startfile on Windows ensures native default launcher handles the execution loop
            if os.name == 'nt':
                os.startfile(full_pdf_path)
            else:
                # Fallback multi-platform command array line context execution
                subprocess.Popen(['xdg-open' if os.name == 'posix' else 'open', full_pdf_path])
                
        except Exception as open_err:
            messagebox.showerror("Execution Error", f"Failed to open PDF document natively:\n{open_err}")

if __name__ == "__main__":
    root_window = tk.Tk()
    root_window.geometry("800x550")
    app = SmartSearchApp(root_window)
    root_window.mainloop()