'''
Functions related to getting relevant KICS PaCs
Reads stored .csv file for all queries, searches relevant ones and returns it as a dataframe
'''
import pandas as pd

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
    
def get_kics_pac(file_path):
    '''
    Wrapper function for creating pd dataframe
    '''
    # Read CSV as a dataframe
    df = pd.read_csv(file_path)
    # Patch DF to common format
    # Tool-ID-Title-Description-IaC-Category-Provider-Severity-Query Document-Related Document
    result = pd.DataFrame()
    result["Tool"] = ["KICS"] * len(df)
    result["ID"] = df["Query ID"]
    result["Title"] = df["Query Name"]
    result["Description"] = ["NaN"] * len(df)
    result["IaC"] = df["Platform "]
    result["Category"] = df["Category "]
    name_ptn = r"https://docs.kics.io/latest/queries/[^/]+/([^/]+)/[^/]+"
    result["Provider"] = df["Query Details"].str.extract(name_ptn)[0].map(id_to_provider)
    result["Severity"] = df["Severity "]
    result["Query Document"] = df["Query Details"]
    result["Related Document"] = df["Documentation"]
    return result

'''
if __name__ == '__main__':
    df = get_kics_pac()
    df.to_csv("result.csv")
'''