'''
File that stores all functions related to creating necessary directories in each run
'''
import difflib
import os
import shutil
import sys

def create_save_dir(is_valid):
    '''
    If integrity check failed, creates empty 'data' dir; if 'data' dir exists, delete all contents and create an empty one.
    Else, integrity check succeded, do nothing
    Retunrs 'save_dir' path
    '''
    project_root = os.getcwd()
    save_dir = os.path.join(project_root, f"data")
    if is_valid is False:
        if os.path.exists(save_dir):
            # Remove all contents of the directory
            for filename in os.listdir(save_dir):
                file_path = os.path.join(save_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # remove file or symlink
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # remove directory
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
        else:
            os.makedirs(save_dir)
    return save_dir

def create_up_tool_list(is_valid, usr_tool_list, supported_tool_list):
    '''
    If integrity check failed, returns list of all supported tools
    Else, integrity check succeded, check if all tools in user input is supported; lowercase inputs are permitted
    If yes, return list of original names for tools to download
    Else, raise ValueError
    '''
    # 1. If integrity check failed, all tools need to be downloaded; return full list
    result = []
    if is_valid is False:
        result = supported_tool_list
    # 2. If integrity check succeeded, run check of user input
    else:
        # Check if user input(args.tool) is not None
        if usr_tool_list:
            _NORMALIZED = {k.lower(): k for k in supported_tool_list}
            norm_keys = list(_NORMALIZED.keys())
            for usr_tool in usr_tool_list:
                usr_tool_norm = usr_tool.lower()
                # If user input not in supported tool list, check possibility of typo
                if usr_tool_norm not in _NORMALIZED.keys():
                    hint_norms = difflib.get_close_matches(usr_tool_norm, norm_keys, n=1, cutoff=0.5)
                    if hint_norms:
                        # Map normalized suggestion back to the original casing
                        suggested_original = _NORMALIZED[hint_norms[0]]
                        print(f"❓ Unknown tool: {usr_tool!r}. Did you mean {suggested_original!r}?")
                        raise ValueError("❌ Tool list input is invalid, double-check tool name and try again.")
                    else:
                        # No good match; list available options
                        options = ", ".join(supported_tool_list)
                        print(f"❓ Unknown tool: {usr_tool!r}.")
                        print(f"Options: {options}. Lowercase inputs are accepted.")
                        raise ValueError("❌ Tool list input is invalid, double-check tool name and try again.")
                else:
                    result.append(_NORMALIZED[usr_tool_norm])
    return result
    
def get_update_tool_list(is_valid, usr_tool_list, supported_tool_list):
    '''Print output results without traceback'''
    try:
        result = create_up_tool_list(is_valid, usr_tool_list, supported_tool_list)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    return result