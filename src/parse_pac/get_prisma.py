'''
Functions related to getting relevant Prisma Cloud PaCs
'''
import os
import pandas as pd
import re
import json

# Correctly parses policy folder name to provider
id_to_provider = {
    "alibaba": "Alibaba Cloud",
    "ansible": "Ansible",
    "api": "API",
    "aws": "AWS",
    "azure": "Azure",
    "docker": "Docker",
    "google-cloud": "Google Cloud Platform",
    "ibm": "IBM Cloud",
    "kubernetes": "Kubernetes",
    "license": "License",
    "oci": "Oracle Cloud Infrastructure",
    "openstack": "OpenStack",
    "panos": "PAN-OS",
    "secrets": "Secrets",
}
# Correctly parses policies with general policy folder name to provider
general_folder_names = [
    "build-integrity",
    "ci-cd-pipeline",
    "sast",
    "secrets",
    "supply-chain"
]


severity_unify = {
    "CRITICAL": "Critical",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low",
    "INFO": "Info"
}

def parse_prisma_checkov(text: str) -> pd.DataFrame:
    """
    Parse Prisma/Checkov policy doc into a DataFrame.
    Get List of Frameworks, find if there are examples related to it.
    Create separate rule per framework within rule if there is an example.
    If not, empty out example and create barebone row.
    Columns:
    ID(Prisma Cloud ID), CheckovID, Title, Severity, Subcategory, Framework(Divide each framework to single row), Description,
    Query Document, Related Document, Insecure Code Example 1
    """
    
    def grab(pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else None

    # Metadata
    title = grab(r'^\s*(?:==\s*)([^\n]*)')
    prisma_id = grab(r'Prisma Cloud Policy ID\s*\|\s*(.+)')
    query_document = grab(r'Checkov ID\s*\|\s*(.*)\[.+\]')
    checkov_id = grab(r'Checkov(?: Check)? ID\s*\|\s*(?:[^\[\n]*\[)?([A-Z0-9_]+)(?:\])?')
    severity = grab(r'Severity\s*\|\s*(.+)')
    subtype = grab(r'Subtype\s*\|\s*(.+)')

    # Description
    desc_m = re.search(r'Description\s+([\s\S]*?)(?=[/=])',
                       text, re.MULTILINE | re.IGNORECASE)
    description = desc_m.group(1).strip() if desc_m else None

    # Fix section
    # Ignore "Fix - Runtime"; CLI fixes, not relevant
    fix_total_block = re.search(r'Fix - Buildtime[\s\S]*(\*[\s\S]*)', text, re.IGNORECASE)
    records = []

    def clean(s):
        if s is None:
            return pd.NA
        return re.sub(r'^\s*\*+\s*', '', s, flags=re.MULTILINE).strip()
    
    if fix_total_block:
        fix_text = fix_total_block.group(0)
        framework_sections = re.split(r"\*(\w+)\*", fix_text)

        for i in range(1, len(framework_sections), 2):
            framework = framework_sections[i]
            body = framework_sections[i+1]

            '''
            # Resource and Argument
            # Removed for better unification between other open-source tools, enable if necessary
            resource = re.search(r"\* *Resource:\* *([^\n]+)", body)
            argument = re.search(r"\* *Argument:\* *([^\n]+)", body)
            '''
            
            # Code block(s)
            code_blocks = re.findall(r"(\[[^*]*)", body, re.S)
            code_final = [code.strip() for code in code_blocks]

            # Create row per framework
            '''
            # Removed for better unification between other open-source tools, enable if necessary
            "Resource": resource.group(1) if resource else None,
            "Argument": argument.group(1) if argument else None,
            '''
            records.append({
                "Open-source Tool": "Prisma",
                "ID": clean(prisma_id),
                "CheckovID": clean(checkov_id),
                "Title": clean(title),
                "Severity": severity_unify[clean(severity)] if clean(severity) in severity_unify.keys() else clean(severity),
                "Subcategory": clean(subtype),
                "IaC Framework": clean(framework),
                "Description": clean(description),
                "Query Document": clean(query_document),
                "Insecure Code Example 1": json.dumps([code_final]) if len(code_final) != 0 else pd.NA
            })

    return pd.DataFrame(records)

def parse_policy_adoc(filepath):
    """Decide parser based on content."""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    # If file is "empty summary" just return empty df
    lines = text.splitlines()
    if len(lines) == 1 and lines[0].startswith("=="):
        return pd.DataFrame()
    else:
        return parse_prisma_checkov(text)
    
def get_prisma_pac(rootdir):
    """
    Creates final pandas df for Prisma
    """
    all_records = []

    for dirpath, _, files in os.walk(rootdir):
        dirname = os.path.basename(dirpath)
        summary_file = f"{dirname}.adoc"

        detail_records = []
        for f in files:
            if f.endswith(".adoc") and f != summary_file:
                filepath = os.path.join(dirpath, f)
                parsed = parse_policy_adoc(filepath)
                # parse_policy_adoc returns a DataFrame, extract dict(s)
                if isinstance(parsed, pd.DataFrame):
                    detail_records.extend(parsed.to_dict(orient="records"))
                else:
                    # fallback in case parse_policy_adoc returns dict
                    detail_records.append(parsed)

        if not detail_records:
            continue

        result = pd.DataFrame(detail_records)

        # Add Category
        relpath = os.path.relpath(dirpath, rootdir)
        parts = relpath.split(os.sep)
        def clean_name(name):
            if not name:
                return None
            return name.replace("-policies", "")

        parent_folder_name = clean_name(parts[0]) if len(parts) > 0 else None

        # Check if parent folder needs to use subfolder name as Category
        if parent_folder_name in general_folder_names:
            category = clean_name(parts[1]) if len(parts) > 1 else None
            result["Category"] = id_to_provider[category] if category in id_to_provider.keys() else category 
        else:
            category = clean_name(parts[1]) if len(parts) > 1 else None
            result["Category"] = id_to_provider[category] if category in id_to_provider.keys() else category

        all_records.append(result)

    if all_records:
        return pd.concat(all_records, ignore_index=True)
    else:
        return pd.DataFrame()

'''
# Use for single dataset clone unit testing
if __name__ == "__main__":
    import sys
    import os
    # Add target dir here
    # target_dir = 
    sys.path.append(target_dir)
    from init_setup.setup_integrity import data_init, data_checker, create_ver_token
    from init_setup.setup_base import dir_init, dir_update, get_update_tool_list
    project_root, pac_raw_dir, pac_db_dir, master_db_dir = dir_init()
    version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)
    tool = "Prisma"
    tool_raw_path = os.path.join(pac_raw_dir, tool)
    print(tool_raw_path)
    df = get_prisma_pac(tool_raw_path)
    pd.set_option("display.max_colwidth", 120)
    print(df.head())
    print(df.shape)
    df.to_csv("prisma.csv")
'''