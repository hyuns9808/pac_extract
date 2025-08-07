'''
Functions related to getting relevant KICS PaCs
Reads stored .csv file for all queries, searches relevant ones and returns it as a dataframe
'''
import pandas as pd
    
# May fix to use more service-specific md files
def get_kics_pac():
    df = load_csv_table("data\\KICS\\all_queries.csv")
    print(df)
    
def load_csv_table(filepath):
    # Read CSV as a dataframe
    result = pd.read_csv(filepath)
    # Patch DF to common format
    result['Tool'] = 'KICS'
    return result

def filter_policies(df, partial_id, iac_type, keyword):
    keyword = keyword.lower()
    return df[
        df['Id'].str.contains(partial_id, case=False, na=False) &
        df['IaC'].str.lower().eq(iac_type.lower()) &
        (
            df['Entity'].str.lower().str.contains(keyword, na=False) |
            df['Policy'].str.lower().str.contains(keyword, na=False)
        )
    ]

if __name__ == '__main__':
    get_kics_pac()