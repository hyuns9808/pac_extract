# ⚗️ PaC_Extract

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-informational.svg"/>
  <a href="https://python-poetry.org/">
    <img alt="Poetry" src="https://img.shields.io/badge/deps-managed%20by%20Poetry-60b?logo=poetry"/>
  </a>
</p>

> A blazing‑fast, developer‑friendly **Policy‑as‑Code (PaC)** file extraction tool.  
> Collects policies from **open‑source IaC scanners** directly from the source and creates a single unified database via **Pandas**.
> **Poetry‑powered** for clean dependency management and reproducible builds.

---

## 📚 Table of Contents

- [Quick Start](#-quick-start)
- [Why PaC Extract?](#-why-pac-extract)
- [Features](#-features)
- [Menus](#️-menus)
- [Policy Sources (Open‑Source Collectors)](#-policy-sources-opensource-collectors)
- [Roadmap](#️-roadmap)
- [FAQ](#-faq)
- [License](#-license)
- [Credits](#-credits)
- [Creator](#-creator)

---

## 🚀 Quick Start

This app is created via **Python and Streamlit** for its core functionality and UI.
**Poetry** is used for environment and dependency management.

To start, type in the following commands in order:

```bash
# If you do not have Poetry, use pipx to install Poetry
pipx install poetry
# Clone and install with Poetry (recommended)
git clone https://github.com/hyuns9808/pac_extract.git
cd pac_extract
poetry install

# Launch web application
poetry run streamlit run src/app.py
```

To run the app, simply create a virtual environment using Poetry by running the following command:
**poetry install**

Next, launch the web application:
**poetry run streamlit run src/app.py**

---

## ✨ Why PaC Extract?

Open-source IaC scanners are powerful, but each has its own PaC library with different rule format, execution model, and document style. Thus, there is a need for a combined database of policies for DevOps engineers to look up popular misconfigurations and its corresponding PaCs. **PaC‑Scanner** acts as a **policy hub** by:

- **Collects & normalizes policies** from popular open-source IaC scanners (e.g., **Checkov**, **KICS**, **Terrascan**, **Trivy**).
- **Creates a unified database** to look-up and compare what polices each open-source tool uses.
- **Streamlines results** into standardized outputs (**CSV**, **JSON**, **SQL**, **XLSX**).

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

## 🖥️ Menus

Within the sidebar, there are **four** menus:

| Menu          | Icon         | Description                                                                                                                                                         |
| ------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Home**      | :house:      | 🏃 Quick overview and essential info at a glance.                                                                                                                   |
| **Download**  | :arrow_down: | 📥 Download/update your raw PaC files and get most recent PaCs per tool <br> 🗂️ Save combined/individual PaC database as file(**CSV**, **JSON**, **SQL**, **XLSX**) |
| **Search**    | :mag:        | 🕹️ Search PaCs with specific keywords or filtering out data <br> 🗂️ Save search/filtered results as a **CSV** or **XLSX** file for closer examination               |
| **Visualize** | :bar_chart:  | 🗒️ Visualize statistics and details of the combined database                                                                                                        |

---

## 📥 Policy Sources (Open‑Source Collectors)

PaC_Extract **ingests policies** from popular open‑source IaC scanners, normalizes them, and creates a combined database via **pandas** which can be saved in various file formats.

PaC_Extract gets PaCs from open-source tools from two methods:

1. **Parsing information from tool's official documents**: By using a custom parser, directly get relative info from the official policy documents of each tools and create a database. Noted via **"Target"** category as **"Docs"** in the table below. This option is chosen when the tool's policies are written in custom format and thus for direct parsing from files requires excessive resources.
2. **Parsing information directly from tool's PaC files**: By using a custom parser, directly parse info from each PaC files within repo. Noted via **"Target"** category as **"Files"** in the table below. This option is chosen when the tool does not provide an exhaustive document on its polices. This tends to be more accurate than parsing information from the official document files, as sometimes the documents may be outdated.

Both modes are supported. However, in order to parse PaCs as accurately as possible, all tools are currently implemented via parsing information directly from tool's PaC files at GitHub.

| Tool                                                               | Target                                                                                                      | Notes                                                                          |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [Checkov](https://github.com/bridgecrewio/checkov)                 | [Docs](https://github.com/bridgecrewio/checkov/tree/main/docs/5.Policy%20Index)                             | Imports PaCs from Checkov's **official documentation** within repo.            |
| [KICS](https://github.com/Checkmarx/kics)                          | [Docs](https://github.com/Checkmarx/kics/tree/master/docs/queries)                                          | Imports PaCs from KICS **official documentation** within repo.                 |
| [Prisma Cloud Docs](https://github.com/hlxsites/prisma-cloud-docs) | [Docs](https://github.com/hlxsites/prisma-cloud-docs/tree/main/docs/en/enterprise-edition/policy-reference) | Imports PaCs from Prisma Cloud's **official documentation** within repo.       |
| [Terrascan](https://github.com/tenable/terrascan)                  | [Files](https://github.com/tenable/terrascan/tree/master/pkg/policies/opa/rego)                             | Parses PaCs **directly from Terrascan's raw Pac files**.                       |
| [Trivy](https://github.com/aquasecurity/trivy)                     | [Files](https://github.com/aquasecurity/trivy-checks/tree/main/checks)                                      | Parses PaCs **directly from Trivy's raw Pac files provided in separate repo**. |

Both combined and individual PaC databases for each tool is downloaded in the **"./pac_database"** directory.

> **Attribution:** Imported policies retain original IDs, titles, and references. See [LICENSES-THIRD-PARTY.md](./LICENSES-THIRD-PARTY.md).

---

## 🗺️ Roadmap

- ✅ Download all PaC information from Checkov, KICS, Terraform, and Trivy
- ✅ Aggregate policies from open‑source IaC scanners into unified PaC library
- ✅ Basic search functionality and pandas profile view
- 📊 Better visualization support
- 🗒️ Manually adding info for each NaN values within the DB which are not provided
- 🧬 Manual parsing of Checkov/KICS instead of using official documentation

Contribute ideas in [Discussions](https://github.com/hyuns9808/pac_extract/discussions).

---

## ❓ FAQ

**Why Poetry?**  
Poetry provides deterministic dependency resolution, locked environments, and reproducible builds, making CI/CD more predictable.

---

## 📜 License

Released under the **MIT License**. See [LICENSE](./LICENSE) for details.

---

## 🙌 Credits

Full credit for each open-source IaC scanning tool for maintaining their PaC libraries public:  
**Checkov**, **KICS**, **Terrascan**, and **Trivy**.
Honorable mention to the broader Open‑Source Security and IaC communities, and **Streamlit** for letting this be more than a simple CLI tool.

---

## ✨ Creator

<div align="center" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; width: 100%;">
  
  <!-- Profile Image -->
  <img src="https://github.com/hyuns9808.png?size=300" 
       alt="Majestic Cat" 
       title="Majestic Cat"
       style="border-radius: 20px; max-width: 300px; height: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">

  <!-- Fun Fact -->
  <p style="font-size: 1.1rem; margin-top: 12px;">
    🐾 Fun fact: This majestic beast is a stray I met at 
    <a href="https://maps.app.goo.gl/78d8uQ19jJc6BPx88" target="_blank" style="color: #ff9800; text-decoration: none;">
      Gamcheon Culture Village
    </a>
  </p>

  <!-- Links -->
  <h3>
    <a href="https://github.com/hyuns9808" style="color: #4cafef; text-decoration: none;">💻 Calvin(Hyunsoo) Yang</a>
  </h3>

</div>
