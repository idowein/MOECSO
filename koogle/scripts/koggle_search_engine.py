import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

# --- CONFIGURATION ---
# Path to your master matrix Excel sheet where each column is a PDF file
MATRIX_EXCEL_PATH = r"C:\Users\ed2832\Downloads\MOECSO\koogle\clean data\cleaned_pdf_words_columns.xlsx"

class KeywordSearchEngine:
    def __init__(self, root, excel_path):
        self.root = root
        self.excel_path = excel_path
        
        # Configure main window properties
        self.root.title("MOECSO - KOOGLE")
        self.root.geometry("800x550")
        
        # Load the dataset into memory
        self.load_dataset()
        
        # Build the graphical interface layout
        self.create_widgets()

    def load_dataset(self):
        """
        Loads the main master Excel matrix where columns represent PDF documents.
        """
        if not os.path.exists(self.excel_path):
            messagebox.showerror("Error", f"Master database file not found at:\n{self.excel_path}")
            self.root.destroy()
            return
        try:
            print("Loading matrix Excel rows into runtime memory...")
            self.df = pd.read_excel(self.excel_path)
            print(f"Successfully indexed {len(self.df.columns)} active documents.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load Excel matrix ledger:\n{e}")
            self.root.destroy()

    def create_widgets(self):
        """
        Creates and positions window panel widgets.
        """
        # Top input panel frame configuration
        search_frame = ttk.Frame(self.root, padding=15)
        search_frame.pack(fill=tk.X)
        
        label = ttk.Label(search_frame, text="Enter Keywords (separated by space):", font=("Segoe UI", 11))
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = ttk.Entry(search_frame, font=("Segoe UI", 11), width=45)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.execute_keyword_search())
        
        self.search_button = ttk.Button(search_frame, text="Count Keywords", command=self.execute_keyword_search)
        self.search_button.pack(side=tk.LEFT)
        
        # Center spreadsheet layout grid view (Treeview)
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
        
        # Bottom window layout information status bar
        self.status_label = ttk.Label(self.root, text=f"Ready. Listening for keywords across {len(self.df.columns)} documents.", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def execute_keyword_search(self):
        """
        Tokenizes the raw user entry directly into a query dictionary, 
        sums up matches per column vector, and sorts documents by absolute weight.
        """
        # Clear existing rows inside the layout view grid
        for row in self.results_table.get_children():
            self.results_table.delete(row)
            
        raw_input = self.search_entry.get().strip()
        if not raw_input:
            self.status_label.config(text="Warning: Keyword input field is empty.")
            return
            
        # Step 1: Parse input text directly into separate clean keyword tokens
        # No stop-word validation or pruning is triggered here
        target_keywords = [w.strip().lower() for w in raw_input.split() if w.strip()]
        
        if not target_keywords:
            return
            
        print(f"User search dictionary list generated: {target_keywords}")
        self.status_label.config(text=f"Calculating distribution matrix for: {', '.join(target_keywords)}...")
        self.root.update_idletasks()
        
        search_results = []
        
        # Step 2: Loop through each file column to evaluate absolute keyword counts
        for column_name in self.df.columns:
            # Flatten column cells into clean lowercase strings
            column_series = self.df[column_name].dropna().astype(str).str.strip().str.lower()
            
            # Count the occurrences of each word from the user dictionary list
            total_file_hits = 0
            for keyword in target_keywords:
                total_file_hits += (column_series == keyword).sum()
                
            # If the keywords appear at least once, register the document metrics
            if total_file_hits > 0:
                search_results.append({
                    "filename": column_name,
                    "score": total_file_hits
                })
                
        # Step 3: Sort the matching files database registry in descending order (highest hits first)
        sorted_results = sorted(search_results, key=lambda x: x["score"], reverse=True)
        
        if not sorted_results:
            self.status_label.config(text="Query executed. Zero matching items uncovered.")
            messagebox.showinfo("Zero Matches", "The specified keywords do not exist inside any indexed PDF documents.")
            return
            
        # Step 4: Map sorted arrays directly onto graphical tree grid row blocks
        for rank_index, item in enumerate(sorted_results):
            row_data = (rank_index + 1, item["filename"], f"{item['score']:,} times")
            self.results_table.insert("", tk.END, values=row_data)
            
        self.status_label.config(text=f"Search finalized. Found {len(sorted_results)} matching documents ordered by aggregate frequency.")

if __name__ == "__main__":
    root_window = tk.Tk()
    app = KeywordSearchEngine(root_window, MATRIX_EXCEL_PATH)
    root_window.mainloop()