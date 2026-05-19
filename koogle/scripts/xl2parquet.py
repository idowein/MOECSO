import pandas as pd
import os

# The heavy cleaned Excel file path from your code
excel_path = r"C:\Users\idowe\MyProjects\MOECSO\koogle\clean data\cleaned_pdf_words_columns.xlsx"
# The new fast Parquet file path destination
parquet_path = r"C:\Users\idowe\MyProjects\MOECSO\koogle\clean data\cleaned_pdf_words_columns.parquet"

print("Loading the cleaned Excel file into memory... (this might take a minute, please wait)")

if not os.path.exists(excel_path):
    print(f"Error: Could not find the Excel file at {excel_path}")
else:
    # Read the heavy excel
    df = pd.read_excel(excel_path)
    print("Excel loaded successfully! Converting to fast Parquet format...")
    
    # Save as Parquet
    df.to_parquet(parquet_path, index=False)
    print("=" * 50)
    print(f"SUCCESS! Fast database file created at:\n{parquet_path}")
    print("=" * 50)