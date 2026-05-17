import os
import pandas as pd
from collections import Counter

# --- CONFIGURATION ---
MASTER_EXCEL_PATH = r"C:\Users\ed2832\Downloads\MOECSO\koogle\pdf_words_columns.xlsx"

# Base stop words registry built from your actual dataset
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
    CRITICAL STEP: Programmatically doubles the stop words list by iterating through 
    the base set and automatically appending a 'ו' (Vav) prefix to every single word.
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

def clean_with_vav_combinations(file_path):
    """
    Applies the programmatically expanded stop words set (including 'Vav' combinations)
    to clean the master document matrix columns and export a crisp final ledger.
    """
    if not os.path.exists(file_path):
        print(f"Error: Master file '{file_path}' not found.")
        return

    # Expand the stop words dictionary dynamically in memory
    full_stop_words = generate_expanded_stop_words(BASE_STOP_WORDS)
    print(f"Base dictionary contains {len(BASE_STOP_WORDS)} words.")
    print(f"Dynamic expansion complete. Total active filters (including 'Vav' prefixes): {len(full_stop_words)}\n")

    print("Opening repository columns for token extraction...")
    df = pd.read_excel(file_path)
    
    clean_token_list = []
    removed_counter = 0

    for column in df.columns:
        words_in_col = df[column].dropna().tolist()
        
        for raw_word in words_in_col:
            token = str(raw_word).strip().lower()
            
            # Match against the combined base and vav-prefixed set
            if token in full_stop_words:
                removed_counter += 1
                continue
                
            if len(token) <= 1:
                removed_counter += 1
                continue
                
            clean_token_list.append(raw_word)

    if not clean_token_list:
        print("Linguistic ruleset stripped 100% of dataset records. Review configurations.")
        return

    print(f"Successfully filtered out {removed_counter:,} non-token structural pieces.")
    print(f"Total pure descriptive tokens remaining in registry: {len(clean_token_list):,}")

    # Generate final counts
    frequency_map = Counter(clean_token_list)
    sorted_dataset = frequency_map.most_common()

    # Formulate output structure
    output_rows = [{"Word": word, "Total_Count": count} for word, count in sorted_dataset]
    summary_df = pd.DataFrame(output_rows)

    # Output file path mapping
    base_dir = os.path.dirname(file_path)
    final_output_path = os.path.join(base_dir, "master_pure_tokens.xlsx")

    print(f"Writing {len(summary_df):,} validated tokens to the final ledger...")
    summary_df.to_excel(final_output_path, index=False)
    
    print(f"\n--- Process finalized. Cleaned database saved at: '{final_output_path}' ---")

if __name__ == "__main__":
    clean_with_vav_combinations(MASTER_EXCEL_PATH)