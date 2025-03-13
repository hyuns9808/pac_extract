# Enable when writing data into CSV
# import csv
import sys
import re
import requests
import os
import xlsxwriter
import zipfile
from io import BytesIO

# COMMON VARIABLES
# CHANGE TOOLNAME ACCORDINGLY TO LOOKUP TOOL!
toolName = "tfsec"
owner = "aquasecurity"
repo = "tfsec"
# URL of rootmd INDEX.md file for AWS ONLY!
rootURL = "https://raw.githubusercontent.com/aquasecurity/tfsec/master/docs/checks/aws/index.md"
# Base root string used for creating specific URLs per check
rootString = "https://raw.githubusercontent.com/aquasecurity/tfsec/master/docs/checks/aws"

# PATTERNS
# Pattern to find policies
title_pattern = re.compile(
    r'title: (.+?)\n\-\-\-'
)
# Pattern to find folder names within md file
folder_pattern = re.compile(
    r'\[(.+?)\]'
)
# Pattern to find links within link data block
link_pattern = re.compile(
    r'\[.+?]\((https?://[^\)]+)\)'
)
# Pattern to construct code name via completed policy URL
# https://raw.githubusercontent.com/aquasecurity/tfsec/master/docs/checks/aws/rds/enable-performance-insights/index.md
name_pattern = re.compile(
    r'.+?checks/(.+?)/index.md'
)
# Regular expression to find content within md file
# Gets: title, default severity, explanation,
# Possible impact, Suggested resolution,
# Insecure example, Secure example,
# and links as a whole block
policy_pattern = re.compile(
    r'\#\s*([^#]+?)\s*'
    r'\#\#\# Default Severity: <span class="severity .+?"\>([^\>]+?)\s*\<\/span>\s*'
    r'\#\#\# Explanation\s*([^#]+?)\s*'
    r'\#\#\# Possible Impact\s*([^#]+?)\s*'
    r'\#\#\# Suggested Resolution\s*([^#]+?)\s*'
    r'\#\#\# Insecure Example\s*\n.*\n.*terraform\s*([\S\s]*)```\s*'
    r'\#\#\# Secure Example\s*\n.*\n.*terraform\s*([\S\s]*)```\s*'
    r'\#\#\# Links([\S\s]*)$'
)

# HELPER FUNCTIONS
# Call when trying to get everything from TFSEC
def fetchAll(resultList):
    serviceList = get_folders_from_url(rootURL)
    urls = []
    for service in serviceList:
        serviceURL = rootString + '/' + service
        add_urls_from_folder(serviceURL, urls)
        get_policy_from_folder(service, resultList)

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

# Function that translates English severity to Korean
def korSeverity(engSeverity):
    if engSeverity == "low":
        return "낮음(LOW)"
    elif engSeverity == "medium":
        return "중간(MEDIUM)"
    elif engSeverity == "high":
        return "높음(HIGH)"
    elif engSeverity == "critical":
        return "매우높음(CRITICAL)"
    else:
        return "뭐야이건"

# Get md content as text
def fetch_markdown_content(inputURL):
    response = requests.get(inputURL)
    return response.text

# Get supporting services name from rootURL and store in serviceList
def get_folders_from_url(targetURL):
    url_md_content = fetch_markdown_content(targetURL)
    return folder_pattern.findall(url_md_content)

# Create list of urls for all policies within specific folder
def add_urls_from_folder(folderURL, resultList):
    policies = folder_pattern.findall(fetch_markdown_content(folderURL + '/index.md')) 
    for policy in policies:
        resultList.append(folderURL + '/' + policy + '/index.md')
    
# Search all policies provided that includes targetString
# result should be list of policies that are
# parsed correctly[('ruleCode': '', 'severity': '', ...)]
def search_all_policies(targetString, serviceList, resultList):
    for service in serviceList:
        get_matching_policy_from_folder(service, targetString, resultList)


