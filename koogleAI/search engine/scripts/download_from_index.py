"""
Re-downloads every PDF that the existing search index was built from.

The index (cleaned_pdf_words_columns.parquet) stores one column per PDF,
named after the PDF file. The files were originally published under
the folders listed in BASE_URLS, so each name is tried against each folder.

Place this file in the "scripts" folder and run it from anywhere:
    py download_from_index.py
Requirements:
    pip install pandas pyarrow requests
"""
import os
import time

import pandas as pd
import requests

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.dirname(SCRIPT_DIR)  # the "search engine" folder

INDEX_PATH = os.path.join(ENGINE_DIR, "cleaned_pdf_words_columns.parquet")
OUTPUT_DIR = os.path.join(ENGINE_DIR, "final reports 17.05.2026")
# The files are spread over several sub-folders on the server.
# Each name is tried against these folders in order; add more as you find them
# (open a report in the browser and copy the folder part of its address).
BASE_URLS = [
    "https://meyda.education.gov.il/files/LishcatMadaan/",
    "https://meyda.education.gov.il/files/LishcatMadaan/SkirotSifrut/",
    "https://meyda.education.gov.il/files/LishcatMadaan/CovidResearch/",
    "https://meyda.education.gov.il/files/Scientist/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
PAUSE_SECONDS = 1.0  # polite delay between downloads


def load_pdf_names(index_path):
    """Return the PDF file names stored as column headers in the index."""
    df = pd.read_parquet(index_path)
    return [str(c) for c in df.columns if str(c).lower().endswith(".pdf")]


def download(session, url, target_path):
    """Download one file. Returns True only if a real PDF was saved."""
    try:
        response = session.get(url, stream=True, timeout=30)
    except requests.RequestException:
        return False
    if response.status_code != 200:
        return False

    chunks = response.iter_content(chunk_size=8192)
    first = next(chunks, b"")
    # Servers sometimes return an HTML error page with status 200
    if not first.startswith(b"%PDF"):
        return False
    with open(target_path, "wb") as f:
        f.write(first)
        for chunk in chunks:
            f.write(chunk)
    return True


def download_from_any_folder(session, name, target_path):
    """Try every folder in BASE_URLS. Returns the URL that worked, or None."""
    for base in BASE_URLS:
        url = base + name
        if download(session, url, target_path):
            return url
    return None


def main():
    if not os.path.exists(INDEX_PATH):
        print(f"Index not found: {INDEX_PATH}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    names = load_pdf_names(INDEX_PATH)
    print(f"The index lists {len(names)} PDF files.\nSaving to: {OUTPUT_DIR}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    downloaded, skipped, missing = 0, 0, []
    for i, name in enumerate(names, start=1):
        target = os.path.join(OUTPUT_DIR, name)
        if os.path.exists(target) and os.path.getsize(target) > 0:
            skipped += 1
            continue

        url = download_from_any_folder(session, name, target)
        if url:
            downloaded += 1
            print(f"[{i}/{len(names)}] OK      {url}")
        else:
            missing.append(name)
            print(f"[{i}/{len(names)}] MISSING {name}")
        time.sleep(PAUSE_SECONDS)

    print("\n" + "=" * 50)
    print(f"Downloaded now:   {downloaded}")
    print(f"Already existed:  {skipped}")
    print(f"Not found:        {len(missing)}")

    if missing:
        missing_path = os.path.join(ENGINE_DIR, "missing_pdfs.txt")
        with open(missing_path, "w", encoding="utf-8") as f:
            f.write("\n".join(missing))
        print(f"List of missing files saved to: {missing_path}")


if __name__ == "__main__":
    main()