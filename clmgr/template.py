comments = {
    "java": {"start": "/*", "char": "*", "line": " *", "end": " */"},
    "sh": {
        "start": "###############################################################################",
        "char": "#",
        "line": "#",
        "end": "#",
    },
}


def template(inception, year, name, locality, country):
    return eval(
        f"f'Copyright (c) {inception} - {year} [{name} - {locality} - {country}]'"
    )
