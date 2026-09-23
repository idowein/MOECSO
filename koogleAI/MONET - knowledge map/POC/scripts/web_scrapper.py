import os
import re
import csv
import time
from collections import Counter
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
TARGET_URL = "https://chief-scientist.education.gov.il/knowledge/publications/?filters=11043"
    
# Explicit output paths for the generated CSV files
MAP_OUTPUT_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\map.csv"
NETWORK_OUTPUT_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\network.csv"

# HTML selectors for data extraction from inner publication pages
TITLE_SELECTOR = "h1"          # Publication title
TEXT_SELECTOR = "div.content"  # Parent container holding the abstract or main text

# Hebrew stop words to filter out from the semantic network
STOP_WORDS = {
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

def setup_browser():
    """
    Configures a headless Chrome browser with anti-bot properties.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

def get_publication_page_links(driver, url):
    """
    Step 1: Opens the main gallery page and extracts links to individual publication pages.
    """
    print(f"Opening main gallery page: {url}")
    driver.get(url)
    time.sleep(6)  # Give the gov dynamic script plenty of time to render rows
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    article_links = []
    
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        # Filter for the specific URL structure of publication inner pages
        if "/knowledge/publications/" in href and "filters=" not in href:
            if not href.startswith('http'):
                href = "https://chief-scientist.education.gov.il" + href
            if href not in article_links and href != url:
                article_links.append(href)
                
    return article_links

def clean_text_to_words(text):
    """
    Cleans the extracted text, leaving only valid Hebrew words and filtering out stop words.
    """
    text = text.lower()
    hebrew_only = re.sub(r'[^א-ת\s]', ' ', text)
    words = hebrew_only.split()
    return [w for w in words if len(w) > 1 and w not in STOP_WORDS]

def ensure_directory_exists(file_path):
    """
    Extracts the directory from the file path and creates it if it doesn't exist.
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    driver = setup_browser()
    
    # Data structures for compiling network nodes and edges
    all_articles = []        # Stores dictionaries of {id, label, url}
    all_words_counter = {}   # Maps article_id to its word frequency Counter object
    unique_words_set = set() # Global tracking of all unique words found across documents
    
    try:
        # Step 1: Extract inner page URLs from the main gallery
        article_urls = get_publication_page_links(driver, TARGET_URL)
        total_articles = len(article_urls)
        print(f"Found {total_articles} individual publication pages on this screen.\n")
        
        if not article_urls:
            print("Could not parse article cards. The layout might be fully protected or blank.")
            driver.quit()
            exit()
            
        # Step 2: Traverse each inner page and parse text data
        current_article_id = 1
        
        for idx, article_url in enumerate(article_urls):
            print(f"Scanning sub-page [{idx + 1}/{total_articles}]: {article_url}")
            
            try:
                driver.get(article_url)
                time.sleep(2.5)  # Strategic delay to avoid triggering server firewalls
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                title_el = soup.select_one(TITLE_SELECTOR)
                text_el = soup.select_one(TEXT_SELECTOR)
                
                if not title_el or not text_el:
                    print(f"Skipping page {idx+1} due to missing structure.")
                    continue
                    
                title = title_el.get_text(strip=True)
                raw_text = text_el.get_text(strip=True)
                
                # Tokenize and clean text
                cleaned_words = clean_text_to_words(raw_text)
                if not cleaned_words:
                    continue
                    
                word_counts = Counter(cleaned_words)
                
                # Append article node metadata
                all_articles.append({
                    'id': current_article_id,
                    'label': title,
                    'url': article_url
                })
                
                # Map word distribution to this article ID
                all_words_counter[current_article_id] = word_counts
                
                # Update the global set of unique words
                unique_words_set.update(word_counts.keys())
                
                current_article_id += 1 # Increment ID for the next document node
                
            except Exception as inner_e:
                print(f"Error scanning page {article_url}: {inner_e}")
                time.sleep(5) # Longer backup delay in case of transient network errors
                
        if not all_articles:
            print("No articles were successfully processed. Exiting.")
            driver.quit()
            exit()

        # Step 3: Map words to sequential unique IDs continuing after the last article ID
        word_to_id = {word: idx + current_article_id for idx, word in enumerate(sorted(unique_words_set))}
        
        print(f"\nProcessing complete. Scraped {len(all_articles)} valid articles and {len(word_to_id)} unique words.")
        
        # Ensure targeted output directories exist before writing files
        ensure_directory_exists(MAP_OUTPUT_PATH)
        ensure_directory_exists(NETWORK_OUTPUT_PATH)
        
        print("Writing VOSviewer files to designated paths...")

        # Step 4: Generate VOSviewer Map file using utf-8-sig encoding for proper Hebrew display
        with open(MAP_OUTPUT_PATH, 'w', newline='', encoding='utf-8-sig') as f_map:
            writer = csv.writer(f_map)
            writer.writerow(['id', 'label', 'url', 'description'])
            
            # Write article nodes
            for art in all_articles:
                writer.writerow([art['id'], art['label'], art['url'], 'Scraped Publication'])
                
            # Write word nodes
            for word, w_id in word_to_id.items():
                writer.writerow([w_id, word, '', ''])
                
        print(f"-> Map file created successfully at: {MAP_OUTPUT_PATH}")

        # Step 5: Generate VOSviewer Network file without headers
        with open(NETWORK_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f_net:
            writer = csv.writer(f_net)
            
            # Write edges (connections) between articles and words with edge strengths
            for art_id, word_counts in all_words_counter.items():
                for word, count in word_counts.items():
                    w_id = word_to_id[word]
                    # Format: [Source Node ID, Target Node ID, Edge Weight/Strength]
                    writer.writerow([art_id, w_id, count])
                    
        print(f"-> Network file created successfully at: {NETWORK_OUTPUT_PATH}")
        print("\n🏆 Execution complete! Upload both files directly into VOSviewer.")
        
    finally:
        driver.quit()
        print("Browser execution closed safely.")