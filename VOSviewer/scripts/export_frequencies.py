import csv
from collections import defaultdict

# --- CONFIGURATION ---
INPUT_MAP = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\clean data\map.txt"
INPUT_NETWORK = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\clean data\network.txt"

# The output file that will contain the full list
OUTPUT_CSV = r"C:\Users\ed2832\Downloads\projects\MOECSO\VOSviewer\raw data\word frequencies.csv"

if __name__ == "__main__":
    print("Analyzing and extracting all word frequencies...")
    
    # Step 1: Load all valid term labels from map.txt (ignoring publication nodes)
    id_to_label = {}
    with open(INPUT_MAP, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header row
        for row in reader:
            if row and len(row) >= 4:
                # Filter specifically for terms, not the publication documents
                if "Scraped Publication" not in row[3]:
                    id_to_label[row[0]] = row[1]

    # Step 2: Sum up all connection weights from network.txt for each word ID
    word_frequencies = defaultdict(int)
    with open(INPUT_NETWORK, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if row:
                src, tgt, weight = row[0], row[1], int(row[2])
                # Accumulate weight if the ID belongs to a mapped word
                if tgt in id_to_label:
                    word_frequencies[tgt] += weight
                if src in id_to_label:
                    word_frequencies[src] += weight

    # Step 3: Sort all extracted words by absolute count in descending order
    sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)

    # Step 4: Write the entire compiled list into a clean CSV file with UTF-8 BOM for Hebrew
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['Word', 'Total Occurrences']) # CSV Headers
        
        for w_id, freq in sorted_words:
            word_label = id_to_label[w_id]
            writer.writerow([word_label, freq])

    print(f"🏆 Complete list successfully exported! Total words: {len(sorted_words)}")
    print(f"File saved at: {OUTPUT_CSV}")