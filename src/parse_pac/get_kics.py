'''
Functions related to getting relevant KICS PaCs
'''
import os
import re
import pandas as pd
import json

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
        "IaC": r"\*\*Platform:\*\*\s*(.+)",
        "Severity": r"\*\*Severity:\*\*.*?>(.+)<",
        "Category": r"\*\*Category:\*\*\s*(.+)",
        "CWE": r"\*\*CWE:\*\*.*?\'(.+)\'",
        "Query Document": r"\*\*URL:\*\*.*?\((.+)\)",
        "Related Document": r"\[Documentation\]\s*\((.+)\)",
    }
    
    metadata = {key: re.search(pattern, md_content, re.MULTILINE).group(1).strip() 
            for key, pattern in metadata_patterns.items()}
    # --- 2. Extract description ---
    desc_match = re.search(r"### Description\s*(.+?)<", md_content, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    # --- 3. Extract code samples ---
    code_block_re = re.compile(
        r"(?P<fence>```|~~~)(?P<lang>[^\s`~]+)(?P<attrs>[^\n`]*)[ \t]*\n(?P<code>[\s\S]*?)\n?(?P=fence)",
        re.DOTALL
    )


    # --- 4. Separate positive and negative examples ---
    
    secure_code_blocks = []
    insecure_code_blocks = []
    insecure_hl_blocks = []
    
    for m in code_block_re.finditer(md_content):
        lang = m.group('lang')
        attrs = m.group('attrs') or ""
        code = m.group('code').strip()

        title_match = re.search(r'title\s*=\s*"([^"]*)"', attrs)
        hl_match    = re.search(r'hl_lines\s*=\s*"([^"]*)"', attrs)

        title = title_match.group(1) if title_match else None
        hl_raw = hl_match.group(1) if hl_match else ""
        hl_lines_list = [int(x) for x in re.findall(r'\d+', hl_raw)] if hl_raw else []

        if title and "Positive" in title:
            insecure_code_blocks.append(code)
            insecure_hl_blocks.append(hl_lines_list)
        elif title and "Negative" in title:
            secure_code_blocks.append(code)

    # --- 5. Build single-row DataFrame ---
    # --- Build row with dynamic columns ---
    row = {
        **metadata,
        "Subcategory": subcategory,
        "Description": description
    }
    # add secure examples
    for i, code in enumerate(secure_code_blocks, start=1):
        row[f"Secure Code Example {i}"] = code

    # add insecure examples + line highlights
    for i, (code, lines) in enumerate(zip(insecure_code_blocks, insecure_hl_blocks), start=1):
        row[f"Insecure Code Example {i}"] = code
        # serialize list so SQLite can handle it
        if isinstance(lines, list):
            row[f"Insecure Code Line {i}"] = json.dumps(lines)  # store as JSON
        else:
            row[f"Insecure Code Line {i}"] = lines

    df = pd.DataFrame([row])
    df["Open-source Tool"] = ["KICS"] * len(df)
    # print(df.columns.to_list())
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
                if len(parts) == 1:
                    # Case: queries/file.md
                    continue
                elif len(parts) == 2:
                    # Case: queries/provider-queries/file.md
                    subcategory = parts[0]
                elif len(parts) == 3:
                    # Case: queries/provider-queries/service/file.md
                    subcategory = parts[1]
                else:
                    # Edge case; unknown
                    subcategory = "Unknown"
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
    head_file_path = os.path.join(tool_raw_path, full_tool_info[tool]["head_path"])
    df = get_kics_pac(head_file_path)
    pd.set_option("display.max_colwidth", 120)
    print(df.head())
    print(df.shape)
    df.to_csv("kics.csv")

