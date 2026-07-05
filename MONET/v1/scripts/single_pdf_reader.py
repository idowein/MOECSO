import os
import re
import pandas as pd
from pypdf import PdfReader

input_path = r"Z:\DATA\מדען ראשי\קולות קוראים 2026\חוסרי מורי STEM\קול קורא\הקול קורא למחקר - הון אנושי בתחומי ה  STEM במערכת החינוך.pdf"

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

if __name__ == "__main__":
    extract_pdf_words_to_xl(input_path)