# Get all policies within folder
# result should be list of policies that are
# parsed correctly[('ruleCode': '', 'severity': '', ...)]
def get_policy_from_folder(serviceName, resultList):
    policiesURL = []
    # first get all policies within folder
    serviceURL = rootString + '/' + serviceName
    add_urls_from_folder(serviceURL, policiesURL)
    for policyURL in policiesURL:
        # get policies; remember link comes as a whole
        policy = policy_pattern.findall(fetch_markdown_content(policyURL))
        process_policies(policy, policyURL, resultList)
    

# Get all policies that contain targetString in title within folder
# result should be list of policies that are
# parsed correctly[('ruleCode': '', 'severity': '', ...)]
def get_matching_policy_from_folder(serviceName, targetString, resultList):
    policiesURL = []
    # first get all policies within folder
    serviceURL = rootString + '/' + serviceName
    print("Looking up folder \'" + serviceName + "\'...")
    add_urls_from_folder(serviceURL, policiesURL)
    for policyURL in policiesURL:
        policy = policy_pattern.findall(fetch_markdown_content(policyURL))
        # Look for target string ONLY in title of policy to save runtime
        if re.search(r'\b' + targetString + r'\b', policy[0][0]):
            print("\tMatching policy found! - " + policyURL)
            process_policies(policy, policyURL, resultList)
    print("")

# Get policies from policyData, finds exact word match of targetString and appends to resultList
# Gets: title, default severity, explanation,
# Possible impact, Suggested resolution,
# Insecure example, Secure example,
# and links as a whole block
def process_policies(policyData, policyURL, resultList):
    title, severity, explanation, pos_imp, sug_res, insec_ex, sec_ex, linkData = policyData[0]
    linkList = link_pattern.findall(linkData)
    ruleCode = name_pattern.findall(policyURL)[0].replace('/','-')
    # Replace severity to Korean, if code breaks, ERASE THIS LINE
    severity = korSeverity(severity.lower())
    resultList.append({
            'ruleCode': ruleCode,
            'severity': severity.strip(),
            'title': title.strip().replace('/n', '/r/n').replace('\t', '    '),
            'explanation': explanation.strip(),
            'pos_imp': pos_imp.strip(),
            'sug_res': sug_res.strip(),
            'insec_ex': insec_ex.strip().replace('/n', '/r/n').replace('\t', '    '),
            'sec_ex': sec_ex.strip().replace('/n', '/r/n').replace('\t', '    '),
            'url': policyURL,
            'linkList': linkList
        })

# Get policies from policyData, writes into givenWorksheet with given specified vale
def write_policies_to_worksheet(givenWorksheet, policyData, format):
    row = 1
    for policy in policyData:
        givenWorksheet.write(row, 0, policy['ruleCode'].replace('\n', ''), format)
        givenWorksheet.write(row, 1, policy['severity'].replace('\n', ''), format)
        givenWorksheet.write(row, 2, policy['title'].replace('\n', ''), format)
        givenWorksheet.write(row, 3, policy['explanation'].replace('\n', ''), format)
        givenWorksheet.write(row, 4, policy['pos_imp'].replace('\n', ''), format)
        givenWorksheet.write(row, 5, policy['sug_res'].replace('\n', ''), format)
        givenWorksheet.write(row, 6, policy['insec_ex'], format)
        givenWorksheet.write(row, 7, policy['sec_ex'], format)
        givenWorksheet.write(row, 8, policy['url'].replace('\n', ''), format)

        linkString = ""
        for link in policy['linkList']:
            linkString += (link + '\n')
        givenWorksheet.write(row, 9, linkString, format)
        row += 1

