import csv
import os
import re
from pypdf import PdfReader

# configuration
pdf_path = f"C:\\Users\\ed2832\\Downloads\\MOECSO\\WarResearches.pdf"

def extract_pdf_words_to_csv(pdf_path):
    """
        Reads local PDF file, extract all words and save them 
        into csv file (each word in a cell)
    """
    # path validity
    if not os.path.exists(pdf_path):
        print(f"Error: file '{pdf_path}' does not exists.")
        return
    
    csv_path = f"C:\\Users\\ed2832\\Downloads\\MOECSO\\pdf_to_csv.csv"

    try:
        reader = PdfReader(pdf_path)

        # open CSV file with UTF 8 encoding for hebrew
        with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Word", "Page_Number"]) # headers
            total_words = 0

            # iterate through each PDF pages
            for page_index, page in enumerate(reader.pages):
                page_text = page.extract_text()

                if page_text:
                    # Using Regex to find all distinct words (alphanumeric sequences)
                    words = re.findall(r'[a-zA-Zא-ת]+', page_text, flags=re.UNICODE)

                    # Write each individual word to the spreadsheet
                    for word in words:
                        # page_index is 0-based, we add 1 for human-readable page numbering
                        writer.writerow([word, page_index + 1])
                        total_words += 1

        print(f"Success! Processed {len(reader.pages)} pages.")
        print(f"Extracted {total_words} words into: '{csv_path}'")

    except Exception as e:
            print(f"An eerror occured durng execution: {e}")

if __name__ == "__main__":
    extract_pdf_words_to_csv(pdf_path)