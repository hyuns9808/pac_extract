# IaC_Extract

<h1 align="center" style="border-bottom: none;">⚗️ IaC_Extract</h1>
<h3 align="center">Fully automated PaC(Policy as Code) extraction from open-source IaC(Infrastructure as Code) tools</h3>

**IaC_Extract** automates the tiresome process of locating relevant policies from popular open-source IaC(Infrastructure as Code) tools.

Although most open-source IaC scanning tools provide information regarding what policies they use to scan IaC files, there is no combined document or process to collect such information.

**IaC_Extract** directly pools all relevant policies from the following 4 popular open-source IaC scanning tools:
1. [regula](https://github.com/fugue/regula)
2. [terrascan](https://github.com/tenable/terrascan)
3. [checkov](https://github.com/bridgecrewio/checkov)
4. [tfsec](https://github.com/aquasecurity/tfsec)

This allows anyone who is planning to create a database for PaC files gather insight of what policies are popular among 

## Highlights

- Searches all policies of four open-source IaC scanning tools related to user input
- Saves them in separate excel(.xlsx) files per tool
- Saves the following properties per policy:
    - RuleID
        - Identification code assigned from each tool per policy
    - Title
        - Brief description of what the policy checks
    - File Location
        - PaC file location from downloaded repository
    - {search_String} Specified
        - Whether there is a specific policy category dedicated to the user's input string
    - Severity
        - How severe the issue detected by the policy is regarding security or infrastructure integrity
    - Summary
        - Detailed description of what the policy checks

## Requirements

**IaC_Extract** requires the following conditions:

- A computer with at least 100MB of free memory
- The following Python packages:
    - requests
    - xlsxwriter
    - pathlib (if using Python version lower than 3.4+)

## How does it work?

**IaC_Extract** downloads the repositories provided by all four open-source tools. 
Then it locates the policy files within the open source tools and parses them via RegEx.
All parsed policies are finally saved as .xlsx files per tool.

## Creator
[![Hyunsoo Yang](https://github.com/hyuns9808.png?size=100)](https://github.com/hyuns9808)
Check out my [personal website!](https://hyuns9808.github.io/calya/)