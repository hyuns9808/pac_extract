from .tool_parsers.get_checkov import get_checkov_pac
from .tool_parsers.get_kics import get_kics_pac
from .tool_parsers.get_terrascan import get_terrascan_pac
from .tool_parsers.get_trivy import get_trivy_pac

# Dictionary used for dispatch
TOOLS = {
    "Checkov": get_checkov_pac,
    "KICS": get_kics_pac,
    "Terrascan": get_terrascan_pac,
    "Trivy": get_trivy_pac
}

def get_pac_of_tool(name: str, /, *args, **kwargs):
    '''
    Directs which function to call based on given tool name.
    Assumes ALL tool names given are VALID(supported, no typos etc).
    '''
    return TOOLS[name](*args, **kwargs)

'''
if __name__ == "__main__":
    get_pac_of_tool("Terrascan")
'''