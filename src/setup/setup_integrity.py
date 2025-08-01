'''
File that stores all functions related to checking the integrity of existing data
Runs the following operations:
1. Check the 'version_token.flag' file and compare it with .
2. If initial run, invalid init_token or data different than info in version_info.json, ignore user input and download all repos
3. If init_token info and data is correct, download only input given from user
'''
import difflib
import json
import os
import re
import sys

def get_version_data(version_data_json_path):
    '''Read 'version_info.json' file'''
    try:
        with open(version_data_json_path, "r", encoding="utf-8") as f:
            version_info = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"\tERROR: 'version_info.json' not found: {version_data_json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {version_data_json_path}: {e}") from e
    if not isinstance(version_info, dict):
        raise TypeError(f"Expected a JSON object (dict) at top level, got {type(version_info).__name__}")
    return version_info

def get_token_data(ver_token_path):
    '''Read '.version_token.flag' file'''
    try:
        with open(ver_token_path, "r", encoding="utf-8") as f:
            token_info = ' '.join(line.strip() for line in f.readlines())
    except FileNotFoundError:
        raise FileNotFoundError(f"\tERROR: '.version_token.flag' not found: {ver_token_path}")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(f"Cannot read {ver_token_path}: {e}") from e
    return token_info

def data_checker():
    '''Checks if 'data' dir is valid'''
    # Update any directory or token info here
    project_root = os.getcwd()
    data_dir_path = os.path.join(project_root, "data")
    data_json_path = os.path.join(project_root, "version_info.json")
    ver_token_path = os.path.join(data_dir_path, ".version_token.flag")
    token_pattern = r'Version:\s*([^\n]+)\s+Date:\s*(\d{8})\s+Tool list:\s*(\[[^\]]+\])'
    is_valid = False
    version_info = get_version_data(data_json_path)
    # 1. Check if 'data' dir exists
    if os.path.exists(data_dir_path):
        # 2. Check if 'version_token.flag' exists and is valid
        if os.path.exists(ver_token_path):
            # 3. Check if 'version_info.json' and 'version_token.flag' content matches
            # By logic, if version_token is correct, this indicates that all defined repos downloaded correctly
            token_info = get_token_data(ver_token_path)
            match = re.search(token_pattern, token_info, re.MULTILINE)
            if match:
                version = match.group(1).strip()
                date = match.group(2).strip()
                tool_list_str = match.group(3).strip()
                if version_info["version"] == version and version_info["date"] == date and json.dumps(list(version_info["tool_info"].keys())) == tool_list_str:
                    is_valid = True
            else:
                print(f"❌ ERROR: Token file is invalid...\n")
    if is_valid is True:
        print("✅ Integrity check complete. All files are valid...\n")
    else:
        print("✅ Integrity check complete. Invalid file composition, redownloading all files...\n")
    return is_valid, version_info

def create_ver_token(version_info):
    '''Creates '.version_token.flag' file based on 'version_info.json' file'''
    project_root = os.getcwd()
    ver_token_path = os.path.join(project_root, f"data/.version_token.flag")
    line_0 = f"Version: {version_info["version"]}\n"
    line_1 = f"Date: {version_info["date"]}\n"
    line_2 = f"Tool list: {json.dumps(list(version_info["tool_info"].keys()))}"
    with open(ver_token_path, 'w') as f:
        f.writelines([line_0, line_1, line_2])
        
        
if __name__ == "__main__":
    data_checker()