Development
===========

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
