'''
Functions related to getting relevant Checkov PaCs
'''
import pandas as pd
import re

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
    "GITLABCI": 
}


# May fix to use more service-specific md files
def get_checkov_pac():
    df = load_md_table("data\Checkov\\5.Policy Index\\all.md")
    return df
    
def load_md_table(filepath):
    # Read markdown table as raw text and manually parse
    with open(filepath, 'r', encoding='utf-8') as f:
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
    result = pd.DataFrame(data, columns=headers)
    # Patch DF to common format
    result['Tool'] = 'Checkov'
    return result

def filter_policies(df, partial_id, iac_type, keyword):
    keyword = keyword.lower()
    return df[
        df['Id'].str.contains(partial_id, case=False, na=False) &
        df['IaC'].str.lower().eq(iac_type.lower()) &
        (
            df['Entity'].str.lower().str.contains(keyword, na=False) |
            df['Policy'].str.lower().str.contains(keyword, na=False)
        )
    ]

if __name__ == '__main__':
    df = get_checkov_pac()
    print(df)
    name_ptn = r"([^_]+)_([^_]+)_([^_]+)"
    df_extracted = df["Id"].str.extract(name_ptn)[1]
    df_unique = df_extracted.drop_duplicates().reset_index(drop=True)
    print(df_unique)
    print(df_extracted.dtype)