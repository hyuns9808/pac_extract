'''
Functions related to getting relevant Terrascan PaCs
'''
import os
import json
import pandas as pd

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
severity_unify = {
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low"
}

def get_terrascan_pac(folder_path):
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
    # Tool-ID-Title-Description-IaC-Category-Provider-Severity-Query Document-Related Document
    result = pd.DataFrame()
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
    
    return result.drop_duplicates()

'''
if __name__ == '__main__':
    df = get_terrascan_pac()
    print(df)
'''