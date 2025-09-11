'''
Functions related to getting relevant KICS PaCs
'''

import re
import pandas as pd
from typing import Dict, Any, List, Optional


def _parse_value_literal(s: str):
    s = s.strip()
    if not s:
        return ""
    if (s[0] == s[-1]) and s[0] in ("'", '"'):
        s = s[1:-1]
    lower = s.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower == "null" or lower == "none":
        return None
    # try int/float
    try:
        if "." in s:
            return float(s)
        return int(s)
    except Exception:
        return s


def _parse_frontmatter(text: str) -> Dict[str, Any]:
    """
    Very small YAML-like frontmatter parser supporting one nesting level (used for 'hide:' block in examples).
    """
    fm = {}
    # match frontmatter block between first '---' and following '---'
    m = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.S | re.M)
    if not m:
        return fm
    body = m.group(1)
    lines = body.splitlines()
    current_parent = None
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val == "":
                    # start nested object
                    fm[key] = {}
                    current_parent = key
                else:
                    fm[key] = _parse_value_literal(val)
                    current_parent = None
        else:
            # nested under current_parent (support only one level)
            if current_parent is None:
                continue
            if ":" in line:
                nkey, nval = line.split(":", 1)
                fm[current_parent][nkey.strip()] = _parse_value_literal(nval.strip())
    return fm


