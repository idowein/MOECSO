import csv
import spacy
from collections import defaultdict

# --- CONFIGURATION PATHS ---
INPUT_MAP = r"C:\Users\ed2832\Downloads\MOECSO\VOSviewer\raw data\map.txt"
INPUT_NETWORK = r"C:\Users\ed2832\Downloads\MOECSO\VOSviewer\raw data\network.txt"

OUTPUT_MAP = r"C:\Users\ed2832\Downloads\MOECSO\VOSviewer\clean data\map.txt"
OUTPUT_NETWORK = r"C:\Users\ed2832\Downloads\MOECSO\VOSviewer\clean data\network.txt"

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
    "חינוך", "החינוך", "מערכת", "המערכת", "פרופ", "ופרופ", "לשכת", "המדענית", "מדענית",
    
    # Custom project terms added for filtration
    "חוסן", "נפשי", "החוסן", "הנפשי"
}

# --- BASE PHRASE CONSOLIDATION ---
BASE_PHRASE_CONSOLIDATION = {
    "בית": "בית_ספר", "ספר": "בית_ספר", "בתי": "בית_ספר", "ספרים": "בית_ספר", "הספר": "בית_ספר",
    "חרבות": "חרבות_ברזל", "ברזל": "חרבות_ברזל",
    "גמישות": "גמישות_פדגוגית", "פדגוגית": "גמישות_פדגוגית", "גפן": "גמישות_פדגוגית", "גפ\"ן": "גמישות_פדגוגית",
    "גני": "גני_ילדים", "ילדים": "גני_ילדים",
    "עובדי": "עובדי_הוראה",
    "מוסד": "מוסד_חינוכי", "מוסדות": "מוסד_חינוכי", "המוסד": "מוסד_חינוכי", "המוסדות": "מוסד_חינוכי"
}

def expand_blacklist_with_prefixes(base_blacklist):
    """Adds common Hebrew single-letter prefixes to the words removal list."""
    expanded_set = set(base_blacklist)
    prefixes = ["ו", "מ", "ה", "ב", "ל", "כ", "וה", "וב", "ול", "ומ"]
    for word in base_blacklist:
        for prefix in prefixes:
            expanded_set.add(prefix + word)
    return expanded_set

def expand_phrases_with_prefixes(base_phrases):
    """Dynamically generates Hebrew grammatical prefix permutations for key phrases."""
    expanded_dict = dict(base_phrases)
    prefixes = ["ו", "מ", "ה", "ב", "ל", "כ", "וה", "וב", "ול", "ומ", "בב", "מה"]
    for word, target_token in base_phrases.items():
        for prefix in prefixes:
            expanded_dict[prefix + word] = target_token
    return expanded_dict

if __name__ == "__main__":
    print("🧠 Loading Built-in Blank Hebrew spaCy Tokenizer...")
    nlp = spacy.blank("he")

    print("🔄 Dynamically expanding blacklist and phrase map prefixes...")
    FINAL_WORDS_TO_REMOVE = expand_blacklist_with_prefixes(WORDS_TO_REMOVE)
    FINAL_PHRASE_CONSOLIDATION = expand_phrases_with_prefixes(BASE_PHRASE_CONSOLIDATION)

    old_id_to_label = {}
    articles_metadata = []
    publication_ids = set()
    
    # Step 1: Read the source map file containing all text nodes
    print("📂 Reading source mapping structure...")
    with open(INPUT_MAP, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        for row in reader:
            if not row: continue
            node_id, label, url, desc = row[0], row[1], row[2], row[3]
            
            if "Scraped Publication" in desc or url.startswith("http"):
                articles_metadata.append(row)
                publication_ids.add(node_id)
            else:
                old_id_to_label[node_id] = label

    # Step 2: Pre-calculate the degree/intersection frequency of each old token in the network
    print("🔢 Pre-calculating connection intersections from raw network...")
    token_occurrence_count = defaultdict(int)
    raw_edges_store = []

    with open(INPUT_NETWORK, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if not row: continue
            src, tgt, weight = row[0], row[1], int(row[2])
            raw_edges_store.append((src, tgt, weight))
            
            # Count occurrences only for term nodes, exclude publications from frequency decay
            if src not in publication_ids:
                token_occurrence_count[src] += 1
            if tgt not in publication_ids:
                token_occurrence_count[tgt] += 1

    # Step 3: Map labels into standardized tokens while dropping low frequency ones
    label_to_new_id = {}
    new_map_rows = [header] + articles_metadata
    next_node_id = len(articles_metadata) + 1
    
    old_id_to_new_id = {}
    removed_ids = set()

    print("⚡ Tokenizing and filtering low-degree terms (< 2 intersections)...")
    for old_id, label in old_id_to_label.items():
        # FILTER A: Drop terms with less than 2 distinct network edge intersections
        if token_occurrence_count[old_id] < 2:
            removed_ids.add(old_id)
            continue

        # FILTER B: Pre-filter using the prefix-complete blacklist
        if label in FINAL_WORDS_TO_REMOVE or len(label) <= 1:
            removed_ids.add(old_id)
            continue

        # TRANSFORMATION: Match against phrase configurations
        if label in FINAL_PHRASE_CONSOLIDATION:
            final_label = FINAL_PHRASE_CONSOLIDATION[label]
        else:
            doc = nlp(label)
            final_label = doc[0].text.strip() if doc else label

        # FILTER C: Secondary check against expanded noise sets
        if final_label in FINAL_WORDS_TO_REMOVE or len(final_label) <= 1:
            removed_ids.add(old_id)
            continue

        # Re-index remaining qualified tokens
        if final_label not in label_to_new_id:
            label_to_new_id[final_label] = str(next_node_id)
            new_map_rows.append([str(next_node_id), final_label, "", "Cleaned NLP Token"])
            next_node_id += 1
            
        old_id_to_new_id[old_id] = label_to_new_id[final_label]

    print(f"📉 Filtered out {len(removed_ids)} nodes due to noise or insufficient intersections (<2).")

    # Step 4: Rebuild and aggregate graph edge connections
    print("📊 Rebuilding and aggregating graph edge connections...")
    network_edges = defaultdict(int)
    
    for src, tgt, weight in raw_edges_store:
        if src in removed_ids or tgt in removed_ids:
            continue
            
        new_src = old_id_to_new_id.get(src, src)
        new_tgt = old_id_to_new_id.get(tgt, tgt)
        
        if new_src == new_tgt:
            continue
            
        network_edges[(new_src, new_tgt)] += weight

    # Step 5: Save outputs to targeted clean storage locations
    print("💾 Saving clean outputs for VOSviewer ingestion...")
    with open(OUTPUT_MAP, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(new_map_rows)
        
    with open(OUTPUT_NETWORK, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        for (src, tgt), total_weight in network_edges.items():
            writer.writerow([src, tgt, total_weight])
            
    print("🏆 Pipeline complete! Low-frequency tokens dropped successfully.")