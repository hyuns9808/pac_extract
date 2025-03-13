# IaC_Extract

<h1 align="center" style="border-bottom: none;">⚗️ IaC_Extract</h1>
<h3 align="center">Fully automated PaC(Policy as Code) extraction from open-source IaC(Infrastructure as Code) tools</h3>

**IaC_Extract** automates the tiresome process of locating relevant PaC(Policy as Code) files from popular open-source IaC(Infrastructure as Code) tools.

Although most open-source IaC scanning tools provide information regarding policies they use to scan IaC files, there is no combined document or process to collect such information.

**IaC_Extract** directly pools all relevant PaCs from the following 4 popular open-source IaC scanning tools:
1. [regula](https://github.com/fugue/regula)
2. [terrascan](https://github.com/tenable/terrascan)
3. [checkov](https://github.com/bridgecrewio/checkov)
4. [tfsec](https://github.com/aquasecurity/tfsec)

This allows anyone planning to create a database for PaC files to gather insight into what PaCs popular open-source IaC tools use!

## Highlights

- Searches all PaCs of four open-source IaC scanning tools related to user input
- Saves them in separate excel(.xlsx) files per tool
- Saves the following properties per policy:
    - RuleID
        - Identification code assigned from each tool per policy
    - Title
        - Brief description of what the policy checks
    - File Location
        - PaC file location from the downloaded repository
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
Next, it locates the policy files within the open-source tools and parses them via RegEx.
Finally, all parsed policies are saved as .xlsx files per tool.

## Creator

<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; height: 100vh;">
    <img src="https://github.com/hyuns9808.png?size=300" alt="Cute, majestic cat I found" title="Majestic Cat" style="max-width: 100%; height: auto;">
    <p>Fun fact: this majestic beast is a stray that I met at <a href="https://maps.app.goo.gl/78d8uQ19jJc6BPx88">Gamcheon Culture Village!</a></p>
</div>

<h3 align="center">
    <a href="https://github.com/hyuns9808">Calvin(Hyunsoo) Yang</a>
</h3>
<h3 align="center">
    Check out my <a href="https://hyuns9808.github.io/calya/">personal website!</a>
</h3>