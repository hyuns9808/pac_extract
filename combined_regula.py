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
toolName = "regula"
owner = "fugue"
repo = "regula"

# PATTERNS
# Regular expression to find content within rego file
policy_pattern = re.compile(
    r'\_\_rego\_\_metadoc\_\_\s*\:\=\s*\{'
    r'[\s\S]*\"custom\"\:\s*\{'
    r'[\s\S]*\"severity\"\:\s*\"([^"]+?)\"'
    r'\s*\}\,'
    r'[\s\S]*\"description\"\:\s*\"([\s\S]*)\"\,'
    r'[\s\S]*\"id\"\:\s*\"([^"]+?)\"\,'
    r'[\s\S]*\"title\"\:\s*\"([^"]+?)\"'
    r'[\s\S]*\}'
)

# HELPER FUNCTIONS
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
        return "아이캔트스피크잉글리쉬 - " + engSeverity

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
    
# Function that gets list of files within specific path
def get_content_in_directory(dir_path, target):
    try:
        # List all files and directories in the given directory
        entries = os.listdir(dir_path)
        if target == 'file':
            files = [entry for entry in entries if os.path.isfile(os.path.join(dir_path, entry))]
        elif target == 'dir':
            files = [entry for entry in entries if os.path.isdir(os.path.join(dir_path, entry))]
        else:
            print("get_content_in_directory arg error: check if target is either 'file' or 'dir'")
            return
        return files
    except FileNotFoundError:
        print(f"Directory {dir_path} not found.")
        return []
    except PermissionError:
        print(f"Permission denied to access {dir_path}.")
        return []
 
# Search all policies provided that includes targetString
# result should be list of policies that are
# parsed correctly[('ruleCode': '', 'severity': '', ...)]
def search_all_policies(targetString, serviceList, resultList):
    matchServices = {}
    total = 0
    for service in serviceList:
        result = get_matching_policy_from_folder(service, targetString, resultList)
        if result != 0:
            matchServices[service] = result
            total += result
    if total != 0:
        print("Folders that contain policies related to " + findcatOrg + ":")
        for matchService in matchServices:
            print(f"\t{matchService}: {matchServices[matchService]}")
    else:
        print(f"No additional folders with policies that mention {findcatOrg}...")
    return total

# Get all policies within folder
# result should be list of policies that are
# parsed correctly[('ruleCode': '', 'severity': '', ...)]
def get_policy_from_folder(serviceName, resultList):
    # first get all policies within folder
    fileNames = get_content_in_directory(f'{policyFolder}\\{serviceName}', "file")
    count = 0
    for fileName in fileNames:
        filePath = "~\\" + serviceName + "\\" + fileName
        with open(f'{policyFolder}\\{serviceName}\\{fileName}', 'r', encoding='utf-8', errors='ignore') as f:
            policyContent = f.read()
        process_policies(policy_pattern.findall(policyContent), filePath, "O", resultList)
        count += 1
    print("Number of policies in folder " + serviceName + ": " + str(count) + "\n")
    return count

# Get all policies that contain targetString in title within folder
# result should be list of policies that are
# parsed correctly[('ruleCode': '', 'severity': '', ...)]
def get_matching_policy_from_folder(serviceName, targetString, resultList):
    # first get all policies within folder
    fileNames = get_content_in_directory(f'{policyFolder}\\{serviceName}', "file")
    print("Looking up folder \'" + serviceName + "\'...")
    count = 0
    for fileName in fileNames:
        with open(f'{policyFolder}\\{serviceName}\\{fileName}', 'r', encoding='utf-8', errors='ignore') as f:
            policyContent = f.read()
        policy = policy_pattern.findall(policyContent)
        pattern = rf'\b{re.escape(targetString)}\b'
        match = re.search(pattern, policy[0][1], re.IGNORECASE)
        if match:
            filePath = "~\\" + serviceName + "\\" + fileName
            print("\tMatching policy found! - " + filePath)
            process_policies(policy, filePath, "X", resultList)
            count += 1
    if count != 0:
        print("Number of matching policies in folder " + serviceName + ": " + str(count) + "\n")
    else:
        print("\tNo matching policies found in folder " + serviceName + ". Proceeding to next folder...\n")
    return count


