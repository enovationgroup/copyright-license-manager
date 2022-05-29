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
    :target: https://github.com/enovationgroup/copyright-license-manager/actions?query=workflow%3ACI
    :alt: GitHub Actions - CI

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

Install dev dependencies.

.. code-block:: bash

    pip install -r requirements_dev.txt

Install for development

.. code-block:: bash

    pip install -e .

Publish
-------

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
