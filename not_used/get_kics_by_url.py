'''
Previous function used to get relevant KICS PaCs using URL-based download
Replaced with KICS repo download solution, saved just in case for future use
Reads stored .csv file for all queries, searches relevant ones and returns it as a dataframe
'''
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

# Correctly parses query document link into provider name
id_to_provider = {
    "alicloud": "Alibaba Cloud",
    "aws": "AWS",
    "azure": "Azure",
    "nan": "NaN",
    "nifcloud": "Nifcloud",
    "gcp": "Google Cloud Platform",
    "tencentcloud": "Tencent Cloud",
}
    
def get_kics_pac(file_path):
    '''
    Wrapper function for creating pd dataframe
    '''
    # Read CSV as a dataframe
    df = pd.read_csv(file_path)
    
    # Patch DF to common format
    # Tool-ID-Title-Description-IaC-Category-Provider-Severity-Query Document-Related Document
    result = pd.DataFrame()
    for url in df["Query Details"]:
        if url != "-":
            data = parse_kics_doc_page(url)
            temp = pd.DataFrame([data])
            result.join(temp)
    return result.drop_duplicates()

def parse_kics_doc_page(url):
    soup = _get_soup(url)

    result = {}

    # Title
    h1 = soup.find("h1")
    result["Query Name"] = h1.get_text(strip=True) if h1 else None

    # Metadata list items
    li_map = {li.find("strong").get_text(strip=True).rstrip(":"): li for li in soup.select("ul li") if li.find("strong")}

    # Query ID
    result["Query ID"] = li_map.get("Query id", "").get_text(strip=True).split(":")[-1] if "Query id" in li_map else None
    result["Platform"] = li_map.get("Platform", "").get_text(strip=True).split(":")[-1] if "Platform" in li_map else None
    result["Severity"] = li_map.get("Severity", "").get_text(strip=True).split(":")[-1] if "Severity" in li_map else None
    result["Category"] = li_map.get("Category", "").get_text(strip=True).split(":")[-1] if "Category" in li_map else None

    # CWE with link
    if "CWE" in li_map:
        cwe_link = li_map["CWE"].find("a")
        result["CWE"] = cwe_link.get_text(strip=True) if cwe_link else None
        result["CWE Link"] = cwe_link["href"] if cwe_link else None

    # URL with link
    if "URL" in li_map:
        url_link = li_map["URL"].find("a")
        result["Repo URL"] = url_link.get_text(strip=True) if url_link else None
        result["Repo Link"] = url_link["href"] if url_link else None

    # Description
    desc_section = soup.find("h3", id="description")
    if desc_section:
        desc_text = []
        for sibling in desc_section.find_next_siblings():
            if sibling.name == "h3":
                break
            desc_text.append(sibling.get_text(" ", strip=True))
        result["Description"] = " ".join(desc_text)
    
    # Secure/insecure example code
    insecure_blocks = []
    secure_blocks = []

    # 1) Prefer explicit section ids if present
    insecure_header = soup.find(id="code_samples_with_security_vulnerabilities") \
                      or _find_header_by_keywords(soup, ["code samples with security vulnerabilities", "with security vulnerabilities", "with security vulnerability", "code samples with vulnerabilities", "code samples with security"])
    secure_header   = soup.find(id="code_samples_without_security_vulnerabilities") \
                      or _find_header_by_keywords(soup, ["code samples without security vulnerabilities", "without security vulnerabilities", "without security vulnerability", "code samples without security"])

    if insecure_header:
        insecure_blocks.extend(_collect_between(insecure_header))
    if secure_header:
        secure_blocks.extend(_collect_between(secure_header))

    # 2) Fallback: collect all div.highlight under the "Code samples" section and classify by filename
    if not (insecure_blocks or secure_blocks):
        code_samples_header = soup.find(id="code_samples") or _find_header_by_keywords(soup, ["code samples"])
        if code_samples_header:
            # scan following siblings until next major header
            for sib in code_samples_header.find_next_siblings():
                if isinstance(sib, Tag) and sib.name in ("h2", "h3", "h4", "h5"):
                    # stop if we reach another top-level section (but continue if it's a subheader we care about)
                    # continue scanning; code_blocks classification happens on highlight divs below
                    pass
                if isinstance(sib, Tag) and "highlight" in (sib.get("class") or []):
                    fn, code = _extract_from_highlight(sib)
                    low = (fn or "").lower()
                    # classify by filename hints: "Positive" -> insecure, "Negative" -> secure
                    if "positive" in low or "vulnerable" in low or "insecure" in low:
                        insecure_blocks.append((fn, code))
                    elif "negative" in low or "without" in low or "secure" in low:
                        secure_blocks.append((fn, code))
                    else:
                        # unknown: put into insecure (but mark filename if present)
                        insecure_blocks.append((fn, code))

    def join_blocks(blocks):
        if not blocks:
            return None
        out = []
        for i, (fn, code) in enumerate(blocks, start=1):
            header = f"# ---- Code Sample {i} ----"
            if fn:
                header += " -- " + fn
            out.append(header + "\n" + code.strip())
        return "\n\n".join(out)

    insecure_text = join_blocks(insecure_blocks)
    secure_text = join_blocks(secure_blocks)
    result["Insecure Example"] = insecure_text
    result["Secure Example"] = secure_text
    
    return result

