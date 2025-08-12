import os
import pandas as pd

from init_setup.setup_parser import parser_setup
from init_setup.setup_base import dir_init, dir_update, get_update_tool_list
from init_setup.setup_integrity import data_init, data_checker, create_ver_token
from init_setup.setup_data import get_pac_folder, get_pac_url
from init_setup.setup_save_master import save_dataframe
from parse_pac.parse_tool import get_pac_of_tool

# 0. Setup argument parser
parser = parser_setup()
args = parser.parse_args()
if args.tools and not args.update:
    parser.error("--names can only be used when --update is enabled.")
    
# 1. Check integrity of 'data' dir to check if all repos need to be updated
# Also return version_info.json content
project_root, pac_raw_dir, pac_db_dir = dir_init()

# 2. Get version info and run data integrity check
version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)

# 3. Run integrity check
is_valid = data_checker(project_root, pac_raw_dir)

# 4. Based on integrity check, update directory content
dir_update(project_root, pac_raw_dir, is_valid)

# 5. Download PaC repos of list of tools to update
up_tool_list = get_update_tool_list(is_valid, args.tools, full_tool_list)
for tool in up_tool_list:
    path = os.path.join(pac_raw_dir, tool)
    if full_tool_info[tool]["is_repo"] == "True":
        get_pac_folder(
            tool_name=tool,
            repo_git=full_tool_info[tool]["url"],
            folder=full_tool_info[tool]["folder_path"],
            dest=path,
            ref=full_tool_info[tool]["branch"],
        )
    else:
        get_pac_url(
            tool_name=tool,
            url=full_tool_info[tool]["url"],
            dest=path
        )

# 5. Update 'version_token.flag' file
create_ver_token(version_info)

# 6. Correctly parse and get info from all downloaded repos using defined scripts
master_df = pd.DataFrame()
for tool in full_tool_list:
    master_df = pd.concat([master_df, get_pac_of_tool(tool)], ignore_index=True)

# 7. From master dataframe, save file based on user request
print(f"Selected user output file format: {args.output}")
for out in args.output:
    save_dataframe(master_df, out)