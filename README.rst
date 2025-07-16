RPMGet
======

What is this?

|ci| |wheels| |bandit| |release|

|pre| |cov| |pylint|

|tag| |license| |reuse| |python|

More about what this is, quick start, etc.

Github workflows and setuptools_scm
-----------------------------------

This project uses setuptools_scm_ for dynamic versioning, therefor some
of the (github) workflows will look for a git tag to set the version in
CI. If there are no tags, this will result in some failed workflow runs.
There are several options to make them succeed:

* create a base tag, eg ``git tag -a 0.0.0``
* set SETUPTOOLS_SCM_PRETEND_VERSION to the above value in the workflow env
* disable failing workflows in the Github Actions tab
* delete any workflows you don't need


Github workflows and repo settings
----------------------------------

Some of the automation workflows may also fail without some non-default
repository settings; the following changes are required to allow these
workflows to run.

Go to the repository Settings tab and scroll to the bottom of the General
settings and enable these checkboxes under Pull Requests:

* Always suggest updating pull request branches (optional)
* Allow auto-merge (required)
* Automatically delete head branches (optional)

Next, in the left-hand menu under the Settings tab, click Actions, then General,
then scroll to Workflow permissions:

* make sure *Read repository contents and packages permissions* is selected
* enable the *Allow GitHub Actions to create and approve pull requests* checkbox,
  then click Save

In addition, the provided dependabot config expects some issue labels, so open the
project URL below (using your new project name) and add the following new labels:

**https://github.com/<your_name>/<project_name>/issues/labels**

* actions
* dependencies
* packaging


Github best practices
---------------------

Finally, best practices for public repositories should include the following
extra features:

* under Advanced Security enable Code Scanning, Dependabot, Private
  Vulnerability Reporting, and (default) Codeql config
* under Rules => Rulesets add some branch protection rules with required
  status checks


Dev tools
=========

Local tool dependencies to aid in development; install them for
maximum enjoyment.

Tox
---

As long as you have git and at least Python 3.8, then you can install
and use tox_.  After cloning the repository, you can run the repo
checks with the ``tox`` command.  It will build a virtual python
environment for each installed version of python with all the python
dependencies and run the specified commands, eg:

::

  $ git clone https://github.com/sarnold/doorstop-to-mermaid
  $ cd doorstop-to-mermaid/
  $ tox -e py

The above will run the default test command using the (local) default
Python version.  To specify the Python version and host OS type, run
something like::

  $ tox -e py311-linux

To build and check the Python package, run::

  $ tox -e build,check

Full list of additional ``tox`` commands:

* ``tox -e dev`` build a python venv and install in editable mode
* ``tox -e build`` build the python packages and run package checks
* ``tox -e check`` install the wheel package from above
* ``tox -e lint`` run ``pylint`` (somewhat less permissive than PEP8/flake8 checks)
* ``tox -e mypy`` run mypy import and type checking
* ``tox -e style`` run flake8 style checks
* ``tox -e reuse`` run the ``reuse lint`` command and install sbom4python
* ``tox -e changes`` generate a new changelog file

To build/lint the api docs, use the following tox commands:

* ``tox -e docs`` build the documentation using sphinx and the api-doc plugin
* ``tox -e ldocs`` run the Sphinx doc-link checking
* ``tox -e cdocs`` run ``make clean`` in the docs build


Gitchangelog
------------

We use gitchangelog_  to generate a changelog and/or release notes, as
well as the gitchangelog message format to help it categorize/filter
commits for tidier output.  Please use the appropriate ACTION modifiers
for important changes in Pull Requests.

Pre-commit
----------

This repo is also pre-commit_ enabled for various linting and format
checks.  The checks run automatically on commit and will fail the
commit (if not clean) with some checks performing simple file corrections.

If other checks fail on commit, the failure display should explain the error
types and line numbers. Note you must fix any fatal errors for the
commit to succeed; some errors should be fixed automatically (use
``git status`` and ``git diff`` to review any changes).

