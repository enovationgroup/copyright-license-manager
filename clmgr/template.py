"""Template functions"""

import re

# Lines that must stay at the very top of a file, above the copyright header.
# Every pattern consumes whole lines, starting at the beginning of a line. A
# line ends with "\r\n", "\n" or "\r", as the file was written.
REST_OF_LINE = r"[^\r\n]*(?:\r\n|\r|\n)?"
SHEBANG = re.compile(r"#!" + REST_OF_LINE)
# PEP 263 requires the encoding declaration on the first or second line
CODING = re.compile(r"[ \t\f]*#[^\r\n]*?coding[:=]" + REST_OF_LINE)
# The indented syntax of Sass has no semicolon after the rule
CHARSET = re.compile(r"@charset" + REST_OF_LINE)
XML_DECLARATION = re.compile(r"<\?xml(?s:.*?)\?>" + REST_OF_LINE)
# Whitespace is allowed in front of a doctype, it is kept above the header
DOCTYPE = re.compile(r"\s*<!(?i:doctype)[^>]*>" + REST_OF_LINE)

# Block comments that are recognised as an existing header, in files that use
# a different comment style for new headers. They are only recognised when they
# hold a copyright statement, so a leading pragma or documentation comment is
# never mistaken for the header. They only describe how to find and update a
# header, so they have no license or divider settings and are not passed to
# style().
C_BLOCK = {"start": "/*", "char": "*", "line": "  ", "end": "*/"}

# The indented syntax of Sass ends a /* comment at the first line that is not
# indented, the closing */ is optional. A closing */ that clmgr writes must be
# indented as well, at the start of a line it would be read as a new rule.
SASS_BLOCK = {**C_BLOCK, "indented": True, "close": "  */"}

# Line comments a language supports next to the style of its headers. They are
# never used as the header, clmgr only warns when one holds a copyright
# statement that it leaves unchanged.
SLASH_LINES = {"start": "//", "end": "//"}
DASH_LINES = {"start": "--", "end": "--"}

# Comment styles, shared by every source extension that uses them
JAVA = {
    "start": "/*",
    "char": "*",
    "line": " * ",
    "end": " */",
    "divider": True,
    "license": {"start": "---", "end": "---"},
    "other_comments": [SLASH_LINES],
}

CSHARP = {
    "start": "/*************************************************************************",
    "char": "*",
    "line": " * ",
    "end": " */",
    "divider": True,
    "license": {"start": "---", "end": "---"},
    "other_comments": [SLASH_LINES],
    "legacy": [C_BLOCK],
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
    "other_comments": [DASH_LINES],
}

BANNER = {
    "start": "/*! *****************************************************************************",
    "char": "*",
    "line": "",
    "end": "****************************************************************************** */",
    "divider": False,
    "license": {"start": "---", "end": "---"},
    "other_comments": [SLASH_LINES],
    "legacy": [C_BLOCK],
}

SASS = {
    "start": "//",
    "char": "//",
    "line": "// ",
    "end": "//",
    "divider": False,
    "license": {"start": "---", "end": "---"},
    "legacy": [SASS_BLOCK],
    # Leading line comments are often directives, such as
    # // stylelint-disable-next-line, which must stay where they are
    "copyright_only": True,
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
    "markup": True,
    # Leading markup comments are often directives, such as
    # <!-- eslint-disable --> or conditional comments
    "copyright_only": True,
    # The comments of a <script> or <style> element
    "other_comments": [C_BLOCK, SLASH_LINES],
}


def style(comment_style, prologue=()):
    """Create the comment configuration of a source extension

    Every extension gets its own copy, so changing one of them can never
    affect another extension that shares the same comment style.

    Parameters
    ----------
    comment_style
        One of the comment styles above that new headers are written in,
        so not C_BLOCK or SASS_BLOCK
    prologue
        Patterns of the lines that must stay above the header

    Returns
    -------
        The comment configuration of the extension

    """
    return {
        "markup": False,
        "copyright_only": False,
        **comment_style,
        "license": dict(comment_style["license"]),
        "legacy": [dict(legacy) for legacy in comment_style.get("legacy", [])],
        "other_comments": [
            dict(other) for other in comment_style.get("other_comments", [])
        ],
        "prologue": list(prologue),
    }


comments = {
    "java": style(JAVA),
    "ts": style(BANNER, [SHEBANG]),
    "cs": style(CSHARP),
    "py": style(HASH, [SHEBANG, CODING]),
    "sql": style(SQL),
    # JavaScript. Runtimes such as Bun and tsx also run jsx and tsx files as
    # scripts, and a first line starting with #! cannot be anything else.
    "js": style(BANNER, [SHEBANG]),
    "mjs": style(BANNER, [SHEBANG]),
    "cjs": style(BANNER, [SHEBANG]),
    "jsx": style(BANNER, [SHEBANG]),
    "tsx": style(BANNER, [SHEBANG]),
    # Stylesheets. CSS has no // comments, the warning about a copyright in
    # one only applies to SCSS and LESS.
    "css": style(BANNER, [CHARSET]),
    "scss": style(BANNER, [CHARSET]),
    "less": style(BANNER, [CHARSET]),
    # New headers use line comments: the indented syntax ends a /* comment at
    # the first line that is not indented, which the banner layout is not.
    "sass": style(SASS, [CHARSET]),
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


def statements(copyright_format, legal_entities, year):
    """Format the copyright statement of every legal entity

    The copyright of an entity ends in the inception year of the entity that
    follows it, the copyright of the last entity ends in the given year.

    Parameters
    ----------
    copyright_format
        The format of a copyright statement
    legal_entities
        The legal entities of the configuration, oldest first
    year
        The year the copyright of the last entity ends in

    Returns
    -------
        The copyright statements, in the order of the legal entities

    """
    ends = [entity["inception"] for entity in legal_entities[1:]] + [year]

    return [
        template(
            copyright_format,
            entity["inception"],
            end,
            entity["name"],
            entity["locality"],
            entity["country"],
        )
        for entity, end in zip(legal_entities, ends)
    ]


# format the copyright statement
def template(copyright_format, inception, year, name, locality, country):
    return copyright_format.format(
        inception=inception,
        year=year,
        name=name,
        locality=locality,
        country=country,
    )
