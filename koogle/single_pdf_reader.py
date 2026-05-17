import os
import re
import pandas as pd
from pypdf import PdfReader

# --- CONFIGURATION ---
# Define the input path for the target PDF file
INPUT_PDF_PATH = f"C:\\Users\\ed2832\\Downloads\\MOECSO\\WarResearches.pdf"

def extract_pdf_words_to_excel(pdf_path):
    """
    Reads a local PDF file, extracts words while ignoring numbers,
    and saves the output directly as an Excel (.xlsx) file to prevent encoding issues.
    """
    # Check if the target PDF file exists before starting the execution
    if not os.path.exists(pdf_path):
        print(f"Error: The file at '{pdf_path}' does not exist. Please check the path.")
        return

    # Extract the base file name to print it nicely in the terminal
    pure_file_name = os.path.basename(pdf_path)
    print(f"--- Starting process for file: {pure_file_name} ---")

    # Generate the output Excel path dynamically in the same directory as the PDF
    base_path, _ = os.path.splitext(pdf_path)
    excel_path = base_path + "_extracted_words.xlsx"

    try:
        print(f"Opening and parsing '{pdf_path}'...")
        reader = PdfReader(pdf_path)
        
        # Initialize an empty list to store dictionary rows before converting to a DataFrame
        data_rows = []
        
        # Iterate through all available pages in the PDF document
        for page_index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            
            if page_text:
                # Regular Expression to match only Hebrew and English letters, completely skipping numbers
                # The re.UNICODE flag ensures Hebrew characters are processed properly
                words = re.findall(r'[a-zA-Zא-ת]+', page_text, flags=re.UNICODE)
                
                # Append each extracted word and its corresponding page number to the dataset
                for word in words:
                    # Page numbers are converted from 0-based index to 1-based index for readability
                    data_rows.append({
                        pure_file_name: word, 
                    })
        
        # Convert the collected list of rows into a structured Pandas DataFrame
        df = pd.DataFrame(data_rows)
        
        # Export the DataFrame directly into a native Excel file
        # index=False prevents Pandas from adding an extra unnamed column for row numbers
        df.to_excel(excel_path, index=False)
        
        print(f"Success! Total parsed pages: {len(reader.pages)}")
        print(f"Extracted {len(df)} words directly into Excel: '{excel_path}'")
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Execute the core extraction function using the configured path
    extract_pdf_words_to_excel(INPUT_PDF_PATH)