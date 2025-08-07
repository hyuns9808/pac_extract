'''
Functions related to getting relevant KICS PaCs
Reads stored .csv file for all queries, searches relevant ones and returns it as a dataframe
'''
import pandas as pd

# Change file path of csv if necessary
file_path = "data\\KICS\\all_queries.csv"
# Correctly parses query document link into provider name
id_to_provider = {
    "alicloud": "Alibaba Cloud",
    "aws": "AWS",
    "azure": "Azure",
    "nan": "NaN",
    "nifcloud": "Nifcloud",
    "gcp": "Google Cloud Platform",
    "tencentcloud": "Tencent Cloud",
}
    
def get_kics_pac(file_path=file_path):
    '''
    Wrapper function for creating pd dataframe
    '''
    # Read CSV as a dataframe
    df = pd.read_csv(file_path)
    # Patch DF to common format
    # Tool-ID-Name-IaC-Provider-Severity-Query Document-Related Document
    result = pd.DataFrame()
    result["Tool"] = ["KICS"] * len(df)
    result["ID"] = df["Query ID"]
    result["IaC"] = df["Platform "]
    name_ptn = r"https://docs.kics.io/latest/queries/[^/]+/([^/]+)/[^/]+"
    result["Provider"] = df["Query Details"].str.extract(name_ptn)[0].map(id_to_provider)
    result["Severity"] = df["Severity "]
    result["Query Document"] = df["Documentation"]
    result["Related Document"] = df["Query Details"]
    return result

def filter_policies(df, partial_id, iac_type, keyword):
    '''
    Returns dataframe that consists of partial id, iac type and keyword match
    '''
    keyword = keyword.lower()
    return df[
        df['Id'].str.contains(partial_id, case=False, na=False) &
        df['IaC'].str.lower().eq(iac_type.lower()) &
        (
            df['Entity'].str.lower().str.contains(keyword, na=False) |
            df['Policy'].str.lower().str.contains(keyword, na=False)
        )
    ]

'''
if __name__ == '__main__':
    df = get_kics_pac()
    print(df)
'''