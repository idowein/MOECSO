import pandas as pd
import os
from pypdf import PdfReader
import re
from tqdm import tqdm

input_index_file = r"C:\Users\ed2832\Downloads\MOECSO\MONET\v1\raw data\filenames_paths.xlsx"
output_corpus_file = r"C:\Users\ed2832\Downloads\MOECSO\MONET\v1\raw data\corpus.csv"
data_rows = []

def pdf_parsing(input_path, data_rows):
    """
    Reads a local PDF file, extracts words while ignoring numbers.
    If the file is scanned (no text extracted) or contains no words, skips it gracefully.
    """
    # Verify if the file actually exists on the path
    if not os.path.exists(input_path):
        tqdm.write(f"Error: {input_path} does not exist.")
        return data_rows

    basename = os.path.basename(input_path)
    file_has_words = False  # Flag to track if any valid words were found in the current PDF
    temp_rows = []          # Temporary list to store rows for the current file only

    try:
        reader = PdfReader(input_path)

        # Loop through all pages using enumerate to track the page index
        for page_index, page in enumerate(reader.pages):
            page_text = page.extract_text()

            # Process the page only if it contains digital text (not empty or just whitespace)
            if page_text and page_text.strip():
                # Extract only Hebrew and English letters, completely skipping numbers
                words = re.findall(r'[a-zA-Zא-ת]+', page_text, flags=re.UNICODE)

                for word in words:
                    temp_rows.append({
                        "file name": basename,
                        "word": word, 
                        "path": input_path
                    })
                    file_has_words = True

        # If the loop finished and no words were found, it means the PDF is scanned or empty
        if not file_has_words:
            tqdm.write(f"Skipping scanned or empty PDF: {basename}")
        else:
            # Append the temporary rows to the master list only if the file contains valid text
            data_rows.extend(temp_rows)

    except Exception as e:
        tqdm.write(f"An error occurred during execution on {basename}: {e}")
    
    return data_rows

def csv_creation(data_rows, csv_path):
    if not data_rows:
            print("No data rows to save.")
            return

    df = pd.DataFrame(data_rows)
        
    # Export to CSV. utf-8-sig ensures Hebrew characters display correctly when opened in Excel later.
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\nSuccess! Extracted {len(df)} total words directly into CSV: '{csv_path}'")

if __name__ == "__main__":
        global_data_rows = []

        if os.path.exists(input_index_file):
            df_index = pd.read_excel(input_index_file)
            print(f"Loaded index file. Found {len(df_index)} files to process.\n" + "-"*50)
    
#            for index, row in tqdm(df_index.iterrows(), total=len(df_index), desc="Processing PDFs"): # iterating the xl file row by row
#                pdf_path = row['path'] 

            for index, row in tqdm(df_index.iterrows(), total=len(df_index), desc="Processing PDFs"):
                pdf_path = row['path']
                
                tqdm.write(f"DEBUG: Row {index}, Path read from excel is: {pdf_path}")
                
                if pd.isna(pdf_path):  # skipping columns that is not pdf paths
                    continue
                    
                global_data_rows = pdf_parsing(pdf_path, global_data_rows)
                print("-" * 30)

            csv_creation(global_data_rows, output_corpus_file)
            
        else:
            print(f"Error: The input index file does not exist at {input_index_file}")