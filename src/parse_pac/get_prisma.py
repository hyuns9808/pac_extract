'''
Functions related to getting relevant Prisma Cloud PaCs
'''
import os
import re
import pandas as pd

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


def parse_summary_adoc(filepath):
    """
    Parse summary .adoc into dataframe (Policy | Checkov ID | Severity).
    Returns empty DF if file is only a header.
    """
    rows = []
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    # If file is "empty summary" just return empty df
    if re.fullmatch(r"\s*==.*", text.strip(), flags=re.DOTALL):
        return pd.DataFrame()

    pattern = re.compile(
        r"\|xref:(?P<file>.+?\.adoc)\[(?P<policy>.+?)\]\s*"
        r"\n\|\s*(?P<checkov_url>.+?)\[(?P<checkov_id>CKV_[A-Z_0-9]+)\]\s*"
        r"\n\|(?P<severity>\w+)",
        re.MULTILINE
    )

    for m in pattern.finditer(text):
        rows.append(m.groupdict())

    return pd.DataFrame(rows)


def parse_policy_adoc(filepath):
    """
    Parse details from individual policy .adoc.
    result["Tool"] = ["Terrascan"] * len(df)
    result["ID"] = df["id"]
    result["Title"] = df["description"]
    result["Description"] = pd.Series([pd.NA] * len(df))
    result["IaC"] = ["Terraform"] * len(df)
    result["Category"] =  df["category"]
    result["Provider"] = df["policy_type"].map(id_to_provider)
    result["Severity"] = df["severity"].map(severity_unify)
    result["Query Document"] = pd.Series([pd.NA] * len(df))
    result["Related Document"] = pd.Series([pd.NA] * len(df))
    """
    
    rows = []
    with open(filepath, encoding="utf-8") as f:
        text = f.read()
    
    # First get all frameworks, create each row per framework
    m = re.search(r"Frameworks\s*\|\s*(.+)", text)
    if m:
        frameworks = [fw.strip() for fw in m.group(1).split(",")]
    else:
        frameworks = []
    
    for framework in frameworks:
        row = {}
        row["Tool"] = "Prisma"

        '''
        # Prisma Cloud Policy ID
        m = re.search(r"Prisma Cloud Policy ID\\s*\\|\\s*([a-f0-9\\-]+)", text)
        if m:
            result["PrismaID"] = m.group(1)
        '''
        # Checkov ID
        m = re.search(r"Checkov ID\s*\|\s*(.+)\[(CKV_[A-Z_0-9]+)\]", text)
        if m:
            row["Query Document"] = m.group(1)
            row["ID"] = m.group(2)
        
        # Title
        m = re.search(r"^==\s*(.*)", text)
        if m:
            row["Title"] = m.group(1)
            
        # Description (capture whole section until "=== Fix")
        m = re.search(r"=== Description\s*\n+(.+?)\n=== Fix", text, flags=re.DOTALL)
        if m:
            row["Description"] = m.group(1).strip()

        # Severity
        m = re.search(r"Severity\s*\|\s*(\w+)", text)
        if m:
            if m.group(1) in severity_unify.keys():
                row["Severity"] = severity_unify[m.group(1)]
            else:
                row["Severity"] = m.group(1)

        # IaC: parsed tool from frameworks
        row["IaC"] = framework
        
        # No "Related Document" in Prisma
        row["Related Document"] = pd.NA
        
        '''
        # Subtype
        m = re.search(r"Subtype\\s*\\|\\s*(\\w+)", text)
        if m:
            result["Subtype"] = m.group(1)

        # Fix (everything from "=== Fix" onward)
        m = re.search(r"=== Fix(.+)", text, flags=re.DOTALL)
        if m:
            details["Fix"] = m.group(1).strip()
        '''
        rows.append(row)
    result = pd.DataFrame(rows)
    return result


def get_prisma_pac(rootdir):
    """
    Creates final pandas df for Prisma
    """
    all_records = []

    for dirpath, _, files in os.walk(rootdir):
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