def _extract_metadata(text: str) -> Dict[str, Any]:
    """
    Extract lines like:
    -   **Query id:** 0e75052f-...
    and return a dict { 'Query id': '...', ... }
    Also does minimal HTML/Markdown link unwrapping for CWE and URL.
    """
    meta = {}
    # matches lines like '-   **Query id:** 0e75...'
    for m in re.finditer(r"^\s*-\s*\*\*(?P<label>[^*]+)\*\*:\s*(?P<value>.+)$", text, re.M):
        label = m.group("label").strip()
        value = m.group("value").strip()
        # unwrap HTML tags
        # if markdown link [text](url)
        mk = re.search(r"\[([^\]]+)\]\(([^)]+)\)", value)
        if mk:
            meta[label] = {"text": mk.group(1), "url": mk.group(2)}
            continue
        # if html anchor <a href="...">text</a>
        ah = re.search(r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>', value)
        if ah:
            meta[label] = {"text": ah.group(2).strip(), "url": ah.group(1).strip()}
            continue
        # remove other html tags (e.g. span)
        clean = re.sub(r"<[^>]+>", "", value).strip()
        meta[label] = clean
    return meta


def _extract_description(text: str) -> Optional[str]:
    m = re.search(r"^###\s*Description\s*(.*?)(?=^###|^####|\Z)", text, re.S | re.M)
    if not m:
        return None
    desc = m.group(1).strip()
    return desc


def _parse_fence_attrs(attr_str: str) -> Dict[str, str]:
    attrs = {}
    # find key="value" pairs
    for k, v in re.findall(r'(\w+)\s*=\s*"([^"]*)"', attr_str):
        attrs[k] = v
    # also allow bare attributes (unlikely here) - not implemented
    return attrs


def _split_yaml_documents(code: str) -> List[str]:
    """
    Splits YAML-style documents on lines that contain only '---' (with optional whitespace).
    Returns list of trimmed document strings (non-empty).
    If no '---' is present, returns the whole code as single document (trimmed).
    """
    if re.search(r"(?m)^\s*---\s*$", code):
        parts = re.split(r"(?m)^\s*---\s*$", code)
        docs = [p.strip() for p in parts if p.strip() != ""]
        return docs
    return [code.strip()]


def _extract_code_sections(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Finds level-4 headings (#### ...) and then captures code fences inside each section.
    Each code fence entry contains: language, attrs dict, raw, documents[]
    Returns a mapping like {'vulnerable': [...], 'safe': [...], 'other section title': [...]}
    """
    sections = []
    # find all level-4 headings
    for m in re.finditer(r"^\s*####\s*(.+)$", text, re.M):
        title = m.group(1).strip()
        start = m.end()
        sections.append({"title": title, "start": start})
    # add sentinel end position
    text_len = len(text)
    for i, sec in enumerate(sections):
        end = sections[i + 1]["start"] if i + 1 < len(sections) else text_len
        sec["content"] = text[sec["start"]:end]

    result = {"vulnerable": [], "safe": [], "other": {}}
    for sec in sections:
        title = sec["title"]
        content = sec["content"]
        # find code fences in this section
        for fm in re.finditer(r"```(?P<lang>[^\s`]+)(?P<attrs>[^\n`]*?)\n(?P<code>.*?)(?=\n```)", content, re.S):
            lang = fm.group("lang").strip()
            attrs_str = fm.group("attrs") or ""
            attrs = _parse_fence_attrs(attrs_str)
            raw_code = fm.group("code").strip()
            documents = _split_yaml_documents(raw_code)
            entry = {
                "language": lang,
                "fence_attrs": attrs,
                "raw": raw_code,
                "documents": documents,
            }
            lt = title.lower()
            if "with" in lt and "without" not in lt:
                result["vulnerable"].append(entry)
            elif "without" in lt or "negative" in lt or "no" in lt:
                result["safe"].append(entry)
            else:
                # unknown classification: add under raw title
                if title not in result["other"]:
                    result["other"][title] = []
                result["other"][title].append(entry)
    return result


def parse_kics_md(filepath):
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
        "query_id": r"\*\*Query id:\*\*\s*(.+)",
        "query_name": r"\*\*Query name:\*\*\s*(.+)",
        "platform": r"\*\*Platform:\*\*\s*(.+)",
        "severity": r"\*\*Severity:\*\*.*?>(.+)<",
        "category": r"\*\*Category:\*\*\s*(.+)",
        "cwe": r"\*\*CWE:\*\*.*?\'(.+)\'",
        "url": r"\*\*URL:\*\*.*?\((.+)\)"
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
        "description": description,
        "secure_code": "\n\n".join(secure_code_blocks),
        "insecure_code": "\n\n".join(insecure_code_blocks),
        "insecure_code_hl": insecure_hl_blocks
    }])

    return df

def get_kics_pac(rootdir):
    """
    Creates final pandas df for KICS
    """
    all_records = []
    for dirpath, dirs, files in os.walk(rootdir):
        dirname = os.path.basename(dirpath)
        # If at root folder(queries), don't parse md files and continue to subdirectories
        if dirname == "queries":
            continue
        # If inside subdirectory, parse md files
        for file in files:
            if file.lower().endswith(".md"):  # ensure only .md files
                file_path = os.path.join(dirpath, file)
                file_result = parse_kics_md(file_path)
                all_records.append(file_result)
    return pd.concat(all_records, ignore_index=True) if all_records else pd.DataFrame()

        
    '''
        dirname = os.path.basename(dirpath)
        summary_file = f"{dirname}.adoc"

        summary_df = pd.DataFrame()
        if summary_file in files:
            summary_df = parse_summary_adoc(os.path.join(dirpath, summary_file))

        detail_records = []
        for f in files:
            if f.endswith(".adoc") and f != summary_file:
                detail_records.append(parse_policy_adoc(os.path.join(dirpath, f)))

        detail_df = pd.concat(detail_records, ignore_index=True) if detail_records else pd.DataFrame()

        # Merge summary + details if both exist
        if not summary_df.empty and not detail_df.empty:
            merged = summary_df.merge(detail_df, on="file", how="left")
        elif not detail_df.empty:
            merged = detail_df
        else:
            merged = summary_df  # could be empty

        if not merged.empty:
            # Add Provider + Category
            relpath = os.path.relpath(dirpath, rootdir)
            print(relpath)
            parts = relpath.split(os.sep)
            print(parts)
            def clean_name(name):
                if not name:
                    return None
                return name.replace("-policies", "")
            parent_folder_name = clean_name(parts[0]) if len(parts) > 0 else None
            print(parent_folder_name)
            # Check if parent folder needs to use subfolder name as provider
            if parent_folder_name in general_folder_names:
                # Needs to use subfolder
                merged["Provider"] = clean_name(parts[1]) if len(parts) > 1 else None
                merged["Category"] = clean_name(parts[1]) if len(parts) > 1 else None
            else:
                # No need for subfolder; map straight to provider
                if parent_folder_name in id_to_provider.keys():
                    merged["Provider"] = id_to_provider[parent_folder_name]
                # Not in mapping dict; store as-is
                else:
                    merged["Provider"] = parent_folder_name
                merged["Category"] = clean_name(parts[1]) if len(parts) > 1 else None
            all_records.append(merged)

    return pd.concat(all_records, ignore_index=True).drop_duplicates()
    '''






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
