import streamlit as st
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from ydata_profiling import ProfileReport

import os
import io
import re
import pandas as pd

from init_setup.setup_integrity import data_init, data_checker, create_ver_token
from init_setup.setup_base import dir_init, dir_update, get_update_tool_list
from init_setup.setup_data import get_pac_folder, get_pac_url
from init_setup.setup_save_master import save_dataframe
from parse_pac.parse_tool import get_pac_of_tool

def app():
    st.set_page_config(
        page_title="PaC Extract",
        page_icon="⚗️"
    )
    # Create all base directories
    project_root, pac_raw_dir, pac_db_dir, master_db_dir = dir_init()
    master_df_csv = os.path.join(master_db_dir, "MASTER_db.csv")
    master_df = pd.DataFrame()
    
    with st.sidebar:
        selected = option_menu(
            menu_title="PaC Extract",
            options=["Home", "Download", "Search", "Visualize"],
            icons=["house", "cloud-download", "search", "bar-chart"],
            menu_icon="cast",
            default_index=0,
        )
    # Home menu
    if selected == "Home":
        st.title("⚗️ PaC Extract")
        st.markdown("""
        ### Lookup PaCs(Policy as Code) of popular open-source tools, straight from the source.
        
         ## ✨ What is PaC Extract?

        - **Collects & normalizes policies** from popular open-source IaC scanners (e.g., **Checkov**, **KICS**, **Terrascan**, **Trivy**).
        - **Creates a unified database** to look-up and compare what polices each open-source tool uses.
        - **Streamlines results** into standardized outputs (**CSV**, **JSON**, **SQL**, **XLSX**).
        
        ---
        
        ## 🖥️ Menus

        Within the sidebar, there are **four** menus:
        
        | Menu | Icon | Description |
        |------|------|-------------|
        | **Home** | :house: | 🏃 Quick overview and essential info at a glance. |
        | **Download** | :arrow_down: | 📥 Download/update your raw PaC files and get most recent PaCs per tool <br> 🗂️ Save combined/individual PaC database as file(**CSV**, **JSON**, **SQL**, **XLSX**) |
        | **Search** | :mag: | 🕹️ Search PaCs with specific keywords or filtering out data <br> 🗂️ Save search/filtered results as a **CSV** or **XLSX** file for closer examination |
        | **Visualize** | :bar_chart: | 🗒️ Visualize statistics and details of the combined database|
        
        ---
        
        ## 📥 Policy Sources (Open‑Source Collectors)

        PaC‑Scanner **ingests policies** from popular open‑source IaC scanners, normalizes them, and creates a combined database via **pandas** which can be saved in various file formats:

        | Tool       | Target | Notes |
        |--------------|----------|-------|
        | [Checkov](https://github.com/bridgecrewio/checkov)      | [Docs](https://github.com/bridgecrewio/checkov/tree/main/docs/5.Policy%20Index) | Imports PaCs from Checkov's **official documentation** within repo. |
        | [KICS](https://github.com/Checkmarx/kics)        | [Docs](https://github.com/Checkmarx/kics/tree/master/docs/queries)   | Imports PaCs from KICS **official documentation** within repo. |
        | [Prisma Cloud Docs](https://github.com/hlxsites/prisma-cloud-docs)        | [Docs](https://github.com/hlxsites/prisma-cloud-docs/tree/main/docs/en/enterprise-edition/policy-reference)   | Imports PaCs from Prisma Cloud's **official documentation** within repo. |
        | [Terrascan](https://github.com/tenable/terrascan)    | [Files](https://github.com/tenable/terrascan/tree/master/pkg/policies/opa/rego) | Parses PaCs **directly from Terrascan's raw Pac files**. |
        | [Trivy](https://github.com/aquasecurity/trivy)   | [Files](https://github.com/aquasecurity/trivy-checks/tree/main/checks) | Parses PaCs **directly from Trivy's raw Pac files provided in separate repo**. |

        Both combined and individual PaC databases for each tool is downloaded in the **"./pac_database"** directory.
        
        ---

        ## 🌟 Features

        - ⚡ **Fast & Lightweight** – Scans large repos of multiple open-source IaC scanning tools within seconds.
        - 🛡️ **Thorough Policy Lookups** – Find all PaC files of each open-source tool, some which do not provide official documents for.
        - 🔍 **Easy search engine** – Easily search for content within the app and export search results in either **.csv or .xlsx** for closer examination.
        - 🌍 **Broad IaC Coverage** – Library contains PaCs for multiple IaC languages, including Terraform, CloudFormation, Kubernetes, Docker, Helm charts, and generic YAML/JSON.
        - 📚 **Curated PaC Library** – Aggregates rules from open‑source IaC scanners into one pandas dataframe.
        - 🧠 **Smart Normalization** – Preserved original PaC files from each tool as much as possible to maintain its contents and meaning.
        - 📊 **Flexible DB** – Save results in various file formats, such as **.csv, .sql, .json, .xlsx.**
        - 🐍 **Poetry‑Powered** – Reproducible environments & dependency pinning with **Poetry**.
        - 👶 **Straightforward UI** - Based on Streamlit, launch an easy-to-use UI to download, search and look up data.
        
        ---
        
        Feel free to explore and reach out if you have questions or feedback!
        """, unsafe_allow_html=True)
    # Download menu
    elif selected == "Download":
        st.title("📥 Download PaC Files")
        st.markdown("Easily select tools and update **Policy as Code** (PaC) files with just a few clicks.")
        # Get version info and run data integrity check
        version_info, version, date, full_tool_list, full_tool_info = data_init(project_root)
        # Supported full file list; update manually if necessary
        full_file_list = ["csv", "json", "sql", "xlsx"]
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
        select_all_tools = st.checkbox(
            "Select all tools",
            value=True,
            help="If selected, update/download PaCs of all supported tools for all selected file types."
        )
        select_all_files = st.checkbox(
            "Select all file types",
            value=True,
            help="If selected, update/download PaCs of selected tools for all supported file types."
        )
        db_only = st.checkbox(
            "Create database files only without updating the files",
            value=False,
            help="If selected, only database files will be created for selected tools without downloading/updating the raw PaC files."
        )
        tools_input = st.multiselect(
            "Select tools to update",
            options=full_tool_list,
            default=[full_tool_list[0]],
            disabled=select_all_tools,
            help="Choose which tools you want to update. Disabled if 'Update all' is checked."
        )
        files_input = st.multiselect(
            "Select file types to save",
            options=full_file_list,
            default=[full_file_list[0]],
            disabled=select_all_files,
            help="Choose the output formats for your downloaded PaC files."
        )
        # Spacer before button
        st.markdown("")
        # Start button
        st.markdown("### 🚀 Ready?")
        if st.button("Start Download", use_container_width=True):
            # Check update options - tools
            if select_all_tools:
                tools_input = full_tool_list
            if not select_all_tools and not tools_input:
                st.error("Please select at least one tool.")
                return
            # Check update options - files
            if select_all_files:
                files_input = full_file_list
            if not select_all_files and not files_input:
                st.error("Please select at least one file type.")
                return
            st.success("Download process started...")
            
            # Run integrity check
            is_valid = data_checker(project_root, pac_raw_dir) and os.path.exists(master_df_csv)
            # Based on integrity check, update directory content
            dir_update(project_root, pac_raw_dir, is_valid)
            
            # Get user inputs
            progress_bar = st.progress(0)
            status_text = st.empty()
            task_count = 0
            up_tool_list = get_update_tool_list(is_valid, tools_input, full_tool_list)
            # All tools + Master file
            total_tasks = len(up_tool_list) + 1
            
            # Status section
            if is_valid:
                st.success("✅ Data integrity check complete — all files are valid!")
            else:
                st.error("❗ Invalid file composition — redownloading all files...")
            if db_only and is_valid:
                st.info(
                    f"""
                    **Creating database files for total {len(up_tool_list)} tools...**\n
                    **List of tools: {up_tool_list}** \n
                    **Database file types: {files_input}**
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
                if not db_only or not is_valid:
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
                for type in files_input:
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
            for full_tool in full_tool_list:
                if full_tool not in up_tool_list:
                    tool_raw_path = os.path.join(pac_raw_dir, full_tool)
                    head_file_path = os.path.join(tool_raw_path, full_tool_info[full_tool]["head_path"])
                    tool_df = get_pac_of_tool(full_tool, head_file_path)
                    master_df = pd.concat([master_df, tool_df], ignore_index=True)
            # REQUIRED: .csv file for master_df
            master_db_dir = os.path.join(pac_db_dir, "MASTER")
            if "csv" not in files_input:
                files_input.append("csv")
            for type in files_input:
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
            st.success(f"✅ All tasks completed! 🎉")
            status_text.markdown("✅ **All tasks completed!** 🎉")
            st.balloons()
    # Search menu
    elif selected == "Search":
        st.title("🔍 PaC Search")
        st.set_page_config(layout="wide")
        # Check master_df; if empty, read master db file
        if not os.path.exists(master_df_csv):
            st.error("""
                ❗ ERROR: No files found.\n 
                Go to 'Main Menu'-'Download PaC Files' and click 'Start Download' button to download all files and try again.
            """)
        else:
            if master_df.empty:
                master_df = pd.read_csv(master_df_csv)
            # Sidebar - Global search input (for filtering rows)
            search_term = st.text_input("Global Search")

            # Filter the dataframe based on search_term across all columns (case insensitive)
            if search_term:
                mask = master_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
                filtered_df = master_df[mask]
            else:
                filtered_df = master_df

            # Setup AgGrid options
            gb = GridOptionsBuilder.from_dataframe(filtered_df)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100)  # Pagination with page size 5
            gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
            gb.configure_grid_options(domLayout='normal')  # Normal layout to show pagination controls

            grid_options = gb.build()

            # Display grid with update mode to capture changes
            grid_response = AgGrid(
                filtered_df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                allow_unsafe_jscode=True,
                theme="alpine",  # 'streamlit', 'alpine', 'balham', 'material', ...
                enable_enterprise_modules=False,
                height=600,
                fit_columns_on_grid_load=True
            )

            edited_df = pd.DataFrame(grid_response['data'])

            # Show filtered and edited data count
            st.markdown(f"**Showing {len(edited_df)} rows (filtered & editable)**")

            # Download buttons for the filtered and edited data
            def to_csv(df):
                return df.to_csv(index=False).encode('utf-8')

            def to_excel(df):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='FilteredData')
                return output.getvalue()

            col1, col2 = st.columns(2)
            with col1:
                if search_term:
                    st.download_button("📥 Download CSV", data=to_csv(edited_df), file_name=f"db_keyword_{search_term}.csv", mime="text/csv")
                else:
                    st.download_button("📥 Download CSV", data=to_csv(edited_df), file_name="db_filtered.csv", mime="text/csv")
            with col2:
                if search_term:
                    st.download_button("📥 Download Excel", data=to_excel(edited_df), file_name=f"db_keyword_{search_term}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.download_button("📥 Download Excel", data=to_excel(edited_df), file_name="db_filtered.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    # Visualize menu
    elif selected == "Visualize":
        st.title("📊 PaC Data Visualization")
        st.set_page_config(layout="wide")
        if not os.path.exists(master_df_csv):
            st.error("""
                ❗ ERROR: No files found.\n 
                Go to 'Main Menu'-'Download PaC Files' and click 'Start Download' button to download all files and try again.
            """)
        else:
            # Check master_df; if empty, read master db file
            if master_df.empty:
                master_df = pd.read_csv(master_df_csv)

            st.header("📋 Data Profiling Report")
            target_cols = master_df.columns.to_list()
            # Remove columns with extremely long values
            no_profile_cols_ptn = re.compile(r"^(Secure|Insecure) Code (Example|Line) \d+$")
            profile_cols = [col for col in target_cols if not no_profile_cols_ptn.match(col)]
            profile_cols.remove("Query Document")
            profile_cols.remove("Related Document")
            profile_cols.remove("CheckovID")
            profile = ProfileReport(
                master_df[profile_cols],
                title="Master Data Profiling Report",
                explorative=True
            )
            profile.config.interactions.targets = profile_cols

            
            # Custom CSS to widen the report container inside the iframe
            custom_css = """
            <style>
            /* Override container width of pandas profiling report */
            .report-container {
                max-width: 100% !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
            /* Also fix margins to use almost full width */
            .container {
                width: 100% !important;
                max-width: 100% !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
            </style>
            """

            html_report = custom_css + profile.to_html()

            # Show profiling report as HTML component with wide width and fixed height
            st.components.v1.html(html_report, height=1200, scrolling=True, width=1200)

if __name__ == "__main__":
    app()