"""Template functions"""

comments = {
    "java": {
        "start": "/*",
        "char": "*",
        "line": " *",
        "end": " */",
        "license": {"start": " * ---", "end": " * ---"},
    },
    "sh": {
        "start": "#",
        "char": "#",
        "line": "#",
        "end": "#",
    },
}

licenses = {"default": "All rights reserved."}


def template(inception, year, name, locality, country):
    return eval(
        f"f'Copyright (c) {inception} - {year} [{name} - {locality} - {country}]'"
    )
