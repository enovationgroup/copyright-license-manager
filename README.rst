Copyright License Manager
=========================

.. image:: https://img.shields.io/pypi/v/clmgr
    :target: https://pypi.org/project/clmgr/
    :alt: PyPI
.. image:: https://img.shields.io/pypi/pyversions/clmgr
    :target: https://pypi.org/project/clmgr/
    :alt: PyPI - Python Version
.. image:: https://img.shields.io/pypi/wheel/clmgr
    :target: https://pypi.org/project/clmgr/
    :alt: PyPI - Wheel
.. image:: https://img.shields.io/pypi/format/clmgr
    :target: https://pypi.org/project/clmgr/
    :alt: PyPI - Format
.. image:: https://img.shields.io/pypi/l/clmgr
    :target: https://pypi.org/project/clmgr/
    :alt: PyPI - License
.. image:: https://github.com/enovationgroup/copyright-license-manager/workflows/CI/badge.svg
    :target: https://github.com/enovationgroup/copyright-license-manager/actions/workflows/ci.yaml/badge.svg
    :alt: GitHub Actions - CI
.. image:: https://github.com/enovationgroup/copyright-license-manager/actions/workflows/pre-commit.yaml/badge.svg
    :target: https://github.com/enovationgroup/copyright-license-manager/actions/workflows/pre-commit.yaml/badge.svg
    :alt: GitHub Actions - pre-commit
.. image:: https://img.shields.io/codecov/c/gh/enovationgroup/copyright-license-manager
    :target: https://img.shields.io/codecov/c/gh/enovationgroup/copyright-license-manager
    :alt: Codecov

A cli tool for easy management of copyright and licenses in source code headers.

Installation
------------

.. code-block:: bash

    pip install clmgr

Features
--------

Current supported languages

* C#
* Java
* Python
* TypeScript

Usage
-----

Basic usage:

.. code-block:: bash

    clmgr -c path/to/config.yml -d path/to/source/directory

Options:

-c, --config FILE     Path to the configuration file (default: copyright.yml)
-d, --dir DIR         Input directory to process (default: current working directory)
-i, --file FILE       Process a single input file
--region REGION       Copyright search region (default: 10)
--debug               Enable verbose logging
--version             Show version information

Arguments
---------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Argument
     - Default
     - Description
   * - ``-c, --config FILE``
     - ``copyright.yml``
     - Path to the configuration file
   * - ``-i, --file FILE``
     - None
     - Path to a single input file to process
   * - ``-d, --dir DIR``
     - Current working directory
     - Input directory to process
   * - ``--region REGION``
     - 10
     - Copyright search region, this is the region of the file that will be searched for existing copyright statemens, the value is the amount of lines that will be searched from the starting of the files.
   * - ``--debug``
     - False
     - Enable verbose logging
   * - ``--version``
     - N/A
     - Show version information and exit

Configuration
-------------

Configuration File
------------------

The Copyright License Manager (clmgr) uses a YAML configuration file to specify how copyright notices should be managed. By default, it looks for a file named `copyright.yml` in the current directory, but you can specify a different file using the `-c` or `--config` option.

Here's a detailed explanation of the configuration options:

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: yaml

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

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

source
^^^^^^
A list of file extensions to process. Supported values include 'py', 'java', 'cs', 'ts'.

include
^^^^^^^
A list of glob patterns to include files for processing.

exclude
^^^^^^^
A list of glob patterns to exclude files from processing.

legal
^^^^^
A list of legal entities associated with the copyright. Each entity can have the following properties:

- inception: The year when the copyright started
- name: The name of the copyright holder
- locality: The city or locality of the copyright holder
- country: The country code of the copyright holder

format
^^^^^^
The format string for each row in the copyright notice. This property is optional and by default,
it is set to `SPDX-FileCopyrightText: Copyright (c) {inception} - {year} [{name} - {locality} - {country}]`.
The following placeholders can be used:

- {inception}: The year when the copyright started
- {year}: The current year
- {name}: The name of the copyright holder
- {locality}: The city or locality of the copyright holder
- {country}: The country code of the copyright holder

license
^^^^^^^
Settings for the license notice:

- enabled: Whether to include a license notice (true/false)
- external: Whether to use an external license file (true/false)
- content: The content of the license notice (if not using an external file)

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~~

Multiple Legal Entities
^^^^^^^^^^^^^^^^^^^^^^^

You can specify multiple legal entities in the `legal` section:

.. code-block:: yaml

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

This is useful when the copyright has been transferred between different entities over time.

Removing Copyright Notices
^^^^^^^^^^^^^^^^^^^^^^^^^^

Copyright statements that are not defined in the legal block will be removed.

External License File
^^^^^^^^^^^^^^^^^^^^^

If you want to use an external file for the license notice:

.. code-block:: yaml

    license:
      enabled: true
      external: true

Examples
~~~~~~~~

1. Basic configuration for a single company with license:

   .. code-block:: yaml

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

2. Configuration with multiple legal entities, removals, and custom license:

   .. code-block:: yaml

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

Docker
----------------

Build the docker container locally.

.. code-block:: bash

    docker build -t clmgr:latest .

`--network=host` might be needed for the container build to resolve the DNS from the host machine.

Run the docker container in a project.

.. code-block:: bash

    docker run -v .:/work -it clmgr:latest

`-v .:/work` will mount the current directory to work dir in the docker container.

Contributing
------------

We welcome contributions to the Copyright License Manager! 

For information on contributing to this project, please see our `Development Guide <DEVELOPMENT.rst>`_.
