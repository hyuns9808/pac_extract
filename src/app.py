import streamlit as st
from streamlit_option_menu import option_menu
import time
import os
import pandas as pd
import sqlite3
import json

project_root = os.getcwd()
pac_dir_path = os.path.join(project_root, "raw_pac_files")
data_dir_path = os.path.join(project_root, "database")
os.makedirs(pac_dir_path, exist_ok=True)
os.makedirs(data_dir_path, exist_ok=True)

DOWNLOAD_DIR = "data"

def download_pac():
    return

def fake_download(tool, file_type):
    file_path = os.path.join(DOWNLOAD_DIR, f"{tool}.{file_type}")
    if file_type == "csv":
        df = pd.DataFrame({
            "id": range(1, 6),
            "tool": [tool]*5,
            "value": [10, 20, 30, 40, 50]
        })
        df.to_csv(file_path, index=False)
    elif file_type == "json":
        data = [{"id": i, "tool": tool, "value": i*10} for i in range(1,6)]
        with open(file_path, "w") as f:
            json.dump(data, f)
    elif file_type == "sql":
        conn = sqlite3.connect(file_path)
        df = pd.DataFrame({
            "id": range(1,6),
            "tool": [tool]*5,
            "value": [10, 20, 30, 40, 50]
        })
        df.to_sql("data", conn, if_exists="replace", index=False)
        conn.close()
    return file_path

def load_file(file_path):
    ext = file_path.split(".")[-1]
    if ext == "csv":
        return pd.read_csv(file_path)
    elif ext == "json":
        with open(file_path) as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif ext == "sql":
        conn = sqlite3.connect(file_path)
        df = pd.read_sql("SELECT * FROM data", conn)
        conn.close()
        return df
    else:
        return None

def app():
    st.title("⚗️ PaC_Extract")
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",  # required
            options=["Home", "Download PaC Files", "Search PaC", "Visualize Data"],  # required
            icons=["cloud-download", "search", "bar-chart"],  # optional
            menu_icon="cast",
            default_index=0,
        )
    if selected == "Home":
        st.header("Home")
    elif selected == "Download PaC Files":
        st.header("Download PaC Files")
        st.markdown("Select which tools to download/update raw PaC files.")
        # Define all inputs
        update = st.checkbox("Update all repos", value=True)
        tools_input = st.multiselect("Select tools to update", ["Checkov", "KICS", "Terrascan", "Trivy"], default=["Checkov"],disabled=update)
        file_types = st.multiselect("Select file types to save", ["csv", "json", "sql", "xlsv"], default=["csv"])

        if st.button("Start Download"):
            if not tools_input.strip():
                st.error("Please enter at least one tool.")
                return
            if not file_types:
                st.error("Please select at least one file type.")
                return

            tools = tools_input.strip().split()
            total_tasks = len(tools) * len(file_types)
            progress_bar = st.progress(0)
            task_count = 0

            for tool in tools:
                for ft in file_types:
                    task_count += 1
                    progress_bar.progress(task_count / total_tasks)
                    st.write(f"Downloading **{tool}** as **{ft}**...")
                    time.sleep(1)  # simulate download delay
                    path = fake_download(tool, ft)
                    st.success(f"Saved to {path}")

            st.balloons()
    if selected == "Download Files":
        st.header("Download Files")
        tools_input = st.text_input("Enter tools to download (space separated)")
        file_types = st.multiselect("Select file types to save", ["csv", "json", "sql"], default=["csv"])

        if st.button("Start Download"):
            if not tools_input.strip():
                st.error("Please enter at least one tool.")
                return
            if not file_types:
                st.error("Please select at least one file type.")
                return

            tools = tools_input.strip().split()
            total_tasks = len(tools) * len(file_types)
            progress_bar = st.progress(0)
            task_count = 0

            for tool in tools:
                for ft in file_types:
                    task_count += 1
                    progress_bar.progress(task_count / total_tasks)
                    st.write(f"Downloading **{tool}** as **{ft}**...")
                    time.sleep(1)  # simulate download delay
                    path = fake_download(tool, ft)
                    st.success(f"Saved to {path}")

            st.balloons()
    elif selected == "Search Data":
        st.header("Search Data")
        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith((".csv", ".json", ".sql"))]
        selected_file = st.selectbox("Select a downloaded file", files)

        if selected_file:
            df = load_file(os.path.join(DOWNLOAD_DIR, selected_file))
            if df is None:
                st.error("Could not load file.")
                return

            search_term = st.text_input("Enter search term (filters any column)")

            if search_term:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
                filtered_df = df[mask]
            else:
                filtered_df = df

            st.write(f"Showing {len(filtered_df)} results")
            st.dataframe(filtered_df)
    elif selected == "Visualize Data":
        st.header("Visualize Data")
        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith((".csv", ".json", ".sql"))]
        selected_file = st.selectbox("Select a downloaded file to visualize", files)

        if selected_file:
            df = load_file(os.path.join(DOWNLOAD_DIR, selected_file))
            if df is None or df.empty:
                st.error("No data available for visualization.")
                return

            st.write("### Data Preview")
            st.dataframe(df.head())

            if "value" in df.columns and "tool" in df.columns:
                chart_data = df.groupby("tool")["value"].sum()
                st.bar_chart(chart_data)
            else:
                st.info("No 'tool' and 'value' columns to plot.")

if __name__ == "__main__":
    app()