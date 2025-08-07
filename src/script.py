import os
import pandas as pd

from setup.setup_parser import parser_setup
from setup.setup_integrity import data_checker, create_ver_token
from setup.setup_base import create_save_dir, get_update_tool_list
from setup.setup_data import get_pac_folder, get_pac_url
from fetch_pac.parse_tool import get_pac_of_tool

# 0. Setup argument parser
parser = parser_setup()
args = parser.parse_args()
if args.tools and not args.update:
    parser.error("--names can only be used when --update is enabled.")
    
# 1. Check integrity of 'data' dir to check if all repos need to be updated
# Also return version_info.json content
is_valid, version_info = data_checker()
version = version_info["version"]
date = version_info["date"]
full_tool_list = list(version_info["tool_info"].keys())
full_tool_info = version_info["tool_info"]

# 2. Based on integrity check results, create empty save directory
save_dir = create_save_dir(is_valid)

# 3. Based on user input and integrity check results, set list of tools to download
up_tool_list = get_update_tool_list(is_valid, args.tools, full_tool_list)

# 4. Download PaC repos of list of tools to update
for tool in up_tool_list:
    if full_tool_info[tool]["is_repo"] is True:
        get_pac_folder(
            tool_name=tool,
            repo_git=full_tool_info[tool]["url"],
            folder=full_tool_info[tool]["folder_path"],
            dest=os.path.join(save_dir, tool),
            ref=full_tool_info[tool]["branch"],
        )
    else:
        get_pac_url(
            tool_name=tool,
            url=full_tool_info[tool]["url"]
        )

# 5. Update 'version_token.flag' file
create_ver_token(version_info)

# 6. Correctly parse and get info from all downloaded repos using defined scripts
master_df = pd.DataFrame()
for tool in full_tool_list:
    master_df = pd.concat([master_df, get_pac_of_tool(tool)], ignore_index=True)

# 7. Generate result
print(master_df)