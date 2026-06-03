import csv
import re
from collections import defaultdict

# --- CONFIGURATION PATHS ---
INPUT_MAP = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\raw data\map.txt"
INPUT_NETWORK = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\raw data\network.txt"

OUTPUT_MAP = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\clean data\map.txt"
OUTPUT_NETWORK = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\clean data\network.txt"

# --- BLACKLIST: Non-thematic, administrative, and generic Hebrew noise words ---
WORDS_TO_REMOVE = {
    # Prepositions & Particles
    "מאת", "של", "את", "על", "אל", "מן", "מה", "עם", "או", "גם", "כי", "אם", "אלא", "ולא", "וכן", "האם", "אכן", 
    "יש", "אין", "לא", "כן", "לכל", "בכל", "מכל", "בקרב", "בעת", "לצד", "מתוך", "בתוך", "כלל", "בכלל", "לעומת", 
    "באמצעות", "על-ידי", "עלידי", "לאור", "עקב", "בשל", "בתור", "כגון", "לשם", "לגבי", "במהלך", "נוגע", "בנוגע", 
    "אודות", "להלן", "לעיל", "אשר", "איזה", "איזו", "אילו", "מכיוון", "משום", "כיוון", "לכן", "ללא", "בלי", 
    "לפי", "עבור", "שבו", "שבה", "שבהם", "שבהן", "מול", "נגד", "אצל", "בגלל", "למען", "בכדי", "כדי", "דרך", 
    "מאז", "לעבר", "סביב", "תחת", "מעל", "מתחת", "עד", "ככל", "כפי", "כל", "כך", "כמו", "ידי", "כאשר", "אז", 
    "אף", "למרות", "לכך", "בעוד", "עוד", "בלבד", "כאילו", "עת", "לפני", "אחרי", "אבל", "אך",

    # Pronouns
    "אני", "אתה", "את", "הוא", "היא", "אנחנו", "אתם", "אתן", "הם", "הן", "עצמו", "עצמה", "עצמם", "עצמן", 
    "זה", "זו", "זאת", "אלו", "אלה", "הללו", "ההוא", "ההיא", "הנך", "הנני", "הנם", "לי", "לך", "לו", "לה", 
    "לנו", "לכם", "לכן", "להם", "להן", "בי", "בך", "בו", "בה", "בנו", "בכם", "בכן", "בהם", "בהן", "אותי", 
    "אותך", "אותו", "אותה", "אותנו", "אתכם", "אתכן", "אותם", "אותן", "שלו", "שלה", "שלנו", "שלכם", "שלכן", 
    "שלהם", "שלהן", "איתי", "איתך", "איתו", "איתה", "איתנו", "איתכם", "איתכן", "איתם", "איתן", "עליי", 
    "עליך", "עליו", "עליה", "עלינו", "עליכם", "עליכן", "עליהם", "עליהן", "מעליי", "מעליו", "מעליה", "ממני", 
    "ממך", "ממנו", "ממנה", "מאיתנו", "מכם", "מכן", "מהם", "מהן", "מכך",

    # Generic Verbs & Actions
    "לעשות", "עשייה", "נעשה", "נעשתה", "נעשים", "נעשות", "לעסוק", "עוסק", "עוסקת", "עוסקים", "עוסקות", "לבחון", 
    "בוחן", "בוחנת", "בוחנים", "בוחנות", "לבצע", "בוצע", "מבוצע", "להציג", "מציג", "מציגה", "מציגים", "מציגות", 
    "להוביל", "מוביל", "מובילה", "מובילים", "מובילות", "לתמוך", "תמיכה", "תומך", "תומכת", "ליצור", "יצירה", 
    "יוצר", "יוצרת", "לבנות", "בנייה", "בונה", "נועד", "נועדה", "נועדו", "נועדים", "נועדות", "לשלב", "משלב", 
    "משלבת", "משלבים", "שילוב", "להביא", "מביא", "מביאה", "מביאים", "לכלול", "כולל", "כוללת", "כוללים", "כוללות", 
    "להסביר", "הסבר", "להבין", "הבנה", "מבין", "מבינה", "לדעת", "יודע", "יודעת", "לחקור", "חוקר", "חוקרת", 
    "חוקרים", "למצוא", "מוצא", "נמצא", "נמצאו", "נמצאה", "קשור", "קשורה", "קשורים", "להשפיע", "משפיע", "משפיעה", 
    "השפעה", "השפעות", "לתאר", "מתאר", "מתארת", "תיאור", "לפתח", "מפתח", "פיתוח", "ליישם", "מיישם", "יישום", 
    "להטמיע", "מטמיע", "הטמעה", "לקדם", "מקדם", "קידום", "הפך", "הפכה", "הופך", "הופכת", "קיימים", "קיים", 
    "קיימת", "קיימות", "אפשר", "אפשרות", "אפשרויות", "ניתן", "יכול", "יכולה", "יכולים", "יכולות", "יוכל",

    # Administrative & Academic Structure Noise
    "מחקר", "מחקרי", "מחקרים", "מחקריהם", "דוח", "דו\"ח", "דוחות", "דו\"חות", "מסמך", "מסמכים", "נייר", 
    "עמדה", "קובץ", "קבצים", "נתונים", "נתון", "ממצא", "ממצאים", "תוצאה", "תוצאות", "סיכום", "סיכומים", 
    "מבוא", "מבואות", "נספח", "נספחים", "טבלה", "טבלאות", "גרף", "גרפים", "איור", "איורים", "אסופה", 
    "אסופות", "מידעון", "מידעונים", "סקירה", "סקירות", "סקירת", "מאמר", "מאמרים", "כתבה", "כתבות", 
    "חוברת", "חוברות", "פרק", "פרקים", "עמוד", "עמודים", "בסיס", "מפתח", "תקציר", "תקצירים", "הערכה", 
    "מדידה", "מדד", "מדדים", "אינדיקטורים", "מתודולוגיה", "כלי", "כלים", "מודל", "מודלים", "תחום", 
    "תחומי", "תחומים", "היבט", "היבטים", "מושג", "מושגים", "סוגיה", "סוגיות", "מערכת", "מערכות", 
    "תהליך", "תהליכים", "גורם", "גורמים", "מאפיין", "מאפיינים", "מדיניות", "תוכנית", "תכנית", 
    "תוכניות", "תכניות", "התפתחות", "פרויקט", "פרוייקט", "פרויקטים", "פרוייקטים", "מיזם", "מיזמים", 
    "יוזמה", "יוזמות", "פעילות", "פעילויות", "אתגר", "אתגרים", "הזדמנויות", "כיוונים", "המלצות", 
    "מגמות", "קשר", "קשרים", "זיקה", "זיקות", "תפקיד", "תפקידים", "תפקוד", "תפקודים", "רקע", 
    "תשתית", "תשתיות", "מצב", "מצבים", "סביבה", "סביבות", "רכיב", "רכיבים", "נושא", "נושאים", 
    "עניין", "עניינים", "בעיה", "בעיות", "שאלה", "שאלות", "תובנה", "תובנות", "מבט", "מבטים", 
    "תפיסה", "תפיסות", "עמדה", "עמדות", "גישה", "גישות", "דרך", "דרכים", "אופן", "אופנים", 
    "צורה", "צורות", "אמצעי", "אמצעים", "מענה", "מענים", "פתרון", "פתרונות", "חשיבות", "נחיצות", 
    "צורך", "צרכים", "תוצר", "תוצרים", "השלכה", "השלכות",

    # Adjectives & Quantifiers
    "גבוה", "גבוהה", "גבוהים", "גבוהות", "נמוך", "נמוכה", "נמוכים", "נמוכות", "חדש", "חדשה", "חדשים", 
    "חדשות", "ישן", "ישנה", "ישנים", "ישנות", "רב", "רבה", "רבים", "רבות", "מעט", "מעטים", "מעטות", 
    "שונה", "שונים", "שונות", "מרכזי", "מרכזית", "מרכזיים", "מרכזיות", "עיקרי", "עיקרית", "עיקריים", 
    "עיקריות", "כללי", "כללית", "כלליים", "כלליות", "ספציפי", "ספציפית", "מקומי", "מקומית", "לאומי", 
    "לאומית", "בינלאומי", "בינלאומית", "ראשון", "ראשונה", "ראשונים", "ראשונות", "שני", "שנייה", 
    "שניים", "שניות", "שלישי", "שלישית", "הבא", "הבאה", "הבאים", "הבאות", "קודם", "קודמת", "קודמים", 
    "קודמות", "אחרון", "אחרונה", "אחרונים", "אחרונות", "משמעותי", "משמעותית", "משמעותיים", "משמעותיות", 
    "חשוב", "חשובה", "חשובים", "חשובות", "רלוונטי", "רלוונטית", "רלוונטיים", "רלוונטיות", "מרבית", 
    "רוב", "חלק", "סך", "מספר", "כמות", "היקף", "אחוז", "אחוזים", "רמה", "רמות", "שיעור", "שיעורים", 
    "שלב", "שלבים", "חלקים", "חלק א", "חלק ב", "חלק ג", "סעיף", "במיוחד", "בעיקר", "לחלוטין", "לגמרי", 
    "כמעט", "ביותר", "פחות", "יותר", "מדי", "טוב", "טובה", "טובים", "טובות", "רע", "רעה", "רעים", "רעות",

    # Temporal & Institutional Background Noise
    "שנה", "שנים", "שנת", "שנתי", "שנתו", "תקופה", "תקופת", "תקופות", "מועד", "מועדים", "זמן", "זמנים", 
    "חודש", "חודשים", "יום", "ימים", "שבוע", "שבועות", "בוקר", "ערב", "צהריים", "לילה", "פסח", "חנוכה", 
    "סוכות", "חגים", "חג", "תשפ\"ו", "תשפ\"ה", "תשפ\"ד", "תשפ\"ג", "תשפ\"ב", "תשפ\"א", "תש\"ו", "תש\"ה", 
    "תש\"ד", "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "ישראל", "בישראל", "משרד", 
    "המשרד", "משרדים", "לשכה", "הלשכה", "מדען", "ראשי", "המדען", "הראשי", "הוראה", "למידה", "לימוד", 
    "חינוך", "החינוך", "מערכת", "המערכת"
}

