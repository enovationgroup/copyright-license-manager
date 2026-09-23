"""Template functions"""

import re

# Lines that must stay at the very top of a file, above the copyright header.
# Every pattern consumes whole lines, starting at the beginning of a line.
SHEBANG = re.compile(r"#![^\n]*\n?")
CHARSET = re.compile(r"@charset[^;\n]*;[^\n]*\n?")
XML_DECLARATION = re.compile(r"<\?xml(?s:.*?)\?>[^\n]*\n?")
DOCTYPE = re.compile(r"<!(?i:doctype)[^>]*>[^\n]*\n?")

# Comment styles, shared by every source extension that uses them
JAVA = {
    "start": "/*",
    "char": "*",
    "line": " * ",
    "end": " */",
    "divider": True,
    "license": {"start": "---", "end": "---"},
}

CSHARP = {
    "start": "/*************************************************************************",
    "char": "*",
    "line": " * ",
    "end": " */",
    "divider": True,
    "license": {"start": "---", "end": "---"},
}

HASH = {
    "start": "#",
    "char": "#",
    "line": "# ",
    "end": "#",
    "divider": False,
    "license": {"start": "---", "end": "---"},
}

SQL = {
    "start": "/*",
    "char": "",
    "line": "  ",
    "end": "*/",
    "divider": False,
    "license": {"start": "---", "end": "---"},
}

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
    """Create the comment configuration of a source extension

    Every extension gets its own copy, so changing one of them can never
    affect another extension that shares the same comment style.

    Parameters
    ----------
    comment_style
        One of the comment styles above
    prologue
        Patterns of the lines that must stay above the header

    Returns
    -------
        The comment configuration of the extension

    """
    return {
        **comment_style,
        "license": dict(comment_style["license"]),
        "prologue": list(prologue),
    }


comments = {
    "java": style(JAVA),
    "ts": style(BANNER, [SHEBANG]),
    "cs": style(CSHARP),
    "py": style(HASH),
    "sql": style(SQL),
    # JavaScript
    "js": style(BANNER, [SHEBANG]),
    "mjs": style(BANNER, [SHEBANG]),
    "cjs": style(BANNER, [SHEBANG]),
    "jsx": style(BANNER),
    "tsx": style(BANNER),
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
    "vue": style(MARKUP),
    "svelte": style(MARKUP),
}

licenses = {"default": "All rights reserved."}

# Source extensions clmgr can process
sources = list(comments)

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