See the following sections in the built docs for more information on
gitchangelog and pre-commit.

You will need to install pre-commit before contributing any changes;
installing it using your system's package manager is recommended,
otherwise install with pip into your usual virtual environment using
something like::

  $ sudo emerge pre-commit  --or--
  $ pip install pre-commit

then install it into the repo you just cloned::

  $ git clone git@github.com:sarnold/doorstop-to-mermaid.git
  $ cd radar-test-gui/
  $ pre-commit install

It's usually a good idea to update the hooks to the latest version::

    pre-commit autoupdate


SBOM and license info
=====================

This project is now compliant with the REUSE Specification Version 3.3, so the
corresponding license information for all files can be found in the ``REUSE.toml``
configuration file with license text(s) in the ``LICENSES/`` folder.

Related metadata can be (re)generated with the following tools and command
examples.

* reuse-tool_ - REUSE_ compliance linting and sdist (source files) SBOM generation
* sbom4python_ - generate SBOM with full dependency chain

Commands
--------

Use tox to create the environment and run the lint command::

  $ tox -e reuse                      # --or--
  $ tox -e reuse -- spdx > sbom.txt   # generate sdist files sbom

Note you can pass any of the other reuse commands after the ``--`` above.

Use the above environment to generate the full SBOM in text format::

  $ source .tox/reuse/bin/activate
  $ sbom4python --system --use-pip -o <file_name>.txt

Be patient; the last command above may take several minutes. See the
doc links above for more detailed information on the tools and
specifications.

.. _Tox: https://github.com/tox-dev/tox
.. _reuse-tool: https://github.com/fsfe/reuse-tool
.. _REUSE: https://reuse.software/spec-3.3/
.. _sbom4python: https://github.com/anthonyharrison/sbom4python
.. _gitchangelog: https://github.com/sarnold/gitchangelog
.. _pre-commit: http://pre-commit.com/
.. _setuptools_scm: https://setuptools-scm.readthedocs.io/en/stable/


.. |ci| image:: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/ci.yml
    :alt: CI Status

.. |wheels| image:: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/wheels.yml/badge.svg
    :target: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/wheels.yml
    :alt: Wheel Status

.. |badge| image:: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/pylint.yml/badge.svg
    :target: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/pylint.yml
    :alt: Pylint Status

.. |release| image:: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/release.yml/badge.svg
    :target: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/release.yml
    :alt: Release Status

.. |bandit| image:: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/bandit.yml/badge.svg
    :target: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/bandit.yml
    :alt: Security check - Bandit

.. |cov| image:: https://raw.githubusercontent.com/sarnold/doorstop-to-mermaid/badges/main/test-coverage.svg
    :target: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/coverage.yml
    :alt: Test coverage

.. |pylint| image:: https://raw.githubusercontent.com/sarnold/doorstop-to-mermaid/badges/main/pylint-score.svg
    :target: https://github.com/sarnold/doorstop-to-mermaid/actions/workflows/pylint.yml
    :alt: Pylint Score

.. |license| image:: https://img.shields.io/badge/license-MIT-blue
    :target: https://github.com/sarnold/doorstop-to-mermaid/blob/main/LICENSE
    :alt: License

.. |tag| image:: https://img.shields.io/github/v/tag/sarnold/doorstop-to-mermaid?color=green&include_prereleases&label=latest%20release
    :target: https://github.com/sarnold/doorstop-to-mermaid/releases
    :alt: GitHub tag

.. |python| image:: https://img.shields.io/badge/python-3.9+-blue.svg
    :target: https://www.python.org/downloads/
    :alt: Python

.. |reuse| image:: https://api.reuse.software/badge/git.fsfe.org/reuse/api
    :target: https://api.reuse.software/info/git.fsfe.org/reuse/api
    :alt: REUSE status

.. |pre| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
