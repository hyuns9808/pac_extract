'''
File that stores all functions related to saving the master dataframe to requested type of file
'''
import pandas as pd
import difflib
import os

def save_dataframe(df: pd.DataFrame, user_input: str):
    # Directory to save master dataframe
    project_root = os.getcwd()
    master_dir = os.path.join(project_root, f"data\\MASTER")
    
    # Define all convertable file format here
    formats = {
        "sql": lambda path: df.to_sql("table_name", "sqlite:///" + path, if_exists="replace", index=False),
        "csv": lambda path: df.to_csv(path, index=False),
        "excel": lambda path: df.to_excel(path, index=False),
        "json": lambda path: df.to_json(path, orient="records", indent=2)
    }

    # Ask user for format
    # user_input = input("Enter desired file format (SQL, CSV, Excel, JSON): ").strip().lower()
    user_input = user_input.strip().lower()

    # Find closest match if typo
    if user_input not in formats:
        closest = difflib.get_close_matches(user_input, formats.keys(), n=1, cutoff=0.6)
        if closest:
            print(f"❗ WARNING - Invalid user input: {user_input}")
            print(f"\tDid you mean '{closest[0]}'?")
            print(f"\tSaving as: '{closest[0]}'. Rerun script if this is not intended.")
            print(f"\tSupported formats: {list(formats.keys())}")
            user_input = closest[0]
        else:
            raise ValueError(f"Unsupported format '{user_input}'. Supported formats: {list(formats.keys())}")

    # Check dir path and save file
    os.makedirs(master_dir,exist_ok=True)
    ext = "xlsx" if user_input == "excel" else user_input
    output_path = os.path.join(master_dir, f"master.{ext}")
    formats[user_input](output_path)
    print(f"✅ Master dataframe file saved at: {output_path}\n")