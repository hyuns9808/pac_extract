'''
File that stores all functions related to checking the integrity of existing data
Runs the following operations:
1. Check the 'version_token.flag' file and compare it with .
2. If initial run, invalid init_token or data different than info in version_info.json, ignore user input and download all repos
3. If init_token info and data is correct, download only input given from user
'''
import json
import os
import re

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

def data_init(project_root):
    '''Gets version info from version_info.json'''
    data_json_path = os.path.join(project_root, "version_info.json")
    version_info = get_version_data(data_json_path)
    version = version_info["version"]
    date = version_info["date"]
    full_tool_list = list(version_info["tool_info"].keys())
    full_tool_info = version_info["tool_info"]
    return version_info, version, date, full_tool_list, full_tool_info
    
def data_checker(project_root, data_dir_path):
    '''Checks if 'data' dir is valid'''
    ver_token_path = os.path.join(data_dir_path, ".version_token.flag")
    token_pattern = r'Version:\s*([^\n]+)\s+Date:\s*(\d{8})\s+Tool list:\s*(\[[^\]]+\])'
    is_valid = False
    version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)
    # 1. Check if 'data' dir exists
    if os.path.exists(data_dir_path):
        # 2. Check if 'version_token.flag' exists and is valid
        if os.path.exists(ver_token_path):
            # 3. Check if 'version_info.json' and 'version_token.flag' content matches
            token_info = get_token_data(ver_token_path)
            match = re.search(token_pattern, token_info, re.MULTILINE)
            if match:
                token_version = match.group(1).strip()
                token_date = match.group(2).strip()
                token_tool_list_str = match.group(3).strip()
                # str comparison
                if version == token_version and date == token_date and json.dumps(full_tool_list) == token_tool_list_str:
                    # 4. Check if all tool directories exist within 'data' dir
                    tool_dir = [f for f in os.listdir(data_dir_path) if os.path.isdir(os.path.join(data_dir_path, f))]
                    tool_set = set(full_tool_list)
                    if set(tool_dir) == tool_set:
                        is_valid = True
            else:
                print(f"❌ ERROR: Token file is invalid...\n")
    print("✅ Integrity check complete.")
    if is_valid is True:
        print("✅ All files are valid.\n")
    else:
        print("❗ Invalid file composition\n")
    return is_valid

def create_ver_token(data_dir_path, version_info):
    '''Creates '.version_token.flag' file based on 'version_info.json' file'''
    ver_token_path = os.path.join(data_dir_path, f".version_token.flag")
    line_0 = f"Version: {version_info["version"]}\n"
    line_1 = f"Date: {version_info["date"]}\n"
    line_2 = f"Tool list: {json.dumps(list(version_info["tool_info"].keys()))}"
    with open(ver_token_path, 'w') as f:
        f.writelines([line_0, line_1, line_2])
        
'''
if __name__ == "__main__":
    data_checker()
'''