"""Template functions"""

import re

# Lines that must stay at the very top of a file, above the copyright header.
# Every pattern consumes whole lines, starting at the beginning of a line.
SHEBANG = re.compile(r"#![^\n]*\n?")
CHARSET = re.compile(r"@charset[^;\n]*;[^\n]*\n?")
XML_DECLARATION = re.compile(r"<\?xml(?s:.*?)\?>[^\n]*\n?")
DOCTYPE = re.compile(r"<!(?i:doctype)[^>]*>[^\n]*\n?")

# Comment styles shared by several source extensions
BANNER = {
    "start": "/*! *****************************************************************************",
    "char": "*",
    "line": "",
    "end": "****************************************************************************** */",
    "divider": False,
    "license": {"start": "---", "end": "---"},
}

SLASH = {
    "start": "//",
    "char": "//",
    "line": "// ",
    "end": "//",
    "divider": False,
    "license": {"start": "---", "end": "---"},
}

# XML based markup does not allow "--" inside a comment, so the license
# markers use "===" to keep the header valid for every markup flavour.
MARKUP = {
    "start": "<!--",
    "char": "",
    "line": "  ",
    "end": "-->",
    "divider": False,
    "license": {"start": "===", "end": "==="},
}


def style(comment_style, prologue=()):
    """Combine a comment style with the prologue patterns of an extension"""
    return {**comment_style, "prologue": list(prologue)}


comments = {
    "java": {
        "start": "/*",
        "char": "*",
        "line": " * ",
        "end": " */",
        "divider": True,
        "license": {"start": "---", "end": "---"},
    },
    "ts": BANNER,
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
    "sh": {
        "start": "#",
        "char": "#",
        "line": "#",
        "end": "#",
        "prologue": [SHEBANG],
    },
    "sql": {
        "start": "/*",
        "char": "",
        "line": "  ",
        "end": "*/",
        "divider": False,
        "license": {"start": "---", "end": "---"},
    },
    # JavaScript
    "js": style(BANNER, [SHEBANG]),
    "mjs": style(BANNER, [SHEBANG]),
    "cjs": style(BANNER, [SHEBANG]),
    "jsx": style(BANNER, [SHEBANG]),
    "tsx": style(BANNER, [SHEBANG]),
    # Stylesheets
    "css": style(BANNER, [CHARSET]),
    "scss": style(BANNER, [CHARSET]),
    "less": style(BANNER, [CHARSET]),
    # The indented syntax ends a /* comment at the first line that is not
    # indented, so it can only use line comments.
    "sass": style(SLASH, [CHARSET]),
    # Markup
    "html": style(MARKUP, [XML_DECLARATION, DOCTYPE]),
    "htm": style(MARKUP, [XML_DECLARATION, DOCTYPE]),
    "vue": MARKUP,
    "svelte": MARKUP,
}

licenses = {"default": "All rights reserved."}

# Source extensions clmgr can process. "sh" has a comment style above, but no
# license handling and no header implementation yet, so it is not offered.
sources = [ext for ext in comments if ext != "sh"]

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
