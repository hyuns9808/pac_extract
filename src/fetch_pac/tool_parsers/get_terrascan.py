'''
Functions related to getting relevant Terrascan PaCs
'''
import os
import json
import pandas as pd

# Change file path of md if necessary
folder_path = "data\\Terrascan\\rego"
# Correctly parses code into provider name
# ['aws' 'azure' 'docker' 'gcp' 'github' 'k8s']
id_to_provider = {
    "aws": "AWS",
    "azure": "Azure",
    "docker": "Docker",
    "gcp": "Google Cloud Platform",
    "github": "GitHub Configuration",
    "k8s": "Kubernetes"
}

def get_terrascan_pac(folder_path=folder_path):
    '''
    Creates final pandas df for Terrascan
    '''
    records = []
    for root, dirs, files in os.walk(folder_path):
        folder_name = os.path.basename(root)
        for file in files:
            if file.endswith('.json'):
                folder_path = os.path.join(root, file)
                try:
                    with open(folder_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Extract desired fields; here extracting all top-level keys, adding folder name
                    record = data.copy()
                    record['folder_name'] = folder_name
                    records.append(record)
                except Exception as e:
                    print(f"Failed to parse {folder_path}: {e}")
    # Create temporary dataframe
    df = pd.DataFrame(records)
    # Patch DF to common format
    # Index(['name', 'file', 'policy_type', 'resource_type', 'template_args',       
    #   'severity', 'description', 'reference_id', 'category', 'version', 'id',
    #   'folder_name'],
    # Tool-ID-Description-IaC-Provider-Severity-Query Document-Related Document
    result = pd.DataFrame()
    result["Tool"] = ["Terrascan"] * len(df)
    result["ID"] = df["reference_id"]
    result["Description"] = df["description"]
    result["IaC"] = ["Terraform"] * len(df)
    result["Provider"] = df["policy_type"].map(id_to_provider)
    result["Severity"] = df["severity"]
    result["Query Document"] = "NaN"
    result["Related Document"] = "NaN"
    
    return result

def filter_policies(df, partial_id, iac_type, keyword):
    '''
    Returns dataframe that consists of partial id, iac type and keyword match
    '''
    keyword = keyword.lower()
    return df[
        df['Id'].str.contains(partial_id, case=False, na=False) &
        df['IaC'].str.lower().eq(iac_type.lower()) &
        (
            df['Entity'].str.lower().str.contains(keyword, na=False) |
            df['Policy'].str.lower().str.contains(keyword, na=False)
        )
    ]

'''
if __name__ == '__main__':
    df = get_terrascan_pac()
    print(df)
'''