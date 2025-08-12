'''
File that stores all functions related to saving the master dataframe to requested type of file
'''
import pandas as pd
import os

def save_dataframe(db_dir, df: pd.DataFrame, tool_name:str, file_type: str):
    # Define all convertable file format here
    formats = {
        "sql": lambda path: df.to_sql("table_name", "sqlite:///" + path, if_exists="replace", index=False),
        "csv": lambda path: df.to_csv(path, index=False),
        "xlsx": lambda path: df.to_excel(path, index=False),
        "json": lambda path: df.to_json(path, orient="records", indent=2)
    }
    
    # Check dir path and save file
    os.makedirs(db_dir, exist_ok=True)
    output_path = os.path.join(db_dir, f"{tool_name}_db.{file_type}")
    formats[file_type](output_path)
    if tool_name == "MASTER":
        print(f"✅ MASTER file saved at: {output_path}\n")
    else:
        print(f"✅ Database file for - '{tool_name}' - in format - '{file_type}' saved at: {output_path}\n")
    return output_path