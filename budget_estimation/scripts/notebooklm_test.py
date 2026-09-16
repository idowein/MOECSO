import os
import re
import pandas as pd
from google import genai
from google.genai import types

# ==============================================================================
# CONFIGURATION & INITIALIZATION
# ==============================================================================

# Insert your Gemini API Key here or set it as an environment variable (GEMINI_API_KEY)
API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Root directory containing the folders of research triplets
BASE_DIRECTORY = r"\\fsmateh\SYS_adlevram\DATA\קולות קוראים מחקר תקציב משערך\raw data"

# Output consolidated CSV filename
OUTPUT_CSV_FILE = "consolidated_research_dataset.csv"

# Initialize Gemini Client
client = genai.Client(api_key=API_KEY)

# ==============================================================================
# PROMPT DEFINITION
# ==============================================================================

EXTRACTION_PROMPT = """
You are a research assistant analyzing a "Golden Triplet" of research documents: (1) Call for Proposals, (2) Research Proposal, and (3) Budget Breakdown.
Analyze the provided documents for this proposal and extract/estimate the required parameters for a statistical model.

Return ONLY a clean CSV Code Block containing an English header row and exactly ONE data row.

Column Headers (in exact order):
call_title,pi_name,proposal_title,duration_months,site_count,subject_count,target_populations_count,data_waves_count,has_surveys,has_interviews,has_focus_groups,has_observations,has_tests,collection_mode,tool_development_type,languages_count,requires_translation,uses_admin_data,requires_data_linking,is_complex_design,budgeted_person_months,has_external_services,deliverables_level,has_special_equipment,is_multidisciplinary

Strict Data Mapping Rules:
[Identifiers - Free Text]
1. call_title: Title/Topic of the Call for Proposals.
2. pi_name: Principal Investigator (PI) Name.
3. proposal_title: Title of the Research Proposal.

[Continuous Numerical Variables - Integers/Floats only. Use -1 if unknown]
4. duration_months: Research duration in months (int).
5. site_count: Number of schools/institutions/research sites (int).
6. subject_count: Estimated number of subjects/participants (int).
7. target_populations_count: Number of distinct target populations (int).
8. data_waves_count: Number of data collection waves (int).
9. languages_count: Number of languages involved (int).
10. budgeted_person_months: Total budgeted person-months across all staff (float/int).

[Binary Variables - 1 for Yes, 0 for No, -1 for Unknown]
11. has_surveys: Use of questionnaires/surveys (1/0).
12. has_interviews: Use of interviews (1/0).
13. has_focus_groups: Use of focus groups (1/0).
14. has_observations: Use of observations (1/0).
15. has_tests: Use of tests/assessments (1/0).
16. requires_translation: Need for translation or cultural adaptation (1/0).
17. uses_admin_data: Use of administrative data or research room (1/0).
18. requires_data_linking: Requirement for merging/linking datasets (1/0).
19. is_complex_design: Complex design / control group / vulnerable population (1/0).
20. has_external_services: Outsourced paid services like survey institutes/editing (1/0).
21. has_special_equipment: Dedicated equipment budgeted (1/0).
22. is_multidisciplinary: Multidisciplinary scope (1/0).

[Categorical Variables (Enums) - Select exactly ONE]
23. collection_mode: Primary mode. Options: [Online, Field, SurveyInstitute, Mixed, Unknown]
24. tool_development_type: Tool dev level. Options: [Existing, Adaptation, New, Validation, Unknown]
25. deliverables_level: Scope of deliverables. Options: [Standard, Extended, Unknown]

Formatting Constraints:
- Wrap text values in double quotes (").
- Output NO introduction, markdown wrapper notes, or conclusions. Provide ONLY the raw CSV code block.
"""

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def clean_csv_response(response_text: str) -> str:
    """Extracts raw CSV content by stripping markdown code block wrappers."""
    lines = response_text.strip().split("\n")
    cleaned = [line for line in lines if not line.strip().startswith("```")]
    return "\n".join(cleaned).strip()


def process_triplet_folder(folder_path: str) -> str:
    """
    Uploads valid PDF/CSV files in a folder to Gemini API, executes the extraction prompt,
    and cleans up uploaded remote files afterwards.
    """
    uploaded_files = []
    
    # 1. Collect valid document files (PDF & CSV)
    valid_filepaths = [
        os.path.join(folder_path, f) for f in os.listdir(folder_path)
        if f.lower().endswith(('.pdf', '.csv')) and not f.startswith("~$")
    ]
    
    if len(valid_filepaths) < 3:
        print(f"  [!] Skipping {folder_path}: Found {len(valid_filepaths)} valid files (requires at least 3).")
        return None

    try:
        # 2. Upload files to Gemini File API
        print(f"  [+] Uploading {len(valid_filepaths)} files to Gemini...")
        for filepath in valid_filepaths:
            uploaded = client.files.upload(file=filepath)
            uploaded_files.append(uploaded)
            print(f"      - Uploaded: {os.path.basename(filepath)}")

        # 3. Generate structured CSV extraction content using Gemini 2.5 Flash
        print("  [+] Querying Gemini Model...")
        contents = uploaded_files + [EXTRACTION_PROMPT]
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        
        cleaned_csv = clean_csv_response(response.text)
        return cleaned_csv

    finally:
        # 4. Clean up remote files from Gemini storage
        for remote_file in uploaded_files:
            try:
                client.files.delete(name=remote_file.name)
            except Exception as clean_err:
                print(f"      [!] Failed to delete remote file {remote_file.name}: {clean_err}")


def main():
    """Main execution loop scanning directories and generating consolidated CSV."""
    all_csv_rows = []
    header_line = None

    print("==================================================")
    print(" Starting Research Triplet Batch Extraction Processing")
    print("==================================================")

    # Traverse directory tree recursively
    for root, dirs, files in os.walk(BASE_DIRECTORY):
        folder_name = os.path.basename(root)
        
        # Determine if directory contains candidate files
        candidate_files = [f for f in files if f.lower().endswith(('.pdf', '.csv')) and not f.startswith("~$")]
        if len(candidate_files) >= 3:
            print(f"\nProcessing Folder: {folder_name}")
            try:
                csv_output = process_triplet_folder(root)
                if csv_output:
                    lines = csv_output.split("\n")
                    if len(lines) >= 2:
                        if header_line is None:
                            header_line = lines[0] # Capture standard header
                        
                        all_csv_rows.append(lines[1]) # Capture data row
                        print(f"  [✓] Successfully extracted data row for: {folder_name}")
                    else:
                        print(f"  [X] Invalid CSV response structure for: {folder_name}")
            except Exception as e:
                print(f"  [X] Error processing folder {folder_name}: {e}")

    # Save consolidated results to file
    if header_line and all_csv_rows:
        with open(OUTPUT_CSV_FILE, "w", encoding="utf-8-sig") as out_f:
            out_f.write(header_line + "\n")
            for row in all_csv_rows:
                out_f.write(row + "\n")
        print("\n==================================================")
        print(f"[SUCCESS] Dataset compiled successfully!")
        print(f"Output saved to: {os.path.abspath(OUTPUT_CSV_FILE)}")
        print("==================================================")
    else:
        print("\n[!] Processing completed, but no rows were extracted.")

if __name__ == "__main__":
    main()