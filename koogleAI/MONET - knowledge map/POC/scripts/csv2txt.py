import csv

# --- CONFIGURATION ---
# Input paths (Your existing CSV files)
CSV_MAP_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\raw data\map.csv"
CSV_NETWORK_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\raw data\network.csv"

# Output paths (The new TXT files for VOSviewer)
TXT_MAP_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\raw data\map.txt"
TXT_NETWORK_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\raw data\network.txt"

def convert_csv_to_vos_txt(csv_path, txt_path, has_utf8_sig=False):
    """
    Reads an existing CSV file and rewrites it as a Tab-Separated TXT file.
    """
    # Select encoding based on whether it needs the BOM header for Hebrew
    encoding_type = 'utf-8-sig' if has_utf8_sig else 'utf-8'
    
    try:
        with open(csv_path, 'r', encoding=encoding_type) as f_in:
            reader = csv.reader(f_in)
            rows = list(reader)
            
        with open(txt_path, 'w', newline='', encoding=encoding_type) as f_out:
            # Using delimiter='\t' to create Tab-Separated Values (TSV)
            writer = csv.writer(f_out, delimiter='\t')
            writer.writerows(rows)
            
        print(f"Successfully converted:\n -> {csv_path}\n -> {txt_path}\n")
    except Exception as e:
        print(f"Error converting {csv_path}: {e}")

if __name__ == "__main__":
    print("Starting conversion process without scraping...")
    
    # Convert Map file (needs utf-8-sig for Hebrew characters)
    convert_csv_to_vos_txt(CSV_MAP_PATH, TXT_MAP_PATH, has_utf8_sig=True)
    
    # Convert Network file (standard utf-8)
    convert_csv_to_vos_txt(CSV_NETWORK_PATH, TXT_NETWORK_PATH, has_utf8_sig=False)
    
    print("🏆 Done! You can now load the .txt files into VOSviewer.")