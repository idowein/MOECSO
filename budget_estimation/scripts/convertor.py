import os
import win32com.client
import pandas as pd

def convert_word_to_pdf(doc_path, pdf_path, word_app):
    """ממיר קובץ Word לקובץ PDF"""
    try:
        # פתיחת המסמך והמרתו (8 = פורמט PDF ב-COM API של Word)
        doc = word_app.Documents.Open(doc_path)
        doc.SaveAs(pdf_path, FileFormat=17)
        doc.Close()
        print(f"[✓] הומר ל-PDF: {pdf_path}")
    except Exception as e:
        print(f"[X] שגיאה בהמרת Word {doc_path}: {e}")

def convert_excel_to_csv(excel_path, csv_path):
    """ממיר את הגיליון הראשון של קובץ Excel לקובץ CSV"""
    try:
        # טעינת קובץ האקסל ושמירתו כ-CSV עם תמיכה בעברית
        df = pd.read_excel(excel_path, sheet_name=0)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"[✓] הומר ל-CSV: {csv_path}")
    except Exception as e:
        print(f"[X] שגיאה בהמרת Excel {excel_path}: {e}")

def process_directory(base_path):
    """עובר על כל הספריות והתתי-ספריות ומבצע המרות"""
    # אתחול אפליקציית Word ברקע
    word_app = win32com.client.Dispatch("Word.Application")
    word_app.Visible = False

    try:
        for root, dirs, files in os.walk(base_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # התעלמות מקבצי זבל/זמניים של אופיס שמתחילים ב-~$
                if file.startswith("~$"):
                    continue

                file_lower = file.lower()

                # המרת Word ל-PDF
                if file_lower.endswith(('.docx', '.doc')):
                    pdf_filename = os.path.splitext(file)[0] + ".pdf"
                    pdf_path = os.path.join(root, pdf_filename)
                    
                    # ביצוע המרה רק אם קובץ ה-PDF עדיין לא קיים
                    if not os.path.exists(pdf_path):
                        convert_word_to_pdf(file_path, pdf_path, word_app)

                # המרת Excel ל-CSV
                elif file_lower.endswith(('.xlsx', '.xls')):
                    csv_filename = os.path.splitext(file)[0] + ".csv"
                    csv_path = os.path.join(root, csv_filename)
                    
                    # ביצוע המרה רק אם קובץ ה-CSV עדיין לא קיים
                    if not os.path.exists(csv_path):
                        convert_excel_to_csv(file_path, csv_path)

    finally:
        # סגירה בטוחה של אפליקציית Word
        word_app.Quit()

if __name__ == "__main__":
    # נתיב הספריה הראשית המכילה את תתי-הספריות של "משולשי הזהב"
    TARGET_PATH = r"\\fsmateh\SYS_adlevram\DATA\מדען ראשי\מערכת שערוך תקציב מחקר לקולות קוראים\raw data\משולשי זהב"

    print("מתחיל בתהליך ההמרה...")
    process_directory(TARGET_PATH)
    print("\nהתהליך הסתיים בהצלחה!")