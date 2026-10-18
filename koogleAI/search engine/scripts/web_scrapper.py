"""
Scrapes PDF publications from the Chief Scientist site, across ALL gallery pages.

The original version read only the first rendered screen of the gallery.
This version keeps loading more results (scrolling, "load more" / "next"
buttons, and a ?page=N fallback) until no new publications appear.

Requirements:
    pip install selenium beautifulsoup4 requests
    (and Google Chrome installed)
"""
import os
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- CONFIGURATION ---
BASE_SITE = "https://chief-scientist.education.gov.il"
TARGET_URL = BASE_SITE + "/knowledge/publications/?filters=11043"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.dirname(SCRIPT_DIR)  # the "search engine" folder
DOWNLOAD_DIR = os.path.join(ENGINE_DIR, "final reports 17.05.2026")

HEADLESS = True          # set to False to watch the browser and debug
MAX_ROUNDS = 100         # safety limit on "load more" / page iterations
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Text of buttons/links that load the next batch of results
NEXT_BUTTON_TEXTS = ["טען עוד", "הצג עוד", "עוד תוצאות", "לעמוד הבא", "הבא",
                     "Load more", "Show more", "Next"]


def setup_browser():
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    return webdriver.Chrome(options=chrome_options)


def collect_publication_links(html, gallery_url):
    """Return the set of publication sub-page URLs present in the given HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "/knowledge/publications/" in href and "filters=" not in href:
            if not href.startswith("http"):
                href = BASE_SITE + href
            if href.rstrip("/") != gallery_url.rstrip("/"):
                links.add(href)
    return links


def click_next_button(driver):
    """Try to click a 'load more' / 'next' control. Returns True if clicked."""
    for text in NEXT_BUTTON_TEXTS:
        xpath = (f"//*[self::a or self::button]"
                 f"[contains(normalize-space(.), '{text}') or contains(@aria-label, '{text}')]")
        for element in driver.find_elements(By.XPATH, xpath):
            try:
                if element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", element)
                    return True
            except Exception:
                continue
    return False


def get_all_publication_links(driver, url):
    """Load every batch of the gallery and gather all publication links."""
    print(f"Opening gallery: {url}")
    driver.get(url)
    time.sleep(6)

    all_links = collect_publication_links(driver.page_source, url)
    print(f"  initial screen: {len(all_links)} publications")

    # Strategy 1: scroll (lazy loading) + click "load more"/"next"
    for round_no in range(1, MAX_ROUNDS + 1):
        before = len(all_links)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        clicked = click_next_button(driver)
        if clicked:
            time.sleep(4)
        all_links |= collect_publication_links(driver.page_source, url)
        print(f"  round {round_no}: {len(all_links)} publications")
        if len(all_links) == before and not clicked:
            break
        if len(all_links) == before and clicked and round_no > 1:
            # clicked but nothing new twice in a row -> stop
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            all_links |= collect_publication_links(driver.page_source, url)
            if len(all_links) == before:
                break

    # Strategy 2: explicit page numbers in the URL
    separator = "&" if "?" in url else "?"
    for page in range(2, MAX_ROUNDS + 1):
        page_url = f"{url}{separator}page={page}"
        driver.get(page_url)
        time.sleep(4)
        found = collect_publication_links(driver.page_source, url)
        new = found - all_links
        if not new:
            break
        all_links |= new
        print(f"  ?page={page}: {len(all_links)} publications")

    return sorted(all_links)


def extract_pdf_from_inner_page(driver, page_url):
    """Visit one publication page and return its PDF link, if any."""
    try:
        driver.get(page_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href.lower().split("?")[0].endswith(".pdf"):
                if not href.startswith("http"):
                    href = BASE_SITE + href
                return href
    except Exception as e:
        print(f"Error scanning {page_url}: {e}")
    return None


def download_file(pdf_url, target_directory, session, index, total):
    filename = pdf_url.split("/")[-1].split("?")[0]
    if not filename.lower().endswith(".pdf"):
        filename = f"document_{index + 1}.pdf"

    full_save_path = os.path.join(target_directory, filename)
    if os.path.exists(full_save_path) and os.path.getsize(full_save_path) > 0:
        print(f"[{index + 1}/{total}] already exists: {filename}")
        return

    print(f"[{index + 1}/{total}] Downloading: {filename}")
    try:
        response = session.get(pdf_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(full_save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            time.sleep(1.5)
        else:
            print(f"  blocked by server, status {response.status_code}")
    except Exception as e:
        print(f"  failed to save {filename}: {e}")


if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    driver = setup_browser()
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    try:
        article_urls = get_all_publication_links(driver, TARGET_URL)
        print(f"\nFound {len(article_urls)} publication pages in total.\n")

        pdf_targets = []
        for idx, article_url in enumerate(article_urls):
            print(f"Scanning sub-page [{idx + 1}/{len(article_urls)}]...")
            pdf_link = extract_pdf_from_inner_page(driver, article_url)
            if pdf_link and pdf_link not in pdf_targets:
                pdf_targets.append(pdf_link)

        print(f"\nFound {len(pdf_targets)} PDF attachments.\n")
        for index, pdf_url in enumerate(pdf_targets):
            download_file(pdf_url, DOWNLOAD_DIR, session, index, len(pdf_targets))
    finally:
        driver.quit()
        print(f"\n--- Done. Files saved in: {DOWNLOAD_DIR} ---")