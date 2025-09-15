'''
Functions related to getting relevant Trivy PaCs
'''
import os
import yaml
import pandas as pd
import numpy as np

# Correctly parses code into provider name
# ['aws' 'azure' 'cloudstack' 'digitalocean' 'github' 'google' 'kubernetes'
# 'nifcloud' 'openstack' 'oracle' '']
id_to_provider = {
    "aws": "AWS",
    "azure": "Azure",
    "cloudstack": "CloudStack",
    "digitalocean": "DigitalOcean",
    "docker": "Docker",
    "github": "GitHub",
    "google": "Google Cloud Platform",
    "kubernetes": "Kubernetes",
    "nifcloud": "Nifcloud",
    "openstack": "OpenStack",
    "oracle": "Oracle Cloud Infrastructure",
    'NaN': "NaN"
}
severity_unify = {
    "CRITICAL": "Critical",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low"
}

def extract_metadata_from_rego(filepath):
    '''
    Gets comment section from all rego files and combines them into a .yaml file for better parsing
    '''
    metadata_lines = []
    in_metadata = False
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()

            # Detect start of metadata block
            if not in_metadata:
                if stripped.lower() == "metadata" or stripped.lower() == "# metadata":
                    in_metadata = True
                    continue
                elif stripped.startswith("#"):
                    in_metadata = True
                else:
                    # No metadata block
                    break

            if in_metadata:
                # Stop if line looks like start of rego code (e.g. package, import, or empty)
                if stripped == "" or stripped.startswith("package") or stripped.startswith("import"):
                    break

                # Remove leading '#' if present
                if stripped.startswith("#"):
                    cleaned = line.lstrip('#').rstrip('\n')
                else:
                    cleaned = line.rstrip('\n')

                metadata_lines.append(cleaned)

    if not metadata_lines:
        return None

    yaml_str = '\n'.join(metadata_lines)
    try:
        metadata = yaml.safe_load(yaml_str)
        return metadata
    except Exception as e:
        print(f"YAML parse error in {filepath}: {e}")
        print("Problematic YAML snippet:")
        print(yaml_str)
        return None

def extract_fields(metadata, filepath):
    '''
    Parse resulting .yaml file for metadata
    '''
    if metadata is None:
        return None

    # Safely get nested fields with defaults
    title = metadata.get('title')
    if title == '': title = "NaN"
    description = metadata.get('description')
    if description == '': description = "NaN"
    related_resources = metadata.get('related_resources')
    if related_resources == '': related_resources = "NaN"
    if isinstance(related_resources, list):
        related_resources = ", ".join(map(str, related_resources))
    input_data = metadata.get('custom', {}).get('input', {})
    type_value = None
    provider_value = None
    if isinstance(input_data, dict):
        selector = input_data.get('selector', [])
        if selector and isinstance(selector, list):
            type_value = selector[0].get('type')
            subtypes = selector[0].get('subtypes', [])
            if subtypes and isinstance(subtypes, list):
                provider_value = subtypes[0].get('provider')
    if type_value is None: type_value = "NaN"
    if provider_value is None: provider_value = "NaN"
    
    # Docker and Kubernetes specific; change values accordingly
    if type_value == "dockerfile":
        type_value = "container"
        provider_value = "docker"
    if type_value == "kubernetes":
        type_value = "orch"
        provider_value = "kubernetes"
    custom = metadata.get('custom', {})

    # Patch DF to common format
    # {'severity', 'id', 'deprecated', 'minimum_trivy_version', 'input', 'short_code', 'long_id', 'service',
    # 'examples', 'recommended_action', 'frameworks', 'provider', 'recommended_actions', 'aliases'}
    # Tool-ID-Title-Description-IaC-Category-Provider-Severity-Query Document-Related Document
    return {
        "Open-source Tool": "Trivy",
        "ID": custom.get('id', ""),
        "Title": title,
        "Description": description,
        "IaC": "Multiple",
        "Category": np.nan,
        "Provider": id_to_provider[provider_value],
        "Severity": severity_unify[custom.get('severity', "")],
        "Query Document": np.nan,
        "Related Document": related_resources
    }

def get_trivy_pac(folder_path):
    '''
    Combined final parser for Trivy PaC files
    '''
    records = []
    for dirpath, _, filenames in os.walk(folder_path):
        for file in filenames:
            if not file.endswith('.rego'):
                continue
            # Exclude test.rego files
            if file.endswith('_test.rego'):
                continue
            filepath = os.path.join(dirpath, file)
            metadata = extract_metadata_from_rego(filepath)
            record = extract_fields(metadata, filepath)
            if record:
                records.append(record)
    return pd.DataFrame(records).drop_duplicates()

'''
if __name__ == '__main__':
    df = get_trivy_pac()
    df.to_csv("trivy.csv")
'''