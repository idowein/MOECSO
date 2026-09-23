import os
import pandas as pd

# --- CONFIGURATION ---
MASTER_EXCEL_PATH = r"C:\Users\ed2832\Downloads\MOECSO\koogle\pdf_words_columns.xlsx"

# Use the exact comprehensive stop words set from our previous configuration
BASE_STOP_WORDS = {
    # --- Layer 1: Prepositions & Locatives ---
    "עד", "בתוך", "לצד", "בכלל", "בקרב", "לבין", "לגבי", "במהלך", "מול", "נגד", "אצל", "בגלל", 
    "למען", "אודות", "בכדי", "דרך", "לעומת", "מכיוון", "משום", "כיוון", "לכן", "בין", "כדי", 
    "ללא", "בלי", "לפי", "עבור", "אשר", "להלן", "במסגרת", "על-ידי", "עלידי", "באמצעות", 
    "כגון", "בעקבות", "לאור", "בסעיף", "לעיל", "לאחר", "בישראל", "מחוץ", "מלבד", "לשם",
    "מאז", "לעבר", "סביב", "עקב", "בשל", "בתור", "אגב", "ככל", "כפי", "תחת", "מעל", "מתחת",
    "עד", "ככל", "כל", "כך", "כמו", "ידי", "כאשר", "מתוך", "תוך", "כדי", "אז", "אף", "למרות", 
    "לכך", "בעוד", "עוד", "נוגע", "בנוגע", "בלבד", "כאילו", "עת", "בעת", "לפני", "אחרי", "אבל", 
    "אין", "יש", "כיצד", "לא", "כן", 

    # --- Layer 2: Complete Inflected Hebrew Pronouns & Preposition Families ---
    "לי", "לך", "לו", "לה", "לנו", "לכם", "לכן", "להם", "להן", "לכל", "לתלמידים", "למורים", "להוראה", "ללמידה",
    "בי", "בך", "בו", "בה", "בנו", "בכם", "בכן", "בהם", "בהן", "שבו", "שבה", "שבהם", "שבהן", "בבית", "בבתי", 
    "בכיתה", "בתוכו", "בתוכה", "בכל", "במידה", "במחקר", "בחינוך", "בהוראה", "בשלב", "באופן", "במצב",
    "את", "אותי", "אותך", "אותו", "אותה", "אותנו", "אתכם", "אתכן", "אותם", "אותן", "של", "שלו", "שלה", 
    "שלנו", "שלכם", "שלכן", "שלהם", "שלהן", "על", "מה", "עם", "או", "גם", "משלה", "משלו", "משלהם", "משלהן",
    "איתי", "איתך", "איתו", "איתה", "איתנו", "איתכם", "איתכן", "איתם", "איתן", "עימי", "עימו", "עימה", "עימם", "עימן",
    "עליי", "עליך", "עליו", "עליה", "עלינו", "עליכם", "עליכן", "עליהם", "עליהן", "מעליי", "מעליו", "מעליה",
    "ממני", "ממך", "ממנו", "ממנה", "מאיתנו", "מכם", "מכן", "מהם", "מהן", "מכך",
    "אני", "אתה", "את", "הוא", "היא", "אנחנו", "אתם", "אתן", "הם", "הן", "עצמו", "עצמה", "עצמם", "עצמן",
    "זה", "זו", "זאת", "אלו", "אלה", "הללו", "ההוא", "ההיא", "הנך", "הנני", "הנם",

    # --- Layer 3: Auxiliary Verbs & Existential Particles ---
    "יש", "היה", "היו", "להיות", "ניתן", "נמצא", "הייתה", "יוכל", "נוסף", "נוספים", "נוספות", "אכן", 
    "אינו", "אינה", "אינם", "אינן", "הינו", "הינה", "הנם", "הנן", "שהם", "וכן", "האם", "אך", "ולא", 
    "אלא", "יכול", "שיש", "שלי", "ואת", "נתון", "היווה", "מהווה", "מהווים", "מהוות", "נעשה", "נעשתה",
    "נעשים", "הפך", "הפכה", "הופך", "נמצאו", "נמצאה", "קיימים", "קיים", "קיימת", "קיימות", "אפשר", "אפשרות",

    # --- Layer 4: Quantitative, Comparative & Meta-Adverbs ---
    "אחד", "אחת", "שונים", "שונות", "גבוהה", "גבוה", "נמוך", "רבים", "רבות", "רב", "מעט", "מספר", 
    "כמה", "חלקם", "רוב", "מרבית", "מלא", "קל", "קשה", "חדש", "חדשה", "ישן", "אחר", "אחרת", "אחרים", 
    "אחרות", "דווקא", "במיוחד", "שוב", "תמיד", "לעיתים", "קרובות", "יחד", "לבד", "כמעט", "כאן", "שם", 
    "רק", "עוד", "כבר", "לא", "כן", "כי", "אם", "אל", "כלשהי", "כלשהו", "כלשהם", "איזה", "איזו", 
    "בסך", "סך", "כלל", "חלק", "שאר", "מנת", "מעטות", "מרובים", "נמוכה", "קודם", "קודמת", "הבא", "הבאה",
    "הבאים", "הבאות", "לעיל", "להלן", "בינתיים", "לאחרונה", "לשעבר", "למדי", "מאוד", "פחות", "יותר",

    # --- Layer 5: Administrative & Academic Structure Words ---
    "מידע", "נתונים", "ממצאים", "תוצאות", "מחקר", "המחקר", "מחקרים", "במחקר", "משרד", "פרק", "עמוד", 
    "טבלה", "גרף", "נספח", "דוח", "סיכום", "מבוא", "הערכה", "תוכנית", "תכנית", "התוכנית", "תוכניות", 
    "פרויקט", "ישראל", "הלשכה", "המדען", "הראשי", "הגשה", "תאריך", "גרסה", "פרסום", "כתיבה", 
    "עריכה", "צוות", "חוקרים", "חוקר", "שנה", "שנים", "יום", "ימים", "חודש", "חודשים", "זמן", 
    "תקופה", "מועד", "כמות", "מדד", "אחוז", "אחוזים", "רמה", "שיעור", "דרגה", "היקף", "ערך", 
    "פריט", "שימוש", "ידע", "הידע", "השימוש", "ניתוח", "פעילות", "קבוצות", "העבודה", "עבודה", 
    "קשר", "הקשר", "מודל", "לימוד", "הלימודים", "חשיבה", "בעיות", "בנושא", "שאלות", "משבר", 
    "תהליך", "לוח", "פריטים", "מסמך", "קובץ", "נתוני", "ממצאי", "תוצאת", "סקירה", "מאמר", "מקור",

    # --- Layer 6: Single Characters & Single Letter Noise ---
    "סה", "ות", "אי", "פי", "ה", "ו", "ב", "ל", "מ", "ש", "ת", "כ", "א", "ח", "נ", "ס", "פ", "ר", "ק", "י", "צ",
    "ע", "ג", "ד", "ז", "ט", "ס", "ץ", "ך", "ם", "ן", "ף", "כו", "וכו", "שלנו", "שלה", "שלו"
}

