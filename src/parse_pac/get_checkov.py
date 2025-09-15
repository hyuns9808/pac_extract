'''
Functions related to getting relevant Checkov PaCs
'''
import pandas as pd

# Correctly parses code into provider name
id_to_provider = {
    "ADO": "Azure DevOps",
    "ALI": "Alibaba Cloud",
    "ANSIBLE": "Ansible",
    "ARGO": "argo",
    "AWS": "AWS",
    "AZURE": "Azure",
    "AZUREPIPELINES": "Azure Pipelines",
    "BCW": "Bridgecrew Cloud",
    "BITBUCKET": "Bitbucket",
    "BITBUCKETPIPELINES": "Bitbucket Pipelines",
    "CIRCLECIPIPELINES": "CircleCI Pipelines",
    "DIO": "DigitalOcean",
    "DOCKER": "Docker",
    "GCP": "Google Cloud Platform",
    "GHA": "GitHub Actions",
    "GIT": "GitHub",
    "GITHUB": "GitHub Configuration",
    "GITLAB": "GitLab",
    "GITLABCI": "GitLab CI",
    "GLB": "GitLab Branch",
    "IBM": "IBM Cloud",
    "K8S": "Kubernetes",
    "LIN": "Linode",
    "NCP": "Naver Cloud",
    "OCI": "Oracle Cloud Infrastructure",
    "OPENAPI": "OpenAPI",
    "OPENSTACK": "OpenStack",
    "PAN": "PAN-OS",
    "SECRET": "Secrets",
    "TC": "Tencent Cloud",
    "TF": "Terraform",
    "YC": "Yandex Cloud"
}
    
def get_checkov_pac(file_path):
    '''
    Creates final pandas df for Checkov
    '''
    # Read markdown table as raw text and manually parse
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Strip lines and ignore separators
    lines = [line.strip() for line in lines if line.strip() and line.startswith('|')]
    # Parse header
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    # Parse rows
    data = []
    for line in lines[2:]:
        row = [cell.strip() for cell in line.split('|')[1:-1]]
        data.append(row)
    df = pd.DataFrame(data, columns=headers)
    # Patch DF to common format
    # Tool-ID-Title-Description-IaC-Category-Provider-Severity-Query Document-Related Document
    result = pd.DataFrame()
    result["Open-source Tool"] = ["Checkov"] * len(df)
    result["ID"] = df["Id"]
    result["Title"] = df["Policy"]
    result["Description"] = pd.Series([pd.NA] * len(df))
    result["IaC"] = df["IaC"]
    result["Category"] = pd.Series([pd.NA] * len(df))
    name_ptn = r"([^_]+)_([^_]+)_([^_]+)"
    result["Provider"] = df["Id"].str.extract(name_ptn)[1].map(id_to_provider)
    result["Severity"] = pd.Series([pd.NA] * len(df))
    result["Query Document"] = df["Resource Link"]
    result["Related Document"] = pd.Series([pd.NA] * len(df))
    return result.drop_duplicates()

'''
# Use for single dataset clone unit testing
if __name__ == "__main__":
    import sys
    import os
    target_dir = os.path.abspath('C:\Exception\InProgress\pac_extract\src')
    sys.path.append(target_dir)
    from init_setup.setup_integrity import data_init, data_checker, create_ver_token
    from init_setup.setup_base import dir_init, dir_update, get_update_tool_list
    project_root, pac_raw_dir, pac_db_dir, master_db_dir = dir_init()
    version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)
    tool = "Checkov"
    tool_raw_path = os.path.join(os.path.join(pac_raw_dir, tool), '5.Policy Index/all.md')
    df = get_checkov_pac(tool_raw_path)
    pd.set_option("display.max_colwidth", 120)
    print(df.head())
    print(df.shape)
'''