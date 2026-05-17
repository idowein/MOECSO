import os
import re
import pandas as pd
from pypdf import PdfReader

def extract_single_pdf_to_word_list(pdf_path):
    """
    Core module: Reads a single PDF file, extracts words (ignoring numbers),
    and returns a flat list of all extracted words found in the document.
    """
    word_list = []
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                # Extract Hebrew and English letters, skipping standalone numbers
                words = re.findall(r'[א-ת]+', page_text, flags=re.UNICODE)
                for word in words:
                    word_list.append(word)
    except Exception as e:
        print(f"Failed to parse text from {os.path.basename(pdf_path)}: {e}")
    
    return word_list

def process_pdfs_as_columns(directory_path):
    """
    Scans the target directory for PDF files, extracts words from each file,
    and maps each PDF file as a single column in a master unified Excel sheet.
    """
    # Check if the provided directory path actually exists
    if not os.path.exists(directory_path):
        print(f"Error: The directory '{directory_path}' does not exist.")
        return

    # List all items in the directory and filter for files ending with .pdf
    files = os.listdir(directory_path)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in the directory: '{directory_path}'")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process.\n")

    # Master dictionary to hold data where key = PDF_Name and value = [List of words]
    columns_data = {}

    # Loop through each discovered PDF file
    for pdf_file in pdf_files:
        full_pdf_path = os.path.join(directory_path, pdf_file)
        print(f"Extracting words for column: {pdf_file}...")

        # Extract only the word list from the current PDF
        file_words = extract_single_pdf_to_word_list(full_pdf_path)
        
        # Assign the list to the dictionary under the unique file name key
        if file_words:
            columns_data[pdf_file] = file_words
            print(f"Collected {len(file_words)} words for this column.\n")
        else:
            print(f"Skipped {pdf_file} (No text or words extracted).\n")

    # Export to Excel only if data was collected
    if columns_data:
        output_excel_path = os.path.join(directory_path, "pdf_words_columns.xlsx")
        print(f"\nBuilding dynamic column structure...")
        
        # orient='index' creates the initial structure from uneven lists
        # Transpose (.T) flips it so keys become horizontal columns instead of vertical rows
        df = pd.DataFrame.from_dict(columns_data, orient='index').T
        
        # Export the final side-by-side columns dataframe to Excel
        df.to_excel(output_excel_path, index=False)
        print(f"Success! Master file created at: '{output_excel_path}'")
    else:
        print("\nProcess finished with no words extracted. Excel file was not created.")

    print("--- Column-based batch processing complete! ---")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Your target system directory
    TARGET_DIRECTORY = r"C:\\Users\\ed2832\\Downloads\\MOECSO"
    
    # Run the column-based batch processor
    process_pdfs_as_columns(TARGET_DIRECTORY)