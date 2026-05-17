import os
import time
import threading
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# --- CONFIGURATION ---
# Path to your master matrix Excel sheet where each column is a PDF file
MATRIX_EXCEL_PATH = r"C:\Users\ed2832\Downloads\MOECSO\koogle\clean data\cleaned_pdf_words_columns.xlsx"
LOGO_IMAGE_NAME = r"C:\Users\ed2832\Downloads\MOECSO\koogle\koogle logo.png"  # Make sure this file is in the same directory as the script

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
        Creates a borderless modern splash window displaying the Koogle logo 
        resized dynamically to fit within the designated dimensions.
        """
        self.splash = tk.Toplevel()
        self.splash.title("Koogle - Loading")
        self.splash.overrideredirect(True)  # Strips standard window borders
        
        # Center the splash panel cleanly on the user's desktop display
        splash_width = 500
        splash_height = 380
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (splash_width / 2))
        y_coordinate = int((screen_height / 2) - (splash_height / 2))
        self.splash.geometry(f"{splash_width}x{splash_height}+{x_coordinate}+{y_coordinate}")
        self.splash.configure(bg="#ffffff")  # Clean white backdrop

        # Canvas block containing the logo asset image
        logo_path = os.path.join(os.path.dirname(__file__) if __file__ else "", LOGO_IMAGE_NAME)
        if os.path.exists(logo_path):
            try:
                # Open image using Pillow
                pil_image = Image.open(logo_path)
                
                # Dynamic scaling: Resize image proportionally to fit nicely inside the splash window
                # Target width of 350px, calculate height maintaining aspect ratio
                target_width = 350
                w_percent = target_width / float(pil_image.size[0])
                target_height = int(float(pil_image.size[1]) * float(w_percent))
                
                # Apply high-quality antialiasing filter during resize operation
                resized_pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Convert Pillow image to a Tkinter compatible PhotoImage object
                self.logo_img = ImageTk.PhotoImage(resized_pil_image)
                
                logo_label = tk.Label(self.splash, image=self.logo_img, bg="#ffffff")
                logo_label.pack(pady=(40, 10))
            except Exception as img_err:
                # Fallback if image rendering fails
                print(f"Image resize error: {img_err}")
                tk.Label(self.splash, text="KOOGLE", font=("Segoe UI", 36, "bold"), fg="#4285F4", bg="#ffffff").pack(pady=(60, 20))
        else:
            tk.Label(self.splash, text="KOOGLE", font=("Segoe UI", 36, "bold"), fg="#4285F4", bg="#ffffff").pack(pady=(60, 20))

        # Status subtitle tracking phase actions
        self.loading_label = tk.Label(self.splash, text="Initializing Koogle Database Engine... 0%", font=("Segoe UI", 10), fg="#5f6368", bg="#ffffff")
        self.loading_label.pack(pady=(15, 5))

        # Modern Progress Bar layout component
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Koogle.Horizontal.TProgressbar", thickness=10, troughcolor="#f1f3f4", background="#4285F4")
        
        self.progress_bar = ttk.Progressbar(self.splash, style="Koogle.Horizontal.TProgressbar", orient="horizontal", length=350, mode="determinate")
        self.progress_bar.pack(pady=5)

        # Trigger background worker thread to read dataset rows without freezing GUI loops
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
            self.root.after(0, self.update_splash_progress, 40, "Opening Excel binary matrix stream arrays...")
            
            loaded_df = pd.read_excel(MATRIX_EXCEL_PATH)
            
            time.sleep(0.5)
            self.root.after(0, self.update_splash_progress, 75, f"Indexing column vectors for {len(loaded_df.columns)} documents...")
            
            self.df = loaded_df
            time.sleep(0.5)
            self.root.after(0, self.update_splash_progress, 100, "System database array verification complete!")
            time.sleep(0.4)
            
            self.root.after(0, self.launch_main_application)
            
        except Exception as err:
            self.root.after(0, self.handle_boot_failure, f"An unexpected fatal system mapping array event occurred:\n{err}")

    def handle_boot_failure(self, message):
        messagebox.showerror("Fatal Initialization Error", message)
        if hasattr(self, 'splash'):
            self.splash.destroy()
        self.root.destroy()

    def launch_main_application(self):
        self.splash.destroy()  # Close loading window completely
        
        self.root.deiconify()  # Reveal main search console
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
        
        self.status_label = ttk.Label(self.root, text=f"Ready. Monitoring query keys over {len(self.df.columns)} cached document blocks.", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

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
            
        self.status_label.config(text=f"Evaluating matrix intersections for targets: {', '.join(target_keywords)}...")
        self.root.update_idletasks()
        
        search_results = []
        
        for column_name in self.df.columns:
            column_series = self.df[column_name].dropna().astype(str).str.strip().str.lower()
            
            total_file_hits = 0
            for keyword in target_keywords:
                total_file_hits += (column_series == keyword).sum()
                
            if total_file_hits > 0:
                search_results.append({
                    "filename": column_name,
                    "score": total_file_hits
                })
                
        sorted_results = sorted(search_results, key=lambda x: x["score"], reverse=True)
        
        if not sorted_results:
            self.status_label.config(text="Zero matching elements traced in indexed layout structures.")
            messagebox.showinfo("Zero Matches", "Specified keys yield no indexed matrix matches.")
            return
            
        for rank_index, item in enumerate(sorted_results):
            row_data = (rank_index + 1, item["filename"], f"{item['score']:,} times")
            self.results_table.insert("", tk.END, values=row_data)
            
        self.status_label.config(text=f"Search completed. Found {len(sorted_results)} matching documents ordered by aggregate relevance score.")

if __name__ == "__main__":
    root_window = tk.Tk()
    root_window.geometry("800x550")
    app = SmartSearchApp(root_window)
    root_window.mainloop()