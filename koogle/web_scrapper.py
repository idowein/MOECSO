import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
TARGET_URL = "https://chief-scientist.education.gov.il/knowledge/publications/?filters=11043"
DOWNLOAD_DIR = r"C:\Users\ed2832\Downloads\MOECSO"

def setup_browser():
    """
    Configures a background Chrome browser with an anti-bot User-Agent.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

def get_publication_page_links(driver, url):
    """
    Step 1: Open the main filter page and extract links to individual publication pages.
    """
    print(f"Opening main gallery page: {url}")
    driver.get(url)
    time.sleep(6)  # Give the gov dynamic script plenty of time to render rows
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    article_links = []
    
    # Scan for links leading to specific publication sub-pages
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        # Filter for the specific URL structure of publication inner pages
        if "/knowledge/publications/" in href and "filters=" not in href:
            if not href.startswith('http'):
                href = "https://chief-scientist.education.gov.il" + href
            if href not in article_links and href != url:
                article_links.append(href)
                
    return article_links

def extract_pdf_from_inner_page(driver, page_url):
    """
    Step 2: Visit an individual publication page and find the actual download PDF link.
    """
    try:
        driver.get(page_url)
        time.sleep(2)  # Short wait for inner page assets
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if href.lower().endswith('.pdf'):
                if not href.startswith('http'):
                    href = "https://chief-scientist.education.gov.il" + href
                return href
    except Exception as e:
        print(f"Error scanning inner page {page_url}: {e}")
    return None

def download_file(pdf_url, target_directory, session, index, total):
    """
    Step 3: Securely download the raw binary PDF stream onto the storage drive.
    """
    filename = pdf_url.split('/')[-1].split('?')[0]
    if not filename or not filename.lower().endswith('.pdf'):
        filename = f"document_{index + 1}.pdf"
        
    full_save_path = os.path.join(target_directory, filename)
    print(f"[{index + 1}/{total}] Downloading: {filename}")

    try:
        response = session.get(pdf_url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(full_save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            time.sleep(1.5)  # Safety pause to keep firewall happy
        else:
            print(f"Download blocked by server. Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to save {filename}: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    driver = setup_browser()
    # Using a requests session to persist cookies and headers during downloads
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})

    try:
        # Step 1: Get all article sub-pages
        article_urls = get_publication_page_links(driver, TARGET_URL)
        print(f"Found {len(article_urls)} individual publication pages on this screen.\n")
        
        if not article_urls:
            print("Could not parse article cards. The layout might be fully protected or blank.")
            complementary = True
        else:
            # Step 2 & 3: Go deep into each page, find the PDF, and download
            pdf_targets = []
            for idx, article_url in enumerate(article_urls):
                print(f"Scanning sub-page [{idx + 1}/{len(article_urls)}]...")
                pdf_link = extract_pdf_from_inner_page(driver, article_url)
                if pdf_link:
                    pdf_targets.append(pdf_link)
            
            print(f"\nTarget map complete. Found {len(pdf_targets)} verified PDF attachments.")
            
            for index, pdf_url in enumerate(pdf_targets):
                download_file(pdf_url, DOWNLOAD_DIR, session, index, len(pdf_targets))
                
    finally:
        driver.quit()
        print("\n--- Process finished. Browser execution closed. ---")