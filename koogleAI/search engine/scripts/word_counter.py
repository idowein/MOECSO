import os
import pandas as pd
from collections import Counter

# --- CONFIGURATION ---
# Path to the large master excel file containing columns for each PDF
MASTER_EXCEL_PATH = r"C:\Users\ed2832\Downloads\MOECSO\koogle\pdf_words_columns.xlsx"

def export_complete_word_frequency(file_path):
    """
    Reads the large columns-based Excel sheet, aggregates the frequency 
    of every single word across all documents, and exports the full 
    sorted analysis into a brand new, clean Excel spreadsheet.
    """
    # Verify that the master dataset exists before attempting to process
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' was not found. Please ensure the extraction process finished successfully.")
        return

    print("Loading master excel dataset and flattening all columns into memory...")
    # Read the large Excel sheet where each column represents a single PDF file
    df = pd.read_excel(file_path)
    
    # Initialize a master list to hold all words combined
    all_words = []
    
    # Iterate through each column to safely collect words
    for column in df.columns:
        # dropna() removes empty cells (NaN) introduced by unequal file lengths
        column_words = df[column].dropna().tolist()
        all_words.extend(column_words)

    if not all_words:
        print("Process halted: No valid words were found in the master spreadsheet columns.")
        return

    print(f"Total words gathered from all documents combined: {len(all_words):,}")
    print("Calculating frequencies and counting occurrences...")
    
    # Count the frequency of every single unique word in the entire dataset
    word_counts = Counter(all_words)
    
    # Extract ALL word counts sorted in descending order (highest frequency first)
    # Passing no arguments to most_common() extracts the entire vocabulary
    all_most_common = word_counts.most_common()

    # Structure the raw summary data list into dictionary rows for Pandas mapping
    structured_rows = []
    for word, count in all_most_common:
        structured_rows.append({
            "Word": word,
            "Total_Count": count
        })

    # Convert the structured data into a fresh clean DataFrame
    summary_df = pd.DataFrame(structured_rows)

    # Define the final export destination path in the same directory
    output_dir = os.path.dirname(file_path)
    output_excel_path = os.path.join(output_dir, "word_number.xlsx")

    print(f"Compiling dataset structure with {len(summary_df):,} unique words...")
    
    # Export the final calculated matrix into a native Excel sheet
    # index=False prevents Pandas from adding an extra row-number identifier column
    summary_df.to_excel(output_excel_path, index=False)
    
    print(f"Success! The complete word frequency ledger has been created successfully.")
    print(f"Output File Saved to: '{output_excel_path}'")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    export_complete_word_frequency(MASTER_EXCEL_PATH)