def generate_expanded_stop_words(base_set):
    """
    Dynamically expands the filter set by adding a 'Vav' prefix to every word.
    """
    expanded_set = set(base_set)  # Start with all original stop words
    for word in base_set:
        # Create a new token combined with the Hebrew 'Vav' connector prefix
        vav_combination = "ו" + word
        b_combination = "ב" + word
        sh_combination = "ש" + word
        expanded_set.add(vav_combination)
        expanded_set.add(sh_combination)
        expanded_set.add(b_combination)
    return expanded_set

def create_cleaned_columns_matrix(file_path):
    """
    Reads the original master matrix, removes all stop words per column,
    and exports a new matching matrix containing only pure tokens.
    """
    if not os.path.exists(file_path):
        print(f"Error: Original master file '{file_path}' not found.")
        return

    full_stop_words = generate_expanded_stop_words(BASE_STOP_WORDS)
    print("Loading original master matrix...")
    df = pd.read_excel(file_path)
    
    # Dictionary to hold the filtered columns
    cleaned_columns_data = {}

    print("Filtering columns individually...")
    for column in df.columns:
        # Extract raw words, drop empty padding cells
        raw_words = df[column].dropna().tolist()
        
        cleaned_words = []
        for raw_word in raw_words:
            token = str(raw_word).strip().lower()
            
            # Skip if the word is a stop word or a single character noise fragment
            if token in full_stop_words or len(token) <= 1:
                continue
            cleaned_words.append(raw_word)
        
        # Save the cleaned word list under the original filename key
        cleaned_columns_data[column] = cleaned_words

    print("Compiling the new cleaned matrix structure...")
    # Orient row lists into horizontal vectors, then transpose back to columns
    cleaned_df = pd.DataFrame.from_dict(cleaned_columns_data, orient='index').T

    # Map output path location
    output_dir = os.path.dirname(file_path)
    final_output_path = os.path.join(output_dir, "cleaned_pdf_words_columns.xlsx")

    print("Exporting the fresh token matrix to Excel...")
    cleaned_df.to_excel(final_output_path, index=False)
    
    print(f"\n--- Matrix cleaning complete! New file saved at: '{final_output_path}' ---")

if __name__ == "__main__":
    create_cleaned_columns_matrix(MASTER_EXCEL_PATH)