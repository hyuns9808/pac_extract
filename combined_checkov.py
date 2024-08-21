import sys
import re
import requests
import os
import xlsxwriter
import zipfile
from io import BytesIO

# COMMON VARIABLES AND PATTERNS
# CHANGE TOOLNAME ACCORDINGLY TO LOOKUP TOOL!
toolName = "checkov"
owner = "bridgecrewio"
repo = "checkov"
# URL of rootmd. Change if necessary.
rootURL = "https://raw.githubusercontent.com/bridgecrewio/checkov/main/docs/5.Policy%20Index/terraform.md"
# Regular expression used to sort policies
policy_pattern = re.compile(
    r'\|\s*\d+\s*\|\s*(CKV[2]?_AWS_\d+)\s*\|\s*resource\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*Terraform\s*\|\s*\[([^\]]+)\]\(([^)]+)\)'
)

# FUNCTIONS
# Get rootmd file of tool.
def fetch_markdown_content():
    response = requests.get(rootURL)
    return response.text

# Download repo of given tool
# Owner, repo divided for use in different tools
def download_and_extract_repo(owner, repo, path):
    url = f'https://github.com/{owner}/{repo}/archive/refs/heads/master.zip'
    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            z.extractall(path=path)
            print(f"Repository '{repo}' downloaded and extracted to - {path}")
    else:
        print(f"Failed to download repository: {response.status_code}")

# Get policies from policyData, finds exact word match of targetString and appends to resultList
def process_policies(policyData, targetString, policyList):
    for policy in policyData:
        code_name, resource_name, description, file_name, link = policy
        combined_text = f"{code_name} {resource_name} {description} {file_name} {link}".lower()
        if re.search(r'\b' + targetString + r'\b', combined_text):
            policyList.append({
                'code_name': code_name.strip(),
                'resource_name': resource_name.strip(),
                'description': description.strip(),
                'file_name': file_name.strip(),
                'link': link.strip()
            })

# Get policies from policyData, writes into givenWorksheet
def write_policies_to_worksheet(givenWorksheet, policyData):
    row = 1
    for policy in policyData:
        givenWorksheet.write(row, 0, policy['code_name'])
        givenWorksheet.write(row, 1, policy['resource_name'])
        givenWorksheet.write(row, 2, policy['description'])
        givenWorksheet.write(row, 3, policy['file_name'])
        givenWorksheet.write(row, 4, policy['link'])
        row += 1


# Create "toolName_targetString.xlsx" file and write policies extracted from policyList
def write_to_excel(policyList, toolName, targetString, path):
    if not os.path.exists(f'{path}\\{findcatOrg}'):
        os.makedirs(f'{path}\\{findcatOrg}')
    try:
        excelName = toolName.lower() + '_' + targetString + '.xlsx'
        workbook = xlsxwriter.Workbook(f'{path}\\{findcatOrg}\\{excelName}')
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})

        headers = ['Code', 'Resource', 'Description', 'File Name', 'Link']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)
        
        write_policies_to_worksheet(worksheet, policyList)
        
        worksheet.autofit()
        workbook.close()
        print(f"\nData written to - '{toolName.lower()}_{targetString}.xlsx'.\nPlease check - '{excelName}'")
    except xlsxwriter.exceptions.FileCreateError:
        print('-' * 80)
        print("Oops, an error occurred! You probably forgot to close the excel file before running the program :/")
        print("Please close the excel file and try again!")

# START OF MAIN CODE
# Input header
input_args = sys.argv[1:]
# Lookup string
findcatOrg = input_args[0]
# Path of ROOT folder that contains both 'tools' and 'result'
rootPath = input_args[1]
# Path of initial tool folder
toolFolder = os.path.join(rootPath, "tools")
# Path of initial result folder
resultFolder = os.path.join(rootPath, "result")
findcat = findcatOrg.lower()

# First, get tool 
print(f"Getting {toolName.upper()} files...")
download_and_extract_repo(owner, repo, toolFolder)

print(f"Extracting from CHECKOV...")

# Get md file data from URL
md_content = fetch_markdown_content()

# Find all policies in the md_content
policies = policy_pattern.findall(md_content)

# Extracted data
extracted_data = []
process_policies(policies, findcat, extracted_data)

# Create XLSX file accordingly
if not extracted_data:
    print(f"No policies found related to {findcatOrg}. Double-check the service you want to look up, and try again!")
else:
    write_to_excel(extracted_data, toolName, findcatOrg, resultFolder)

'''
# CODE FOR CSV FILE
# If you need to use a CSV instead of a xlsx file, use this portion!
# Define the CSV file name
csv_file_name = toolName + '_' + findcatOrg + '.csv'

# Write the extracted data to a CSV file
with open(csv_file_name, mode='w', newline='') as csv_file:
    fieldnames = ['code_name', 'resource_name', 'description', 'file_name', 'link']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
    writer.writeheader()
    for data in extracted_data:
        writer.writerow(data)

print(f"Data written to {csv_file_name}.\nPlease check - " + newPath + f"\\{csv_file_name}")
'''