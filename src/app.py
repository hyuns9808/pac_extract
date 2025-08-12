import streamlit as st
from streamlit_option_menu import option_menu
import time
import os
import pandas as pd
import sqlite3
import json

from init_setup.setup_integrity import data_init, data_checker, create_ver_token
from init_setup.setup_base import dir_init, dir_update, get_update_tool_list
from init_setup.setup_data import get_pac_folder, get_pac_url
from init_setup.setup_save_master import save_dataframe
from parse_pac.parse_tool import get_pac_of_tool

def download_pac():
    return

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
    # Create all base directories
    project_root, pac_raw_dir, pac_db_dir = dir_init()
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",  # required
            options=["Home", "Download PaC Files", "Search PaC", "Visualize Data"],  # required
            icons=["cloud-download", "search", "bar-chart"],  # optional
            menu_icon="cast",
            default_index=0,
        )
    # Home menu
    if selected == "Home":
        st.header("Home")
    # Download menu
    elif selected == "Download PaC Files":
        st.title("📥 Download PaC Files")
        st.markdown("Easily select tools and update **Policy as Code** (PaC) files with just a few clicks.")
        # Get version info and run data integrity check
        version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)
        # Print version info
        st.subheader("📦 PaC_Extract Version Info")
        # Info box for version/date/tools
        st.info(
            f"""
            **Version:** {version}  
            **Date:** {date}  
            **Supported Tools:** {", ".join(full_tool_list)}
            """,
            icon="ℹ️"
        )
        # Divider
        st.divider()
        # Inputs
        st.subheader("⚙️ Download Settings")
        update = st.checkbox(
            "Update all repositories",
            value=True,
            help="If selected, all tools will be updated regardless of your tool selection."
        )
        db_only = st.checkbox(
            "Create database files only without updating the files",
            value=True,
            help="If selected, only database files will be created for selected tools without downloading/updating the raw PaC files."
        )
        tools_input = st.multiselect(
            "Select tools to update",
            options=full_tool_list,
            default=[full_tool_list[0]],
            disabled=update,
            help="Choose which tools you want to update. Disabled if 'Update all' is checked."
        )
        file_types = st.multiselect(
            "Select file types to save",
            options=["csv", "json", "sql", "xlsx"],
            default=["csv"],
            help="Choose the output formats for your downloaded PaC files."
        )
        # Spacer before button
        st.markdown("")
        # Start button
        st.markdown("### 🚀 Ready?")
        if st.button("Start Download", use_container_width=True):
            # Check update options
            if update:
                tools_input = full_tool_list
            if not update and not tools_input:
                st.error("Please enter at least one tool.")
                return
            if not file_types:
                st.error("Please select at least one file type.")
                return
            st.success("Download process started...")
            
            # Run integrity check
            is_valid = data_checker(project_root, pac_raw_dir)
            # Based on integrity check, update directory content
            dir_update(project_root, pac_raw_dir, is_valid)
            
            # Get user inputs
            progress_bar = st.progress(0)
            status_text = st.empty()
            task_count = 0
            up_tool_list = get_update_tool_list(is_valid, tools_input, full_tool_list)
            # All tools + Master file
            total_tasks = len(up_tool_list) + 1
            # Master DF
            master_df = pd.DataFrame()
            
            # Status section
            if is_valid:
                st.success("✅ Data integrity check complete — all files are valid!")
            else:
                st.error("❗ Invalid file composition — redownloading all files...")
            if db_only:
                st.info(
                    f"""
                    **Creating database files for total {len(up_tool_list)} tools...**\n
                    **List of tools: {up_tool_list}** \n
                    **Database file types: {file_types}**
                    """,
                    icon="ℹ️"
                )
            else:
                st.info(
                    f"""
                    **Downloading files for total {len(up_tool_list)} tools...**\n
                    **List of tools: {up_tool_list}**
                    """,
                    icon="ℹ️"
                )
            st.markdown("<hr style='margin:0; border: 0.5px solid #ddd;'>", unsafe_allow_html=True)
            
            # Update all tools based on user input
            for tool in up_tool_list:
                # Setup progress bar
                if total_tasks > 0:
                    progress_value = task_count / total_tasks
                else:
                    progress_value = 0
                progress_bar.progress(progress_value)
                percent = int(progress_value * 100)
                status_text.markdown(f"**Progress:** {percent}% — Downloading **{tool}**...")
                tool_raw_path = os.path.join(pac_raw_dir, tool)
                
                # First, download RAW PaC files
                if not db_only:
                    st.info(
                        f"""
                        **Downloading raw PaC files for tool: {tool}**
                        """,
                        icon="ℹ️"
                    )
                    if full_tool_info[tool]["is_repo"] == "True":
                        get_pac_folder(
                            tool_name=tool,
                            repo_git=full_tool_info[tool]["url"],
                            folder=full_tool_info[tool]["folder_path"],
                            dest=tool_raw_path,
                            ref=full_tool_info[tool]["branch"],
                        )
                    else:
                        get_pac_url(
                            tool_name=tool,
                            url=full_tool_info[tool]["url"],
                            dest=tool_raw_path
                        )
                    st.success(f"✅ Raw PaC files for tool - '{tool}' -  saved at: `{tool_raw_path}`")
                    st.markdown("<hr style='margin:0; border: 0.5px solid #ddd;'>", unsafe_allow_html=True)
                
                # Second, save individual file
                st.info(
                    f"""
                    **Creating database files for tool: {tool}**
                    """,
                    icon="ℹ️"
                )
                head_file_path = os.path.join(tool_raw_path, full_tool_info[tool]["head_path"])
                tool_df = get_pac_of_tool(tool, head_file_path)
                master_df = pd.concat([master_df, tool_df], ignore_index=True)
                tool_db_dir = os.path.join(pac_db_dir, tool)
                for type in file_types:
                    output_path = save_dataframe(tool_db_dir, tool_df, tool, type)
                    st.success(f"✅ Database file for - '{tool}' - in format - '{type}' - saved at: {output_path}\n")
                st.markdown("<hr style='margin:0; border: 0.5px solid #ddd;'>", unsafe_allow_html=True)
                task_count += 1
            
            # Third and last, save master file
            st.info(
                    f"""
                    **Creating MASTER database files...**
                    """,
                    icon="ℹ️"
            )
            master_db_dir = os.path.join(pac_db_dir, "master")
            for type in file_types:
                save_dataframe(master_db_dir, master_df, "MASTER", type)
                st.success(f"✅ MASTER database file in format - '{type}' saved at: {output_path}\n")
            st.markdown("<hr style='margin:0; border: 0.5px solid #ddd;'>", unsafe_allow_html=True)
            
            # After all individual files are downloaded, update token
            if is_valid is False:
                st.info(
                    f"""
                    **Creating version token...**\n
                    """,
                    icon="ℹ️"
                )
                create_ver_token(pac_raw_dir, version_info)
            
            progress_bar.progress(1.0)
            status_text.markdown("✅ **All tasks completed!** 🎉")
            st.balloons()
    # Search menu
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
    # Visualize menu
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