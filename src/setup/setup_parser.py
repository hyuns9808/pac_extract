'''
File that stores all functions related to creating the argument parser
'''
import argparse

def parser_setup():
    '''Setup argument parser'''
    parser = argparse.ArgumentParser(
                        prog='PaC_Extract',
                        description='A developer‑friendly Policy‑as‑Code (PaC) file extraction tool for Terraform.',
                        )
    # --update/-u = True to update all repos
    parser.add_argument('-u', '--update', action='store_true',
                        help="Enable to update all repos")
    # --tools/-t = List of tools to update
    parser.add_argument('-t', '--tools', nargs="+",
                        help="List of tools to update repos (only allowed with --update)")
    # --tools/-t = List of tools to update
    # parser.add_argument('--id', required=True, help='Partial ID to match')
    # --iac/-i = Type of IaC to look for(Terraform, CloudFormation, etc.)
    parser.add_argument('-i','--iac', required=True, help='IaC type (e.g., Terraform)')
    # --keyword/-k = Partial keyword to look for in either resource name or description. Returns any matches.
    parser.add_argument('-k','--keyword', required=True, help='Keyword to match in Entity or Policy')
    return parser