# Create "toolName_targetString.xlsx" file and write policies extracted from policyList
def write_to_excel(policyList, toolName, targetString, path):
    print(f"\n{toolName.upper()} SUMMARY:")
    print(f"\n{toolName.upper()} TOTAL POLICIES: {len(policyList)}")
    if not os.path.exists(f'{path}\\{findcatOrg}'):
        os.makedirs(f'{path}\\{findcatOrg}')
    try:
        excelName = toolName.lower() + '_' + targetString + '.xlsx'
        workbook = xlsxwriter.Workbook(f'{path}\\{findcatOrg}\\{excelName}')
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        wrapText = workbook.add_format({'text_wrap': True})

        headers = ['Rule Code', 'Severity', 'Title', 'Explanation', 'Possible Impact', 'Suggested Resolution', 'Insecure Example', 'Secure Example', 'Policy URL', 'Links']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)

        write_policies_to_worksheet(worksheet, policyList, wrapText)
        worksheet.autofit()
        workbook.close()
        print(f"\nData written to - '{toolName.lower()}_{targetString}.xlsx'.\nPlease check - '{excelName}'")
    except xlsxwriter.exceptions.FileCreateError:
        print("Oops, an error occurred! You probably forgot to close the excel file before running the program :/")
        print("Please close the excel file and try again!")




'''
# FUNCTION FOR CSV FILE: NEEDS REVISION!!!!!!
# If you need to use a CSV instead of a xlsx file, use this portion!
# Need major fixes, but too lazy to do it XD GLHF!
def write_to_csv(extracted_data, toolName, findcatOrg):
    try:
        csv_file_name = toolName.lower() + '_' + findcatOrg + '.csv'
       with open(csv_file_name, mode='w', encoding='utf-8', newline='') as csv_file:
            fieldnames = ['category', 'resource_name', 'severity', 'description', 'refID', 'id']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            writer.writeheader()
            for data in extracted_data:
                writer.writerow(data)

        print(f"Data written to {csv_file_name}.\nPlease check - " + newPath + f"\\{csv_file_name}")
    except (exception name):
        print('-' * 80)
        print("Oops, an error occurred! You probably forgot to close the csv file before running the program :/")
        print("Please close the excel file and try again!")
'''

# START OF MAIN CODE
# Input header
# Main code
# Input header
input_args = sys.argv[1:]
# Lookup string
findcatOrg = input_args[0]
# Path of ROOT folder that contains both 'tools' and 'result'
rootPath = input_args[1]
# Path of initial tool folder
toolFolder = input_args[2]
# Path of initial result folder
resultFolder = input_args[3]
findcat = findcatOrg.lower()

# First, get tool 
print(f"Getting {toolName.upper()} files...")
download_and_extract_repo(owner, repo, toolFolder)

print(f"Extracting from TFSEC...")

serviceList = get_folders_from_url(rootURL)
extracted_data = []

# 0. Check if user is trying to get all policies.
if(findcat == 'findall'):
    fetchAll(extracted_data)

# 1. Check if there is SPECIFIC folder for service

matchService = []
for service in serviceList:
    if re.search(r'\b' + findcat + r'\b', service):
        matchService.append(service)

# 1.A: No SPECIFIC folder for service, need to go through all files manually
# a. Go to root index.md, get all folder names, store in higher cat list
# b. Iterate through higher cat list, get small cat list per higher cat
# c. URL is complete per small cat.
if len(matchService) == 0:
    print(f"\nRegula does not have a specific folder of policies for '{findcatOrg}', searching all rules by context...")
    print("This may take some time, how about a bathroom break? :D\n")
    search_all_policies(findcat, serviceList, extracted_data)
# 1.B: 1 SPECIFIC folder for service, get contents of that folder
elif len(matchService) == 1:
    for service in matchService:
        print(f"\nTfsec provides a specific folder of policies for '{findcatOrg}': {service}")
        print("Please refer to specific folder for further details.")
        get_policy_from_folder(service, extracted_data)
# 1.C: More than 1 SPECIFIC folder for service, get contents of all folders
else:
    print(f"\nTfsec provides multiple folders for '{findcatOrg}':")
    for service in matchService:
        print(f'\t{service}')
        get_policy_from_folder(service, extracted_data) 
    print("Please refer to each folder for further details.")
# 2. Print into excel file
# Create XLSX file accordingly
if not extracted_data:
    print(f"No policies found related to '{findcatOrg}'. Double-check the service you want to look up, and try again!")
else:
    write_to_excel(extracted_data, toolName, findcatOrg, resultFolder)