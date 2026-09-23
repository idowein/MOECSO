import os
import re
import pandas as pd
from pypdf import PdfReader

input_path = r"Z:\DATA\מדען ראשי\קולות קוראים 2026\חוסרי מורי STEM\קול קורא\הקול קורא למחקר - הון אנושי בתחומי ה  STEM במערכת החינוך.pdf"
xl_path = r"C:\Users\ed2832\Downloads\MOECSO\MONET\v1\raw data\corpus.xlsx"

def extract_pdf_words_to_xl(input_path):
    """
    Reads a local PDF file, extracts words while ignoring numbers,
    and saves the output directly as an Excel (.xlsx) file to prevent encoding issues.
    """

    # check if pdf exist
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist.")
        return

    basename = os.path.basename(input_path)
    print(f"Start to process {basename}")

    try:
        reader = PdfReader(input_path)
        data_rows = []

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

        df = pd.DataFrame(data_rows)
        # Export the DataFrame directly into a native Excel file
        # index=False prevents Pandas from adding an extra unnamed column for row numbers
        df.to_excel(xl_path, index=False)

        print(f"Success! Total parsed pages: {len(reader.pages)}")
        print(f"Extracted {len(df)} words directly into Excel: '{xl_path}'")
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    extract_pdf_words_to_xl(input_path)

