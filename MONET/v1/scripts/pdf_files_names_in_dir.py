from pathlib import Path 

folder_path = Path("Z:\DATA\מדען ראשי")
pdf_number = 0

for path in folder_path.rglob("*.pdf"):
    print(path.name)
    pdf_number += 1

print(f"The number of the pdf files is: {pdf_number}")