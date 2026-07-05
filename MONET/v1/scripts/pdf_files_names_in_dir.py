from pathlib import Path 
import pandas as pd
import os

folder_path = Path("Z:\DATA\מדען ראשי")
xl_path = r"C:\Users\ed2832\Downloads\MOECSO\MONET\v1\raw data\filenames_paths.xlsx"
pdf_number = 0
data_rows = []

for path in folder_path.rglob("*.pdf"):
    basename = os.path.basename(path)
    print(basename)
    pdf_number += 1
    data_rows.append({
        "file name": basename,
        "path": path
    })


df = pd.DataFrame(data_rows)
# Export the DataFrame directly into a native Excel file
# index=False prevents Pandas from adding an extra unnamed column for row numbers
df.to_excel(xl_path, index=False)

print(f"The number of the pdf files is: {pdf_number}")