import subprocess
import sys
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

def initial_run(tools, toolFolder, resultFolder):
    # Input header
    print('-' * 80)
    print("IaC_Extract")
    print('-' * 80)
    print("Written by Calvin (Hyunsoo) Yang | 양현수 - https://github.com/hyuns9808")
    print("Public repo of IaC_Extract - https://github.com/hyuns9808/IaC_Extract")
    print("")
    print('-' * 80)
    print("This program automatically downloads the most recent version of each open source program.")   
    print("Then takes a STRING as an input and gets the PaC files of 4 tools that contains the string.")
    print("Tools are in the following order:\n")
    for tool in tools:
        print(f"\t{tool}")
    print(f"\nThe downloaded tools are stored at - {toolFolder}")
    print(f"All extracted data are stored as a .xlsx(Excel) file and saved at  - {resultFolder}\n")
    print("!!! YOU NEED AT LEAST 100MB OF STORAGE IN YOUR SYSTEM TO DOWNLOAD ALL FILES PROPERLY !!!")
    print("!!!                    ALL DATA EXTRACTED IS WRITTEN IN ENGLISH                      !!!")
    print('-' * 80)

def repeated_run(toolFolder, resultFolder, dir_path):
    print("Press 'Enter' to exit.")
    findcatOrg = input("Enter a string you would like to look up for ALL TOOLS: ")
    if findcatOrg == "":
        return False

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
        script = os.path.join(dir_path, script)
        stdout, stderr = run_script_with_args(script, args)
        if stderr:
            print(f"Error running {script}:\n{stderr}")
        else:
            print(stdout)
        print("-" * 80)
    
    print("\nAll policies are extracted! Opening folder with resulting excel files...\n")
    try:
        open_folder(os.path.realpath(os.path.join(resultFolder, findcatOrg)))
    except FileNotFoundError:
        print("No results were found; check your lookup value and try again!\n")
    print("-" * 80)
    return True


if __name__ == "__main__":
    # Path where output file will be stored
    # For local testing, use code below:
    # dir_path = os.path.dirname(os.path.abspath(__file__))
    dir_path = pathlib.Path().resolve()
    toolFolder = os.path.join(dir_path, "tools")
    resultFolder = os.path.join(dir_path, "result")
    req_file = os.path.join(dir_path, "requirements.txt")

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
    
    '''
    requirements = [
        "Requests",
        "xlsxwriter"
    ]
    '''

    # Run initial code(greetings, initial setup etc.)
    initial_run(tools, toolFolder, resultFolder)

    # Keep searching till user is defeated
    user_will = True
    while user_will:
        user_will = repeated_run(toolFolder, resultFolder, dir_path)