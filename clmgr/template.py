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
    "sql": {
        "start": "/*",
        "char": "",
        "line": "  ",
        "end": "*/",
        "divider": False,
        "license": {"start": "---", "end": "---"},
    },
}

licenses = {"default": "All rights reserved."}

# Source extensions clmgr can process. "sh" has a comment style above, but no
# license handling and no header implementation yet, so it is not offered.
sources = ["cs", "java", "py", "sql", "ts"]

# Placeholders a copyright format may use
placeholders = ["inception", "year", "name", "locality", "country"]


# format the copyright statement
def template(copyright_format, inception, year, name, locality, country):
    return copyright_format.format(
        inception=inception,
        year=year,
        name=name,
        locality=locality,
        country=country,
    )
