import os
import re
import csv
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
TARGET_URL = "https://chief-scientist.education.gov.il/knowledge/publications/?filters=11043"
    
# Unified output path for the raw text corpus (Input for the next NLP block)
CORPUS_OUTPUT_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\chief_scientist_corpus.csv"

# HTML selectors for data extraction from inner publication pages
TITLE_SELECTOR = "h1"          # Publication title

def setup_browser():
    """
    Configures a headless Chrome browser instance with anti-bot mitigation.
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
    time.sleep(6)  # Allow dynamic government scripts ample time to render database rows
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    article_links = []
    
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        # Filter for the specific URL structure belonging to inner publication nodes
        if "/knowledge/publications/" in href and "filters=" not in href:
            if not href.startswith('http'):
                href = "https://chief-scientist.education.gov.il" + href
            if href not in article_links and href != url:
                article_links.append(href)
                
    return article_links

def clean_raw_text(text):
    """
    Normalizes whitespaces, tabs, and duplicate line breaks.
    Preserves full sentences and contextual flow for optimal BERT model processing.
    """
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def ensure_directory_exists(file_path):
    """
    Extracts the parent directory from the target file path and creates it if missing.
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    driver = setup_browser()
    scraped_articles_list = []
    
    try:
        # Step 1: Extract sub-page publication links from the main gallery view
        article_urls = get_publication_page_links(driver, TARGET_URL)
        total_articles = len(article_urls)
        print(f"Found {total_articles} individual publication pages on this screen.\n")
        
        if not article_urls:
            print("Could not parse article cards. The layout might be fully protected or blank.")
            driver.quit()
            exit()
            
        # Step 2: Loop through each inner publication page and scrape structural fields
        current_article_id = 1
        
        for idx, article_url in enumerate(article_urls):
            print(f"Scanning sub-page [{idx + 1}/{total_articles}]: {article_url}")
            
            try:
                            driver.get(article_url)
                            
                            # Strategic delay: Give JavaScript plenty of time to fully inflate the text layers
                            time.sleep(5.0)  
                            
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            title_el = soup.select_one(TITLE_SELECTOR)
                            
                            if not title_el:
                                print(f"Skipping page {idx+1} due to missing title layout.")
                                continue
                                
                            title = title_el.get_text(strip=True)
                            
                            # --- THE NUCLEAR OPTION FOR TEXT RETENTION ---
                            # Instead of looking for unreliable divs like 'div.content', we grab the ENTIRE body text.
                            # To ensure we don't grab script code or style sheets, we strip them out first:
                            for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                                script_or_style.extract()
                            
                            # Grab every single readable word visible on the body object
                            raw_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
                            
                            # --- DYNAMIC TEXT FILTERING ---
                            # Since we grabbed the entire body, let's clean up generic web noise 
                            # like shared button menus or navigation labels that surround the article
                            noise_patterns = [
                                r"שתפו בפייסבוק", r"שתפו בטוויטר", r"הדפסה", r"ראשי", 
                                r"משרד החינוך", r"לשכת המדען הראשי", r"כל הזכויות שמורות"
                            ]
                            for pattern in noise_patterns:
                                raw_text = re.sub(pattern, "", raw_text)
                            
                            clean_corpus_text = clean_raw_text(raw_text)
                            
                            # Verification Check: Ensure we actually captured a substantial document
                            word_count = len(clean_corpus_text.split())
                            if word_count < 20:  # If it's too short, it's just a broken redirect page
                                print(f"-> Warning: Captured only {word_count} words. Skipping potential empty node.")
                                continue
                            
                            # Append structured row with full content body
                            scraped_articles_list.append({
                                'id': current_article_id,
                                'title': title,
                                'url': article_url,
                                'raw_text': clean_corpus_text  
                            })
                            
                            print(f"-> SUCCESS! Scraped {word_count} words for: '{title}'")
                            current_article_id += 1
                            
            except Exception as inner_e:
                
                if not scraped_articles_list:
                    print("No articles were successfully processed. Exiting.")
                    driver.quit()
                    exit()

        print(f"\nScraping complete. Successfully gathered {len(scraped_articles_list)} articles.")
        
        # Step 3: Compile into a Pandas DataFrame and export to a central CSV repository
        ensure_directory_exists(CORPUS_OUTPUT_PATH)
        
        print(f"Creating unified DataFrame and saving to: {CORPUS_OUTPUT_PATH}")
        df = pd.DataFrame(scraped_articles_list)
        df.to_csv(CORPUS_OUTPUT_PATH, index=False, encoding='utf-8-sig')
        
        print("\n🏆 Execution complete! The raw corpus table is ready for the NLP Pipeline.")
        
    finally:
        driver.quit()
        print("Browser execution closed safely.")