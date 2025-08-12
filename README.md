# ⚗️ PaC_Extract

> A blazing‑fast, developer‑friendly **Policy‑as‑Code (PaC)** file extraction tool for **Terraform**.  
> Collects policies from **open‑source IaC scanners** directly from the source and creates a single unified database via **Pandas**.  
> **Poetry‑powered** for clean dependency management and reproducible builds.

<p align="center">
  <img src="docs/assets/banner.png" alt="PaC-Scanner banner" width="720"/>
</p>

<p align="center">
  <a href="https://github.com/yourorg/pac-scanner/actions">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/yourorg/pac-scanner/ci.yml?label=CI"/>
  </a>
  <a href="https://pypi.org/project/pac-scanner/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/pac-scanner.svg"/>
  </a>
  <img alt="Python" src="https://img.shields.io/pypi/pyversions/pac-scanner.svg"/>
  <img alt="License" src="https://img.shields.io/badge/license-MIT-informational.svg"/>
  <a href="https://python-poetry.org/">
    <img alt="Poetry" src="https://img.shields.io/badge/deps-managed%20by%20Poetry-60b?logo=poetry"/>
  </a>
  <a href="https://hub.docker.com/r/yourorg/pac-scanner">
    <img alt="Docker pulls" src="https://img.shields.io/docker/pulls/yourorg/pac-scanner.svg"/>
  </a>
</p>

---

## 📚 Table of Contents

- [Why PaC_Scanner?](#-why-pac-scanner)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Writing Policies](#-writing-policies)
- [Policy Sources (Open‑Source Collectors)](#-policy-sources-open-source-collectors)
- [Reports](#-reports)
- [CI/CD](#-cicd)
- [Development](#-development)
- [Roadmap](#-roadmap)
- [FAQ](#-faq)
- [License](#-license)
- [Credits](#-credits)

---

## ✨ Why PaC_Scanner?

Traditional IaC scanners are powerful, but each has its own PaC library with different rule format, execution model, and report style. **PaC‑Scanner** acts as a **policy hub** by:

- **Collects & normalizes policies** from popular open-source IaC scanners (e.g., **Checkov**, **tfsec**, **Terrascan**, **kube‑score**).
- **Unifies evaluation** through a single, consistent engine (OPA/Rego, JSON logic, and YAML checks).
- **Streamlines results** into standardized outputs (CLI, **JSON**, **SARIF**, **HTML**).

---

## 🌟 Features

- ⚡ **Fast & Lightweight** – Scans large repos in seconds.
- 🛡️ **Extensible Policy Lookups** – Find all PaC files of each open-source tool, some which do not provide official documents for.
- 🌍 **Broad IaC Coverage** – Terraform, CloudFormation, Kubernetes, Docker, Helm charts, generic YAML/JSON.
- 📚 **Curated PaC Library** – Aggregates rules from open‑source IaC scanners into one pandas dataframe.
- 🧠 **Smart Normalization** – Deduplicates, tags, and versions imported rules for consistency.
- 📊 **Rich Reports** – Save results in various file formats, such as **.csv, .sql, .json, .xlsx.**
- 🐍 **Poetry‑Powered** – Reproducible environments & dependency pinning with **Poetry**.
- 🧑 **Straightforward UI** - Based on Streamlit, launch an easy-to-use UI to download, search and look up data.

---

## 🚀 Quick Start

```bash
# Clone and install with Poetry (recommended)
git clone https://github.com/hyuns9808/pac_extract.git
cd pac_extract
poetry install

# Launch web application
poetry run streamlit run src/app.py
```

---

## 📦 Installation

### Using Poetry (recommended)
```bash
poetry install
```

> **Note:** When running through Poetry, prefix commands with `poetry run ...`.

---

## 🖥️ Usage


---



## 📥 Policy Sources (Open‑Source Collectors)

PaC‑Scanner can **ingest policies** from popular open‑source IaC scanners, normalize them, and tag them with a consistent schema:

| Source       | Importer | Notes |
|--------------|----------|-------|
| Checkov      | `checkov` | Imports built‑in checks and maps severities/tags. |
| KICS        | `kics`   | Converts rules and remediation links. |
| Terrascan    | `terrascan` | Normalizes categories and resource filters. |
| Trivy   | `trivy` | Adapts findings to K8s resource schema. |

Go to the "Download PaC Files" menu to download all information per each tool.

> **Attribution:** Imported policies retain original IDs, titles, and references. See [LICENSES-THIRD-PARTY.md](./LICENSES-THIRD-PARTY.md).

---

## 🗺️ Roadmap

- ✅ Terraform, CloudFormation, Kubernetes support  
- ✅ Aggregate policies from open‑source IaC scanners into unified PaC library  
- 🔄 Cloud provider **live‑state** scanning (AWS, Azure, GCP)  
- 📡 Remote policy registries (fetch from Git/OCI)  
- 🖥️ IDE inline feedback (VSCode/JetBrains extensions)  
- 🧬 Policy graph & dependency awareness  

Contribute ideas in [Discussions](https://github.com/yourorg/pac-scanner/discussions) or open a [feature request](https://github.com/yourorg/pac-scanner/issues/new?template=feature_request.md).

---

## ❓ FAQ

**Why Poetry?**  
Poetry provides deterministic dependency resolution, locked environments, and reproducible builds, making CI/CD more predictable.

**Can I disable certain imported rules?**  
Yes — use `exclude_rules` patterns or disable an entire collector in `.pac-scanner.yaml`.

**What if I already use Checkov/tfsec?**  
Great! Keep them. PaC‑Scanner can **import** their policies so your teams get a single pane of glass for rules, severities, and outputs.

---

## 📜 License

Released under the **MIT License**. See [LICENSE](./LICENSE) for details.

---

## 🙌 Credits

This project stands on the shoulders of giants:  
**Checkov**, **tfsec**, **Terrascan**, **kube‑score**, **OPA/Regal**, and the broader Open‑Source Security and IaC communities.  
We thank the authors and maintainers of these projects and preserve attribution in imported rules.

---

> 🛠 Built for developers who care about security **before** production.
