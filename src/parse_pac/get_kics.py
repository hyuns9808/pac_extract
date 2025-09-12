'''
Functions related to getting relevant KICS PaCs
'''

import re
import pandas as pd
from typing import Dict, Any, List, Optional

def parse_kics_md(filepath, subcategory="Unknown"):
    """
    Parse the markdown security-query document and return a structured dict.
    Keys returned:
      - frontmatter: dict (simple YAML frontmatter)
      - metadata: dict
      - description: str (or None)
      - code_samples: { 'vulnerable': [...], 'safe': [...], 'other': {...} }
    """
    # Read the markdown file
    with open(filepath, "r", encoding="utf-8") as f:
        md_content = f.read()

    # --- 1. Extract metadata ---
    metadata_patterns = {
        "ID": r"\*\*Query id:\*\*\s*(.+)",
        "Title": r"\*\*Query name:\*\*\s*(.+)",
        "Tool": r"\*\*Platform:\*\*\s*(.+)",
        "Severity": r"\*\*Severity:\*\*.*?>(.+)<",
        "Category": r"\*\*Category:\*\*\s*(.+)",
        "CWE": r"\*\*CWE:\*\*.*?\'(.+)\'",
        "Related Document": r"\*\*URL:\*\*.*?\((.+)\)"
    }

    metadata = {key: re.search(pattern, md_content, re.MULTILINE).group(1).strip() 
                for key, pattern in metadata_patterns.items()}

    # --- 2. Extract description ---
    desc_match = re.search(r"### Description\s*(.+?)\n###", md_content, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    # --- 3. Extract code samples ---
    code_pattern = re.compile(
        r"```yaml\s*(?:title=\"([^\"]+)\")?\s*(?:hl_lines=\"([^\"]+)\")?\s*\n(.*?)```",
        re.DOTALL
    )

    matches = code_pattern.findall(md_content)

    # --- 4. Separate positive and negative examples ---
    secure_code_blocks = []
    insecure_code_blocks = []
    insecure_hl_blocks = []

    for match in matches:
        title, hl_lines, code = match
        hl_lines_list = [int(x) for x in hl_lines.split() if x.isdigit()] if hl_lines else []
        
        if title and "Positive" in title:
            insecure_code_blocks.append(code.strip())
            insecure_hl_blocks.append(hl_lines_list)
        elif title and "Negative" in title:
            secure_code_blocks.append(code.strip())

    # --- 5. Build single-row DataFrame ---
    df = pd.DataFrame([{
        **metadata,
        "Subcategory": subcategory,
        "Description": description,
        "Secure Code Example": "\n\n".join(secure_code_blocks),
        "Insecure Code Example": "\n\n".join(insecure_code_blocks),
        "Insecure Code Line": insecure_hl_blocks
    }])

    return df

def get_kics_pac(rootdir):
    """
    Creates final pandas df for KICS
    """
    all_records = []
    for root, dirs, files in os.walk(rootdir):
        for file in files:
            if file.lower().endswith(".md"):  # ensure only .md files
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, rootdir)
                
                parts = rel_path.split(os.sep)
                # parts: [provider-queries, ...]
                provider_dir = parts[0]

                if len(parts) == 2:
                    # Case: queries/provider-queries/file.md
                    continue
                elif len(parts) == 3:
                    # Case: queries/provider-queries/service/file.md
                    subcategory = parts[1]
                else:
                    # Edge case; unknown
                    subcategory = "Unknown"
                print(file_path)
                file_result = parse_kics_md(file_path, subcategory)
                all_records.append(file_result)
    return pd.concat(all_records, ignore_index=True) if all_records else pd.DataFrame()

# Use for single dataset clone unit testing
if __name__ == "__main__":
    import sys
    import os
    target_dir = os.path.abspath('C:\\Exception\\InProgress\\pac_extract\\src')
    sys.path.append(target_dir)
    from init_setup.setup_integrity import data_init, data_checker, create_ver_token
    from init_setup.setup_base import dir_init, dir_update, get_update_tool_list
    project_root, pac_raw_dir, pac_db_dir, master_db_dir = dir_init()
    version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)
    tool = "KICS"
    tool_raw_path = os.path.join(pac_raw_dir, tool)
    df = get_kics_pac(tool_raw_path)
    pd.set_option("display.max_colwidth", 120)
    print(df.head())
    print(df.shape)
    df.to_csv("kics.csv")
