"""Template functions"""

comments = {
    "java": {
        "start": "/*",
        "char": "*",
        "line": " * ",
        "end": " */",
        "divider": True,
        "license": {"start": "---", "end": "---"},
    },
    "ts": {
        "start": "/*! *****************************************************************************",
        "char": "*",
        "line": "",
        "end": "****************************************************************************** */",
        "divider": False,
        "license": {"start": "---", "end": "---"},
    },
    "cs": {
        "start": "/*************************************************************************",
        "char": "*",
        "line": " * ",
        "end": " */",
        "divider": True,
        "license": {"start": "---", "end": "---"},
    },
    "py": {
        "start": "#",
        "char": "#",
        "line": "# ",
        "end": "#",
        "divider": False,
        "license": {"start": "---", "end": "---"},
    },
    "sh": {"start": "#", "char": "#", "line": "#", "end": "#"},
}

licenses = {"default": "All rights reserved."}


# format the copyright statement
def template(copyright_format, inception, year, name, locality, country):
    return eval(f"f'{copyright_format}'")
