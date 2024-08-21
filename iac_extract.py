import subprocess
import os
import platform
import pathlib

def run_script_with_args(script_path, args):
    try:
        # Use subprocess to run the script with arguments
        result = subprocess.run(
            ["python", script_path] + args,
            stdout=subprocess.PIPE,     # Capture standard output
            stderr=subprocess.PIPE      # Capture standard error
        )
        
        # Return the output and any errors
        return result.stdout.decode(), result.stderr.decode()
    except Exception as e:
        return "", str(e)

def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

if __name__ == "__main__":
    # Path where output file will be stored
    dir_path = pathlib.Path().resolve()
    toolFolder = os.path.join(dir_path, "tools")
    resultFolder = os.path.join(dir_path, "result")

    # Name of tools you want to check
    tools = [
        'regula',
        'terrascan',
        'checkov',
        'tfsec'
    ]

    # Name of files you are going to run
    scripts = [
        "combined_regula.py",
        "combined_terrascan.py",
        "combined_checkov.py",
        "combined_tfsec.py"
    ]
    # Input header
    print('-' * 80)
    print("ULTIMATE(sorta) PaC Lookup Parser")
    print('-' * 80)
    print("Written by HYUNSOO YANG/양현수 @ SPARROW, 2024")
    print(">> Global Intern, SP Dvlpmnt Team 3: IaC Scanning Research")
    print(">> SP개발3팀 글로벌인턴: IaC 스캐닝 리서치")
    print('-' * 80)
    print("This program automatically DOWNLOADS the most recent version of each open source program.")   
    print("Then takes a STRING as an input and gets the PaC files of 4 tools that contains the string.")
    print("Tools are in the following order:\n")
    for tool in tools:
        print(f"\t{tool.upper()}")
    print(f"\nThe downloaded tools are stored at - {toolFolder}")
    print(f"All extracted data are stored as a .xlsx(Excel) file and saved at  - {resultFolder}\n")
    print("!!! AS THE FOLLOWING TOOL DOWNLOADS ALL TOOLS, YOU NEED AT LEAST 100MB OF STORAGE IN YOUR SYSTEM !!!")
    print("!!!                  PLEASE NOTE THAT ALL DATA EXTRACTED IS WRITTEN IN ENGLISH                   !!!")
    print('-' * 80)
    
    findcatOrg = input("Enter a string you would like to look up for ALL TOOLS: ")

    if not os.path.exists(toolFolder):
        os.makedirs(toolFolder)

    print('-' * 80)
    print(f"Created folder {toolFolder}. All scanning tool files will be stored here.")
    print('-' * 80)

    if not os.path.exists(resultFolder):
        os.makedirs(resultFolder)

    print('-' * 80)
    print(f"Created folder {resultFolder}. All result files will be stored here.")
    print('-' * 80)

    args = [findcatOrg, dir_path, toolFolder, resultFolder]

    for script in scripts:
        stdout, stderr = run_script_with_args(script, args)
        if stderr:
            print(f"Error running {script}:\n{stderr}")
        else:
            print(stdout)
        print("-" * 80)
    
    open_folder(os.path.realpath(os.path.join(resultFolder, findcatOrg)))
    print("\nAll policies are extracted! Opening folder with resulting excel files...")
    input("Press enter to exit;")