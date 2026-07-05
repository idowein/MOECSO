import pandas as pd
import os
from pypdf import PdfReader
import re
from tqdm import tqdm

input_index_file = r"C:\Users\ed2832\Downloads\MOECSO\MONET\v1\raw data\filenames_paths.xlsx"
output_corpus_file = r"C:\Users\ed2832\Downloads\MOECSO\MONET\v1\raw data\corpus.xlsx"
data_rows = []

def pdf_parsing(input_path, data_rows):
    """
    Reads a local PDF file, extracts words while ignoring numbers,
    and saves the output in dictionary
    """

    # check if pdf exist
    if not os.path.exists(input_path):
        tqdm.write(f"Error: {input_path} does not exist.")
        return

    basename = os.path.basename(input_path)

    try:
        reader = PdfReader(input_path)

        for page_index, page in enumerate(reader.pages):
            page_text = page.extract_text()

            if page_text:
                # Regular Expression to match only Hebrew and English letters, completely skipping numbers
                # The re.UNICODE flag ensures Hebrew characters are processed properly
                words = re.findall(r'[a-zA-Zא-ת]+', page_text, flags=re.UNICODE)

                for word in words:
                    data_rows.append({
                                    "file name":basename,
                                    "word": word, 
                                    "path": input_path
                                    }) 

    except Exception as e:
        tqdm.write(f"An error occurred during execution on {basename}: {e}")                    
    return data_rows

def xl_creation(data_rows, xl_path):
        df = pd.DataFrame(data_rows)
        # Export the DataFrame directly into a native Excel file
        # index=False prevents Pandas from adding an extra unnamed column for row numbers
        df.to_excel(xl_path, index=False)

        #print(f"Success! Total parsed pages: {len(reader.pages)}")
        print(f"Extracted {len(df)} words directly into Excel: '{xl_path}'")

if __name__ == "__main__":
        global_data_rows = []

        if os.path.exists(input_index_file):
            df_index = pd.read_excel(input_index_file)
            print(f"Loaded index file. Found {len(df_index)} files to process.\n" + "-"*50)
    
            for index, row in tqdm(df_index.iterrows(), total=len(df_index), desc="Processing PDFs"): # iterating the xl file row by row
                pdf_path = row['path'] 
                
                if pd.isna(pdf_path):  # skipping columns that is not pdf paths
                    continue
                    
                global_data_rows = pdf_parsing(pdf_path, global_data_rows)
                print("-" * 30)

            xl_creation(global_data_rows, output_corpus_file)
            
        else:
            print(f"Error: The input index file does not exist at {input_index_file}")