# --- CONSOLIDATION: Unifying split words into a single meaningful phrase token ---
PHRASE_CONSOLIDATION = {
    "בית": "בית_ספר", "ספר": "בית_ספר", "בתי": "בית_ספר", "ספרים": "בית_ספר", "הספר": "בית_ספר",
    "חרבות": "חרבות_ברזל", "ברזל": "חרבות_ברזל",
    "גמישות": "גמישות_פדגוגית", "פדגוגית": "גמישות_פדגוגית", "גפן": "גמישות_פדגוגית", "גפ\"ן": "גמישות_פדגוגית",
    "גני": "גני_ילדים", "ילדים": "גני_ילדים",
    "עובדי": "עובדי_הוראה", "הוראה": "עובדי_הוראה"
}

# --- LEMMATIZATION MAP: Manual remapping dictionary to protect word structures from truncation ---
EXPLICIT_REMAPS = {
    "החינוך": "חינוך", "בחינוך": "חינוך", "לחינוך": "חינוך", "מחינוך": "חינוך", "וחינוך": "חינוך",
    "ההוראה": "הוראה", "בהוראה": "הוראה", "להוראה": "הוראה",
    "הלמידה": "למידה", "בלמידה": "למידה", "ללמידה": "למידה",
    "המורים": "מורים", "במורים": "מורים", "למורים": "מורים", "הורה": "הורים", "ההורים": "הורים", "ורים": "הורים", "מור": "מורה",
    "התלמידים": "תלמידים", "בתלמידים": "תלמידים", "לתלמידים": "תלמידים", "תלמיד": "תלמידים",
    "חינוכית": "חינוך", "חינוכי": "חינוך", "החינוכי": "חינוך", "החינוכית": "חינוך",
    "הערכה": "הערכה", "בהערכה": "הערכה", "ההערכה": "הערכה",
    "המשבר": "משבר", "במשבר": "משבר", "הסביבה": "סביבה", "בסביבה": "סביבה",
    "אוריינ": "אוריינות"
}

