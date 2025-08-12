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

Traditional IaC scanners are powerful, but each has its own rule format, execution model, and report style. **PaC‑Scanner** acts as a **policy hub**:

- **Collects & normalizes policies** from popular open-source IaC scanners (e.g., **Checkov**, **tfsec**, **Terrascan**, **kube‑score**).
- **Unifies evaluation** through a single, consistent engine (OPA/Rego, JSON logic, and YAML checks).
- **Streamlines results** into standardized outputs (CLI, **JSON**, **SARIF**, **HTML**).

---

## 🌟 Features

- ⚡ **Fast & Lightweight** – Scans large repos in seconds.
- 🛡️ **Extensible Policy Engine** – Author rules in **Rego**, JSON logic, or simple **YAML**.
- 🌍 **Broad IaC Coverage** – Terraform, CloudFormation, Kubernetes, Docker, Helm charts, generic YAML/JSON.
- 📚 **Curated PaC Library** – Aggregates rules from open‑source IaC scanners into one framework.
- 🧠 **Smart Normalization** – Deduplicates, tags, and versions imported rules for consistency.
- 🏗️ **CI/CD Ready** – GitHub Actions, GitLab CI, Jenkins, CircleCI.
- 📊 **Rich Reports** – JSON, **SARIF** (Code Scanning), HTML dashboards, or concise CLI output.
- 🔌 **Pluggable Rulesets** – Use built‑ins or your own bundles.
- 🐍 **Poetry‑Powered** – Reproducible environments & dependency pinning with **Poetry**.

---

## 🚀 Quick Start

```bash
# Clone and install with Poetry (recommended)
git clone https://github.com/yourorg/pac-scanner.git
cd pac-scanner
poetry install

# Run your first scan
poetry run pac-scanner scan ./iac
```

---

## 📦 Installation

### Using Poetry (recommended)
```bash
poetry install
```

### Using pip
```bash
pip install pac-scanner
```

### Using Homebrew (macOS/Linux)
```bash
brew install pac-scanner
```

### Using Docker
```bash
docker run --rm -v $(pwd):/scan yourorg/pac-scanner scan .
```

> **Note:** When running through Poetry, prefix commands with `poetry run ...`.

---

## 🖥️ Usage

### Scan a directory
```bash
poetry run pac-scanner scan ./iac
```

### Apply custom policy bundles
```bash
poetry run pac-scanner scan . --policy-bundle ./policies
```

### Select input types explicitly
```bash
poetry run pac-scanner scan ./ --types terraform,kubernetes
```

### Fail the build on severity threshold
```bash
poetry run pac-scanner scan ./ --fail-on high
```

### Output results in JSON or SARIF
```bash
poetry run pac-scanner scan ./ --output json > results.json
poetry run pac-scanner scan ./ --output sarif > results.sarif
```

### HTML report
```bash
poetry run pac-scanner scan ./ --output html --out-file report.html
```

---

## ⚙️ Configuration

Create a `.pac-scanner.yaml` at repo root:

```yaml
# .pac-scanner.yaml
inputs:
  paths:
    - ./iac
    - ./k8s
  types: [terraform, kubernetes, docker]
policies:
  bundles:
    - ./policies  # your custom bundle(s)
  sources:
    checkov: enabled
    tfsec: enabled
    terrascan: enabled
    kube_score: enabled
  exclude_rules:
    - experimental-*
    - deprecated-*
report:
  format: sarif        # cli|json|sarif|html
  fail_on: high        # none|low|medium|high|critical
  out_file: results.sarif
runtime:
  parallelism: 8
  cache_dir: ./.pac-cache
```

---

## 🧑‍💻 Writing Policies

You can write policies in **OPA/Rego**, JSON logic, or simple **YAML** checks.

**YAML example**
```yaml
id: aws-sg-no-80
title: Disallow 0.0.0.0/0 ingress on port 80
severity: high
resource: aws_security_group
check:
  ingress:
    - port: 80
      cidr: 0.0.0.0/0
```

**Rego example (`policies/network/sg.rego`)**
```rego
package pac.network

deny[res] {
  some sg
  input.resource.type == "aws_security_group"
  sg := input.resource.config
  ingress := sg.ingress[_]
  ingress.from_port <= 80
  ingress.to_port >= 80
  ingress.cidr_blocks[_] == "0.0.0.0/0"
  res := {
    "id": "aws-sg-no-80",
    "message": sprintf("Security group allows 0.0.0.0/0 on port 80 at %s", [input.resource.filepath]),
    "severity": "high"
  }
}
```

---

## 📥 Policy Sources (Open‑Source Collectors)

PaC‑Scanner can **ingest policies** from popular open‑source IaC scanners, normalize them, and tag them with a consistent schema:

| Source       | Importer | Notes |
|--------------|----------|-------|
| Checkov      | `checkov` | Imports built‑in checks and maps severities/tags. |
| tfsec        | `tfsec`   | Converts rules and remediation links. |
| Terrascan    | `terrascan` | Normalizes categories and resource filters. |
| kube‑score   | `kube_score` | Adapts findings to K8s resource schema. |

Example enabling collectors:

```bash
poetry run pac-scanner fetch-policies   --enable checkov,tfsec,terrascan,kube_score   --dest ./external-policies
```

> **Attribution:** Imported policies retain original IDs, titles, and references. See [LICENSES-THIRD-PARTY.md](./LICENSES-THIRD-PARTY.md).

---

## 📊 Reports

**CLI summary**
```text
✅ Passed: 153   ❌ Failed: 7   ⏭ Skipped: 12
High: 3   Medium: 2   Low: 2
```

**JSON**
```bash
poetry run pac-scanner scan ./ --output json > results.json
```

**SARIF (GitHub Code Scanning)**
```bash
poetry run pac-scanner scan ./ --output sarif > results.sarif
```

**HTML**
```bash
poetry run pac-scanner scan ./ --output html --out-file report.html
```

---

## 🔗 CI/CD

### GitHub Actions

```yaml
name: pac-scan
on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Poetry
        uses: abatilo/actions-poetry@v2

      - name: Configure Poetry
        run: |
          poetry config virtualenvs.in-project true
          poetry install --no-interaction --no-ansi

      - name: Run PaC-Scanner
        run: poetry run pac-scanner scan ./iac --output sarif > results.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

### GitLab CI

```yaml
pac_scan:
  image: python:3.11
  script:
    - pip install poetry
    - poetry install --no-interaction --no-ansi
    - poetry run pac-scanner scan ./ --fail-on high
  artifacts:
    paths:
      - results.sarif
```

---

## 🧰 Development

```bash
# 1) Install dependencies (creates .venv via Poetry)
poetry install

# 2) Run unit tests
poetry run pytest -q

# 3) Lint & type-check
poetry run ruff check .
poetry run mypy src

# 4) Run CLI locally
poetry run pac-scanner --help
```

**Useful Poetry scripts** (in `pyproject.toml`)
```toml
[tool.poetry.scripts]
pac-scanner = "pac_scanner.cli:app"
```

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