# Get policies from policyData, appends to resultList
def process_policies(policyData, filePath, serviceSpecific, policyList):
    for policy in policyData:
        severity, description, id, title = policy
        severity = korSeverity(severity.lower())
        policyList.append({
            'severity': severity.strip(),
            'description': description.strip(),
            'id': id.strip(),
            'title': title.strip(),
            'serviceSpecific': serviceSpecific,
            'filePath': filePath
        })

# Get policies from policyData, writes into givenWorksheet
def write_policies_to_worksheet(givenWorksheet, policyData):
    row = 1
    for policy in policyData:
        givenWorksheet.write(row, 0, policy['id'])
        givenWorksheet.write(row, 1, policy['title'])
        givenWorksheet.write(row, 2, policy['filePath'])
        givenWorksheet.write(row, 3, policy['serviceSpecific'])
        givenWorksheet.write(row, 4, policy['severity'])
        givenWorksheet.write(row, 5, policy['description'])
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

        headers = ['RuleID', 'Title', 'File Location', targetString + ' Specified', 'Severity', 'Summary']
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

# Path of policy folder for each provider
# Change path for different cloud provider
policy_path_string = "rego\\rules\\tf\\aws"
# Path of final constructed policy folder
policyFolder = os.path.join(os.path.join(toolFolder, f"{repo}-master"), policy_path_string)


# First, get tool 
print(f"Getting {toolName.upper()} files...")
download_and_extract_repo(owner, repo, toolFolder)

print(f"Extracting from {toolName.upper()}...")

# Get list of folders from Regula GitHub repo
serviceList = get_content_in_directory(policyFolder, "dir")

# First, see if there is folder for specific service
matchService = []
for service in serviceList:
    if findcat in service.split('_'):
        matchService.append(service)
        serviceList.remove(service)
# List to store ALL extracted policies as a bunch
extracted_data = []
specificTotal = 0

# 1.A: No SPECIFIC folder for service, need to go through all files manually
# a. Use serviceList and iterate through all folders
# b. Search all files within folder
if len(matchService) == 0:
    print(f"\n{toolName.upper()} does not have a specific folder of policies for '{findcatOrg}'...")
# 1.B: 1 SPECIFIC folder for service, get contents of that folder
elif len(matchService) == 1:
    print(f"{toolName.upper()} provides the following folder for '{findcatOrg}':")
    for service in matchService:
        specificTotal += get_policy_from_folder(service, extracted_data)
    print("Please refer to specific folder for further details.")
# 1.C: More than 1 SPECIFIC folder for service, get contents of all folders
else:
    print(f"\n{toolName.upper()} provides multiple folders for '{findcatOrg}':")
    for service in matchService:
        print(f'\t{service}')
        specificTotal += get_policy_from_folder(service, extracted_data) 
    print("Please refer to each folder for further details.")
# Prompt user that program will continue searching all files:
print(f"\nAttempting to searching all rules by context of policies for '{findcatOrg}'...")
print("This may take some time, how about a bathroom break? :D\n")
matchTotal = search_all_policies(findcat, serviceList, extracted_data)
print(f"\n{toolName.upper()} SUMMARY:")
print(f"\tTotal number of polices specified for {findcatOrg}: {specificTotal}")
print(f"\tTotal number of polices not specified but mentions {findcatOrg}: {matchTotal}")
print(f"\n{toolName.upper()} TOTAL POLICIES: {str(specificTotal + matchTotal)}")

# Create XLSX file accordingly
if not extracted_data:
    print(f"No policies found related to {findcatOrg}. Double-check the service you want to look up, and try again!")
else:
    if not os.path.exists(resultFolder):
        os.makedirs(resultFolder)
    write_to_excel(extracted_data, toolName, findcatOrg, resultFolder)

'''
# CODE FOR CSV FILE: SUPER OUTDATED
# If you need to use a CSV instead of a xlsx file, use this portion!
# Define the CSV file name
csv_file_name = toolName + '_' + findcatOrg + '.csv'

# Write the extracted data to a CSV file
with open(csv_file_name, mode='w', newline='') as csv_file:
    fieldnames = ['summary', 'resource', 'severity', 'ruleID']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
    writer.writeheader()
    for data in extracted_data:
        writer.writerow(data)

print(f"Data written to {csv_file_name}.\nPlease check - " + resultPath + f"\\{csv_file_name}")
'''