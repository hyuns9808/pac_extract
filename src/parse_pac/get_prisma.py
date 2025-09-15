'''
Functions related to getting relevant Prisma Cloud PaCs
'''
import os
import pandas as pd
import re
import yaml

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
    PolicyID, CheckovID, Severity, Subtype, Frameworks, Description,
    Example_Framework, Resource, Arguments, Solution, Code_example, Code_description
    """
    
    def grab(pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else None

    # Metadata
    title = grab(r'^==\s*(.+)')
    policy_id = grab(r'Prisma Cloud Policy ID\s*\|\s*(.+)')
    query_document = grab(r'Checkov ID\s*\|\s*(.*)\[.+\]')
    checkov_id = grab(r'Checkov ID\s*\|\s*.*\[(.+)\]')
    severity = grab(r'Severity\s*\|\s*(.+)')
    subtype = grab(r'Subtype\s*\|\s*(.+)')
    frameworks_full = grab(r'Frameworks\s*\|\s*(.+)')

    # Description
    desc_m = re.search(r'\#\#\#\s*Description\s+([\s\S]*?)(?\#^\#\#\#\s*Fix - Buildtime|\Z)',
                       text, re.MULTILINE | re.IGNORECASE)
    description = desc_m.group(1).strip() if desc_m else None

    # Fix section
    fix_m = re.search(r'\#\#\#\s*Fix - Buildtime\s*([\s\S]*)', text, re.IGNORECASE)
    records = []

    def clean(s):
        if s is None:
            return None
        return re.sub(r'^\s*\*+\s*', '', s, flags=re.MULTILINE).strip()

    if fix_m:
        fix_text = fix_m.group(1)

        # Split framework blocks (*Terraform*, *Ansible*, *Docker*, etc.)
        framework_blocks = re.findall(
            r'\*\s*([^\*]+?)\s*\*\s*([\s\S]*?)(?=(?:\*\s*[^\*]+?\s*\*\s*)|$)',
            fix_text, flags=re.IGNORECASE
        )

        for fw_name, block in framework_blocks:
            fw_name = fw_name.strip()
            block = block.strip()

            # Resource / Module
            res_m = re.search(r'^\s*(?:\*+\s*)?(?:Resource|Module)\s*:\s*(.+)', block, re.MULTILINE | re.IGNORECASE)
            resource = res_m.group(1).strip() if res_m else None

            # Arguments / Attribute
            arg_m = re.search(r'^\s*(?:\*+\s*)?(?:Arguments|Attribute)\s*:\s*(.+)', block, re.MULTILINE | re.IGNORECASE)
            arguments = arg_m.group(1).strip() if arg_m else None

            # Find first code block
            code_m = re.search(r'\[source[^\]]*\]\s*----\s*([\s\S]*?)\s*----', block)
            if code_m:
                code_example = code_m.group(1).strip()
                code_start = code_m.start()
                code_end = code_m.end()
                # Solution is everything before code block, excluding Resource/Arguments lines
                solution_text = block[:code_start]
                if arg_m:
                    # Need fix this part
                    # remove Arguments/Attribute line
                    solution_text = re.sub(
                        r'^\s*(?:\*+\s*)?(?:Arguments|Attribute)\s*:\s*.+', '', solution_text,
                        flags=re.MULTILINE|re.IGNORECASE
                    )
                if res_m:
                    solution_text = re.sub(
                        r'^\s*(?:\*+\s*)?(?:Resource|Module)\s*:\s*.+', '', solution_text,
                        flags=re.MULTILINE|re.IGNORECASE
                    )
                solution = solution_text.strip() if solution_text.strip() else None
                # Code description: any text after code block
                code_description_text = block[code_end:].strip()
                code_description = code_description_text if code_description_text else None
            else:
                # No code block: all remaining text is solution
                solution = block.strip() if block.strip() else None
                code_example = None
                code_description = None

            records.append({
                "Open-source Tool": "Prisma",
                "ID": clean(checkov_id),
                "Title": clean(title),
                "Severity": clean(severity),
                "Category": clean(subtype),
                "Frameworks": clean(frameworks_full),
                "Description": clean(description),
                "Query Document": clean(query_document),
                "Example_Framework": clean(fw_name),
                "Resource": clean(resource),
                "Arguments": clean(arguments),
                "Solution": clean(solution),
                "Secure Code Example 1": clean(code_example),
                "Code_description": clean(code_description)
            })
    else:
        # No fix section
        records.append({
            "Open-source Tool": "Prisma",
            "ID": clean(policy_id),
            "Title": clean(title),
            "Severity": clean(severity),
            "Category": clean(subtype),
            "Frameworks": clean(frameworks_meta),
            "Description": clean(description),
            "Example_Framework": None,
            "Resource": None,
            "Arguments": None,
            "Solution": None,
            "Code_example": None,
            "Code_description": None
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
    if "Prisma Cloud Policy ID" in text:   # Prisma/Checkov style
        return parse_prisma_checkov(text)
    else:
        return pd.DataFrame([{"raw_text": text}])
    
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
                print(filepath)
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

        # Add Provider + Category
        relpath = os.path.relpath(dirpath, rootdir)
        parts = relpath.split(os.sep)
        def clean_name(name):
            if not name:
                return None
            return name.replace("-policies", "")

        parent_folder_name = clean_name(parts[0]) if len(parts) > 0 else None

        # Check if parent folder needs to use subfolder name as provider
        if parent_folder_name in general_folder_names:
            provider = clean_name(parts[1]) if len(parts) > 1 else None
            result["Provider"] = provider
            result["Category"] = provider
        else:
            # Map straight to provider
            if parent_folder_name in id_to_provider.keys():
                result["Provider"] = id_to_provider[parent_folder_name]
            else:
                result["Provider"] = parent_folder_name
            result["Category"] = clean_name(parts[1]) if len(parts) > 1 else None

        all_records.append(result)

    if all_records:
        return pd.concat(all_records, ignore_index=True)
    else:
        return pd.DataFrame()


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
    tool = "Prisma"
    tool_raw_path = os.path.join(pac_raw_dir, tool)
    print(tool_raw_path)
    df = get_prisma_pac(tool_raw_path)
    pd.set_option("display.max_colwidth", 120)
    print(df.head())
    print(df.shape)
    df.to_csv("prisma.csv")
