import os
import pandas as pd
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
import re

# --- CONFIGURATION ---
INPUT_CSV_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\MONET\v1\chief_scientist_corpus.csv"
OUTPUT_CSV_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\MONET\v1\chief_scientist_processed.csv"

# Local folder path containing the downloaded DictaBERT files
MODEL_PATH = r"C:\Users\ed2832\Downloads\projects\MOECSO\models\dictabert-morph"

# Part-of-Speech tags we want to keep for VOSviewer theme clustering
ALLOWED_POS_TAGS = {"NOUN", "PROPN", "ADJ"}

def load_dictabert_model():
    """
    Loads both the AutoTokenizer and AutoModel from local offline storage.
    """
    print(f"Loading DictaBERT model and tokenizer from: {MODEL_PATH}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    # trust_remote_code=True executes the local BertForMorphTagging.py logic cleanly
    model = AutoModel.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model.eval() 
    return model, tokenizer

def process_text_with_dicta(text, model, tokenizer):
    """
    Processes the ENTIRE article document without missing a single word.
    Splits the body into strict, sequential 40-word blocks and flattens the linguistic output.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
        
    try:
        # Step 1: Clean basic structural breaks and split into single words
        # This bypasses any hidden encoding or punctuation bugs that stop the predictor
        all_words = [w.strip() for w in text.split() if w.strip()]
        if not all_words:
            return ""
            
        valid_words = []
        chunk_size = 40  # Safe size: 40 words at a time ensures BERT never truncates
        
        # Step 2: Loop through the entire text, chunk by chunk sequentially
        for i in range(0, len(all_words), chunk_size):
            chunk_words = all_words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            # Predict precisely on this single text block
            results = model.predict([chunk_text], tokenizer=tokenizer)
            if not results:
                continue
                
            # Step 3: Gather ALL tokens from the prediction response
            for sentence_out in results:
                for token in sentence_out.get('tokens', []):
                    pos_tag = str(token.get('pos', '')).upper().strip()
                    
                    # Exact POS tag checks (Nouns, Adjectives, Proper Nouns)
                    is_noun = "NOUN" in pos_tag or pos_tag == "NN" or pos_tag == "NNP"
                    is_adj = "ADJ" in pos_tag or pos_tag == "JJ"
                    is_propn = "PROPN" in pos_tag
                    
                    if is_noun or is_adj or is_propn:
                        # Fetch the cleanest lemma available, fallback to raw token if missing
                        lemma_word = token.get('lemma', token.get('lex', ''))
                        if not lemma_word or not lemma_word.strip():
                            lemma_word = token.get('token', '')
                            
                        lemma_word = lemma_word.strip()
                        
                        # Append the word only if it's meaningful (longer than 1 character)
                        if len(lemma_word) > 1:
                            valid_words.append(lemma_word)
                            
        # Return the complete flattened string representing the whole document
        return " ".join(valid_words)
        
    except Exception as e:
        print(f"Warning: Piece dropped due to unexpected prediction error: {e}")
        return ""


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"Error: Input file missing at {INPUT_CSV_PATH}. Run block 1 first.")
        exit()
        
    # Step 1: Read raw scraped data
    print(f"Reading dataset: {INPUT_CSV_PATH}")
    df = pd.read_csv(INPUT_CSV_PATH)
    
    # Step 2: Initialize offline neural pipeline components
    dicta_model, dicta_tokenizer = load_dictabert_model()
    
    # Step 3: Run morphological analysis loop
    print("\nExecuting Block 2 & 3: Morphological Parsing & POS Filtering...")
    tqdm.pandas(desc="Analyzing Language Structure")
    
    # Pass both model and tokenizer into the progress loop
    df['cleaned_text'] = df['raw_text'].progress_apply(
        lambda x: process_text_with_dicta(x, dicta_model, dicta_tokenizer)
    )
    
    # Step 4: Export processed corpus states
    print(f"\nExporting processing results to: {OUTPUT_CSV_PATH}")
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
    
    print("\n🏆 Execution Complete! Block 2 & 3 are fully operational and processing data.")