def _get_soup(source):
    """Return BeautifulSoup for a URL or raw HTML string."""
    if isinstance(source, str) and source.strip().startswith("<"):
        return BeautifulSoup(source, "html.parser")
    resp = requests.get(source, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def _extract_from_highlight(div):
    """
    Given a <div class="highlight"> block, return (filename, code_text).
    Preserves raw formatting from <pre><code>.
    """
    fn_span = div.find("span", class_="filename")
    filename = fn_span.get_text(strip=True) if fn_span else None

    # Grab the <pre><code> content directly
    pre = div.find("pre")
    if pre:
        code_el = pre.find("code") or pre
        # get_text with strip=False preserves whitespace
        code_text = code_el.get_text(strip=False)
    else:
        code_text = ""

    return filename, code_text.strip()

def _collect_between(header_tag):
    """
    Collect highlight / pre blocks between header_tag and the next header (h2-h5).
    Returns list of (filename, code_text).
    """
    blocks = []
    for sib in header_tag.find_next_siblings():
        if isinstance(sib, Tag) and sib.name in ("h2", "h3", "h4", "h5"):
            break
        if isinstance(sib, Tag):
            classes = sib.get("class", []) or []
            # prefer div.highlight
            if "highlight" in classes:
                fn, code = _extract_from_highlight(sib)
                if code:
                    blocks.append((fn, code))
            # some pages may put code directly in <pre>
            elif sib.name == "pre":
                code = sib.get_text("\n", strip=False).strip()
                if code:
                    blocks.append((None, code))
    return blocks

def _find_header_by_keywords(soup, keywords):
    """Return first header tag (h2-h5) whose text contains any keyword."""
    for tag in soup.find_all(("h2", "h3", "h4", "h5")):
        txt = tag.get_text(" ", strip=True).lower()
        for kw in keywords:
            if kw.lower() in txt:
                return tag
    return None

def extract_code_samples(source):
    """
    Extract code samples from a KICS doc page (URL or HTML).
    Returns (insecure_text, secure_text) strings (or None).
    Each string concatenates multiple samples with dividers:
      # ---- Code Sample 1 ---- -- <filename>
      <code block>
    """
    soup = _get_soup(source)

    insecure_blocks = []
    secure_blocks = []

    # 1) Prefer explicit section ids if present
    insecure_header = soup.find(id="code_samples_with_security_vulnerabilities") \
                      or _find_header_by_keywords(soup, ["code samples with security vulnerabilities", "with security vulnerabilities", "with security vulnerability", "code samples with vulnerabilities", "code samples with security"])
    secure_header   = soup.find(id="code_samples_without_security_vulnerabilities") \
                      or _find_header_by_keywords(soup, ["code samples without security vulnerabilities", "without security vulnerabilities", "without security vulnerability", "code samples without security"])

    if insecure_header:
        insecure_blocks.extend(_collect_between(insecure_header))
    if secure_header:
        secure_blocks.extend(_collect_between(secure_header))

    # 2) Fallback: collect all div.highlight under the "Code samples" section and classify by filename
    if not (insecure_blocks or secure_blocks):
        code_samples_header = soup.find(id="code_samples") or _find_header_by_keywords(soup, ["code samples"])
        if code_samples_header:
            # scan following siblings until next major header
            for sib in code_samples_header.find_next_siblings():
                if isinstance(sib, Tag) and sib.name in ("h2", "h3", "h4", "h5"):
                    # stop if we reach another top-level section (but continue if it's a subheader we care about)
                    # continue scanning; code_blocks classification happens on highlight divs below
                    pass
                if isinstance(sib, Tag) and "highlight" in (sib.get("class") or []):
                    fn, code = _extract_from_highlight(sib)
                    low = (fn or "").lower()
                    # classify by filename hints: "Positive" -> insecure, "Negative" -> secure
                    if "positive" in low or "vulnerable" in low or "insecure" in low:
                        insecure_blocks.append((fn, code))
                    elif "negative" in low or "without" in low or "secure" in low:
                        secure_blocks.append((fn, code))
                    else:
                        # unknown: put into insecure (but mark filename if present)
                        insecure_blocks.append((fn, code))

    def join_blocks(blocks):
        if not blocks:
            return None
        out = []
        for (fn, code) in blocks:
            header = f"# {fn}" if fn else "# Code Sample"
            out.append(header + "\n" + code)
        return "\n\n".join(out)

    insecure_text = join_blocks(insecure_blocks)
    secure_text = join_blocks(secure_blocks)
    return insecure_text, secure_text


if __name__ == '__main__':
    import sys
    import os
    target_dir = os.path.abspath('C:\\Exception\\InProgress\\pac_extract\\src')
    sys.path.append(target_dir)
    from init_setup.setup_integrity import data_init, data_checker, create_ver_token
    from init_setup.setup_base import dir_init, dir_update, get_update_tool_list
    project_root, pac_raw_dir, pac_db_dir, master_db_dir = dir_init()
    version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)
    tool = "KICS/all_queries.csv"
    tool_raw_path = os.path.join(pac_raw_dir, tool)
    df = get_kics_pac(tool_raw_path)
    pd.set_option("display.max_colwidth", 120)
    print(df.head())
    print(df.shape)
    df.to_csv("prisma.csv")



'''
# Example usage
if __name__ == '__main__':
    url = "https://docs.kics.io/latest/queries/ansible-queries/aws/fb5a5df7-6d74-4243-ab82-ff779a958bfd/"
    data = parse_kics_doc_page(url)
    df = pd.DataFrame([data])
    pd.set_option("display.max_colwidth", 120)
    print(df.T)  # transpose to see nicely
'''