def clean_hebrew_prefix(word):
    """
    Safely strips common Hebrew prepositions/prefixes (ה, ב, ל, כ, מ, ו)
    from the beginning of the string without truncating or harming word endings.
    """
    if len(word) <= 3:
        return word
    
    # Regular expression matching specific singular Hebrew character prefixes
    cleaned = re.sub(r'^[ומהבלכ](?=[א-ת]{3,})', '', word)
    return cleaned

if __name__ == "__main__":
    print("🚀 Starting pipeline: Cleaning with massive wordlist, Consolidating, and Normalizing Safely...")

    old_id_to_label = {}
    articles_metadata = []
    
    # Step 1: Read and process the source map data
    with open(INPUT_MAP, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        for row in reader:
            if not row: continue
            node_id, label, url, desc = row[0], row[1], row[2], row[3]
            
            # Isolate publication rows to pass them through untouched
            if "Scraped Publication" in desc or url.startswith("http"):
                articles_metadata.append(row)
            else:
                old_id_to_label[node_id] = label

    # Build a dictionary for the new sanitized and normalized mapping structure
    label_to_new_id = {}
    new_map_rows = [header] + articles_metadata
    next_node_id = len(articles_metadata) + 1
    
    old_id_to_new_id = {}
    removed_ids = set()

    for old_id, label in old_id_to_label.items():
        # A) Filter out blacklisted words
        if label in WORDS_TO_REMOVE:
            removed_ids.add(old_id)
            continue
            
        # B) Consolidate multi-word phrase components (e.g., school terms or war names)
        if label in PHRASE_CONSOLIDATION:
            final_label = PHRASE_CONSOLIDATION[label]
        # C) Apply explicit static token mappings
        elif label in EXPLICIT_REMAPS:
            final_label = EXPLICIT_REMAPS[label]
        else:
            # D) Strip minor grammatical prefixes safely
            final_label = clean_hebrew_prefix(label)
            
        if final_label in WORDS_TO_REMOVE or len(final_label) <= 1:
            removed_ids.add(old_id)
            continue

        # Allocate new numeric node IDs or link to an existing consolidated group
        if final_label not in label_to_new_id:
            label_to_new_id[final_label] = str(next_node_id)
            new_map_rows.append([str(next_node_id), final_label, "", "Cleaned Term"])
            next_node_id += 1
            
        old_id_to_new_id[old_id] = label_to_new_id[final_label]

    print(f"Purged {len(removed_ids)} raw words using the massive blacklist. Map structure optimized.")

    # Step 2: Read network infrastructure data and aggregate weights for unified edges
    network_edges = defaultdict(int)
    
    with open(INPUT_NETWORK, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if not row: continue
            src, tgt, weight = row[0], row[1], int(row[2])
            
            # Drop connections attached to blacklisted terms
            if src in removed_ids or tgt in removed_ids:
                continue
                
            # Remap old structural node IDs to consolidated target values
            new_src = old_id_to_new_id.get(src, src)
            new_tgt = old_id_to_new_id.get(tgt, tgt)
            
            # Prevent programmatic self-loops from collapsed tokens
            if new_src == new_tgt:
                continue
                
            network_edges[(new_src, new_tgt)] += weight

    # Step 3: Write out pristine tab-separated structural outputs for VOSviewer
    with open(OUTPUT_MAP, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(new_map_rows)
        
    with open(OUTPUT_NETWORK, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        for (src, tgt), total_weight in network_edges.items():
            writer.writerow([src, tgt, total_weight])
            
    print("🏆 Done! Safe Pipeline execution complete with massive blacklist and precise output routing.")
    print(f"Cleaned map written to: {OUTPUT_MAP}")
    print(f"Cleaned network written to: {OUTPUT_NETWORK}")