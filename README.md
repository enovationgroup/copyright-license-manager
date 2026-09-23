# Copyright License Manager

[![PyPI](https://img.shields.io/pypi/v/clmgr)](https://img.shields.io/pypi/v/clmgr)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/clmgr)](https://pypi.org/project/clmgr/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/clmgr)](https://pypi.org/project/clmgr/)
[![PyPI - Format](https://img.shields.io/pypi/format/clmgr)](https://pypi.org/project/clmgr/)
[![PyPI - License](https://img.shields.io/pypi/l/clmgr)](https://pypi.org/project/clmgr/)
[![GitHub Actions - CI](https://github.com/enovationgroup/copyright-license-manager/workflows/CI/badge.svg)](https://github.com/enovationgroup/copyright-license-manager/actions/workflows/ci.yaml/badge.svg)
[![GitHub Actions - pre-commit](https://github.com/enovationgroup/copyright-license-manager/actions/workflows/pre-commit.yaml/badge.svg)](https://github.com/enovationgroup/copyright-license-manager/actions/workflows/pre-commit.yaml/badge.svg)
[![Codecov](https://img.shields.io/codecov/c/gh/enovationgroup/copyright-license-manager)](https://img.shields.io/codecov/c/gh/enovationgroup/copyright-license-manager)

A cli tool for easy management of copyright and licenses in source code headers.

## Installation

```shell
pip install clmgr
```

## Features

Current supported languages

- C#
- Java
- Python
- SQL
- TypeScript
- JavaScript (`js`, `mjs`, `cjs`, `jsx`, `tsx`)
- Stylesheets (`css`, `scss`, `sass`, `less`)
- Markup (`html`, `htm`, `vue`, `svelte`)

## Usage

Basic usage:

```shell
clmgr -c path/to/config.yml -d path/to/source/directory

Options:

-c, --config FILE     Path to the configuration file (default: copyright.yml)
-d, --dir DIR         Input directory to process (default: current working directory)
-i, --file FILE       Process a single input file
--region REGION       Copyright search region (default: 10)
-n, --dry-run         Report which files would change without writing them
--check               Implies --dry-run; exit with 1 when a file would change
--diff                Print a unified diff for every file that is changed
--debug               Enable verbose logging
--version             Show version information
```

### Arguments

| Argument            | Default                   | Description                                                      |
| ------------------- | ------------------------- | ---------------------------------------------------------------- |
| `-c, --config FILE` | `copyright.yml`           | Path to the configuration file                                   |
| `-i, --file FILE`   | None                      | Path to a single input file to process                           |
| `-d, --dir DIR`     | Current working directory | Input directory to process                                       |
| `--region REGION`   | `10`                      | Copyright search region                                          |
| `-n, --dry-run`     | false                     | Report which files would change without writing them             |
| `--check`           | false                     | Implies `--dry-run`; exit with `1` when a file would change      |
| `--diff`            | false                     | Print a unified diff for every file that is changed              |
| `--debug`           | false                     | Enable verbose logging                                           |
| `--version`         | N/A                       | Show version information and exit                                |

### Dry run

`--dry-run` reports which files clmgr would change without modifying anything on
disk. This is useful to verify the `include` and `exclude` patterns of a project:

```shell
clmgr --dry-run
```

```text
would add to src/main/java/com/example/Application.java
would update src/main/java/com/example/Service.java
up to date   src/main/java/com/example/Repository.java
1 file: Copyright would be added
1 file: Copyright would be updated
1 file: Copyright up to date
```

Every scanned file is reported, so a dry run also shows what the `source`,
`include` and `exclude` options select.

Add `--diff` to see the exact changes that would be made:

```shell
clmgr --dry-run --diff
```

`--diff` is independent of `--dry-run`. On a normal run it reports every change
that is applied, which is useful to see what a run did to a project:

```shell
clmgr --diff
```

### Output streams

The report and the summary are written to `stderr`, `--diff` writes to `stdout`.
Running clmgr in a terminal shows both, but it also means the diff can be saved
as a patch without having to filter the report out of it:

```shell
clmgr --dry-run --diff > copyright.patch
patch -p0 < copyright.patch
```

### Exit codes

| Code | Meaning                                                            |
| ---- | ------------------------------------------------------------------ |
| `0`  | Success; with `--check` no file needs to be changed                |
| `1`  | With `--check`, at least one file would be changed                 |
| `2`  | Error, for example a missing configuration file or input directory |

### Continuous integration

Use `--check` to fail a build when copyright headers are missing or out of date.
It never writes to the working tree, so it is safe to run on any checkout.

```yaml
- name: Check copyright headers
  run: clmgr --check --diff
```

## Configuration

### Configuration File

The Copyright License Manager (clmgr) uses a YAML configuration file to specify how copyright notices should be managed. By default, it looks for a file named `copyright.yml` in the current directory, but you can specify a different file using the `-c` or `--config` option.

Here's a detailed explanation of the configuration options:

#### Basic Structure

```yaml
source:
  - py
  - java
  - cs
  - ts
include:
  - "src/**/*"
exclude:
  - "**/*.min.js"
legal:
  - inception: 2014
    name: Enovation Group B.V.
    locality: Capelle aan den IJssel
    country: NL
format: "Copyright (c) {inception} - {year} [{name} - {locality} - {country}]"
license:
  enabled: true
  external: false
  content: All rights reserved.
```

#### Configuration Options

The `source` and `legal` options are required, every other option has a
default. clmgr reports what is wrong and exits with `2` when the configuration
cannot be used.

##### source

A list of file extensions to process. Supported values are 'py', 'java', 'cs',
'ts', 'sql', 'js', 'mjs', 'cjs', 'jsx', 'tsx', 'css', 'scss', 'sass', 'less',
'html', 'htm', 'vue' and 'svelte'.

JSON has no comments, so a copyright header cannot be added to it. Minified
files are usually generated and are best left out with an `exclude` pattern
such as `**/*.min.*`.

The comment style of the header depends on the file type:

| Extensions                             | Header                                            |
| -------------------------------------- | ------------------------------------------------- |
| `ts`, `js`, `mjs`, `cjs`, `jsx`, `tsx` | `/*! ... */` banner                               |
| `css`, `scss`, `less`                  | `/*! ... */` banner                               |
| `sass`                                 | `//` line comments                                |
| `html`, `htm`, `vue`, `svelte`         | `<!-- ... -->`, with `===` around the license     |

The `/*!` banner is kept by minifiers such as terser, esbuild, cssnano and the
compressed output of Sass, so the notice ends up in the shipped files as well.
The indented Sass syntax only supports line comments for a header, which are
not written to the compiled CSS.

```scss
/*! *****************************************************************************
SPDX-FileCopyrightText: Copyright (c) 2014 - 2026 [Enovation Group B.V. - Capelle aan den IJssel - NL]
---
All rights reserved.
---
****************************************************************************** */
```

Markup comments use `===` around the license, because XML based markup does
not allow `--` inside a comment. For the same reason clmgr reports a
configuration error when the copyright statements or the license content
contain `--` while a markup source is configured:

```html
<!--
  SPDX-FileCopyrightText: Copyright (c) 2014 - 2026 [Enovation Group B.V. - Capelle aan den IJssel - NL]
  ===
  All rights reserved.
  ===
-->
```

Lines that must stay at the top of a file are left in place and the header is
placed below them: a shebang (`#!`) in JavaScript and TypeScript, a `@charset`
rule in stylesheets, and an XML declaration or doctype in HTML. A byte order
mark always stays in front of the file.

An existing `/* */` header that holds a copyright statement is updated in
place, even when new headers of that file type use a different comment style.
Any other leading comment, such as an `eslint-disable` pragma, is left alone
and the header is added above it.

##### include

A list of glob patterns to include files for processing. When it is left empty
every file of a configured source extension is processed.

##### exclude

A list of glob patterns to exclude files from processing.

Patterns are matched against the path of a file relative to the input
directory. A `*` matches within one directory, `**` matches across
directories, and a pattern without a separator also matches a file name, a
file name without its extension, or a directory anywhere in the tree:

```yaml
include:
  - "src/**/*"      # every file under src, at any depth
exclude:
  - "**/*.min.js"   # minified files anywhere
  - build           # any directory named build
  - Generated       # any file named Generated.java, Generated.py, ...
```

##### legal

A list of legal entities associated with the copyright. Each entity must have the following properties:

- inception: The year when the copyright started
- name: The name of the copyright holder
- locality: The city or locality of the copyright holder
- country: The country code of the copyright holder

##### format

The format string for each row in the copyright notice. This property is optional and by default,
it is set to `SPDX-FileCopyrightText: Copyright (c) {inception} - {year} [{name} - {locality} - {country}]`.
Only the following placeholders can be used, any other placeholder is reported
as a configuration error:

- inception: The year when the copyright started
- year: The current year
- name: The name of the copyright holder
- locality: The city or locality of the copyright holder
- country: The country code of the copyright holder

##### license

Settings for the license notice. This section is optional, when it is left out
no license notice is managed:

- enabled: Whether to include a license notice (true/false), default false
- external: Whether to use an external license file (true/false)
- content: The content of the license notice (if not using an external file)

#### Advanced Configuration


##### Multiple Legal Entities

You can specify multiple legal entities in the `legal` section:

```yaml
legal:
  - inception: 2014
    name: Mars Hospital
    locality: Rotterdam
    country: NL
  - inception: 2016
    name: Lunar Base
    locality: Capelle aan den IJssel
    country: NL
  - inception: 2018
    name: Enovation Group B.V.
    locality: Capelle aan den IJssel
    country: NL
```

This is useful when the copyright has been transferred between different entities over time.

#####  Removing Copyright Notices

Copyright statements that are not defined in the legal block will be removed.

##### External License File

If you want to use an external file for the license notice:

```yaml
license:
  enabled: true
  external: true
```

### Examples

1. Basic configuration for a single company with license:

    ```yaml
    source:
      - py
      - java
    legal:
      - inception: 2015
        name: Enovation Group B.V.
        locality: Capelle aan den IJssel
        country: NL
    license:
      enabled: true
      content: All rights reserved.
    ```

2. Configuration with multiple legal entities, removals, and custom license:

    ```yaml
    source:
      - java
      - ts
      - cs
      - py
    legal:
      - inception: 2014
        name: Mars Hospital
        locality: Rotterdam
        country: NL
      - inception: 2017
        name: Lunar Base
        locality: Capelle aan den IJssel
        country: NL
      - inception: 2019
        name: Enovation Group B.V.
        locality: Capelle aan den IJssel
        country: NL
    license:
      enabled: true
      external: false
      content: All rights reserved.
    include:
    exclude:
    ```

## Docker

Build the docker container locally.

```shell
docker build -t clmgr:latest .
```

`--network=host` might be needed for the container build to resolve the DNS from the host machine.

The image contains a copy of the source taken at build time, so rebuild it after
changing clmgr.

Run the docker container in a project.

```shell
docker run --rm -v .:/work -it clmgr:latest
```

`-v .:/work` will mount the current directory to work dir in the docker container.

Leave out `-t` when redirecting the output. A pseudo terminal joins `stdout` and
`stderr` into a single stream.

## Contributing

We welcome contributions to the Copyright License Manager! 

For information on contributing to this project, please see our `Development Guide <DEVELOPMENT.rst>`_.
