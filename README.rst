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

Testing
-------

This project uses ``pytest`` to run tests, if docstring examples are provided or
included these will be included automatically.

Install test dependencies.

.. code-block:: bash

    pip install -r requirements_dev.txt

Run tests.

.. code-block:: bash

    pytest

Development
-----------

This project uses ``black`` to format code and ``flake8`` for linting. To ensure
these actions are run ``pre-commit`` is used. A git alias is provided which
will configure the entire environment.

Configure environment.

.. code-block:: bash

    git config include.path ../.gitaliases
    git setup

Install dev dependencies.

.. code-block:: bash

    pip install -r requirements_dev.txt

Install for development

.. code-block:: bash

    pip install -e .

Format Code

.. code-block:: bash

    python -m black clmgr/**

Release (Manual)
----------------

The following action describe the manual release process.

Install dev dependencies.

.. code-block:: bash

    pip install -r requirements_dev.txt

Clean.

.. code-block:: bash

    git clean -xfd

Build.

.. code-block:: bash

    python setup.py sdist bdist_wheel

Verify.

.. code-block:: bash

    twine check dist/*

Upload.

.. code-block:: bash

    twine upload dist/*

Release
-------

Releases are published automatically when a tag is pushed to GitHub.

.. code-block:: bash

    # Set next version number
    export RELEASE=x.x.x

    # Create tags
    git commit --allow-empty -m "build: release ${RELEASE}"
    git tag -a ${RELEASE} -m "build: release ${RELEASE}"

    # Push - Assume that we are working from a fork
    git push upstream --tags
