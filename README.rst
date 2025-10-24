RPMGet
======

RPMGet uses an ini-style config file to manage an arbitrary set of
development dependencies or releases as RPM packages. Either install
these packages in RHEL development environment or create a local
package repo.

|ci| |wheels| |bandit| |release|

|pre| |cov| |pylint|

|tag| |license| |reuse| |python|

Things you can do now:

* validate configuration files and URLs
* download configured rpm files to a single directory or rpm tree
* automatically skip downloading files that match size checks
* download one or more URL arguments to current directory (no config)
* dump a sample config file
* create an rpm repository from rpm tree layout

As stated above, the primary use cases (in the `user experience
sense`_) are intended to support managing/using a set of RPMs in
development workflows targeting older-but-still-supported Enterprise
Linux environments, eg, RHEL9 or similar.

The initial package metadata for RPMGet itself has been back-ported to
``setup.cfg`` which is compatible with el9 versions of packaging tools
when using the newer pyproject macros. For more details, see the `built
documentation`_, as well as the el9-rpm-toolbox_ repo for the latest
RPM package release.

.. important:: The ``--update`` argument requires an existing set of rpms
               downloaded in the "tree" layout, so you will need to run
               the initial download command with your config layout set
               to "tree" *before* using ``--update``.

.. _user experience sense: https://en.wikipedia.org/wiki/Use_case#Definition
.. _built documentation: https://sarnold.github.io/rpmget
.. _el9-rpm-toolbox: https://github.com/VCTLabs/el9-rpm-toolbox


Quick Start
~~~~~~~~~~~

* Install from GH release page, eg in a Tox file or venv
* Clone from GH and install in a venv
* Write a minimal config file (see below)

  + Using one of these file extensions: [.conf, .ini, .cfg]
  + Using at least one option with one or more URL strings

From a venv run ``rpmget -c <filename>`` with your config file to download
rpm files in the config. The initial download will create a manifest file
in the XDG user cache directory, ie ``~/.cache/rpmget/my_config.ini.json``.
Running the above command again without changing the config or deleting the
downloaded rpms should skip the downloading since the remote and local sizes
should all match.

::

  $ rpmget -c el9-toolbox-all.ini
  INFO:rpmget:Using input file el9-toolbox-all.ini
  INFO:root:Processing 13 valid url(s)
  INFO:root:Downloaded 0 file(s)
  INFO:root:Skipped 13 file(s)

To force downloading again, simply delete the ``top_dir`` directory and
run the rpmget command again.



Examples
--------

From a venv, run the following commands to validate your config and download
rpms::

  $ rpmget -c my_config.ini --validate
  INFO:rpmget:Using input file my_config.ini
  INFO:rpmget:User config is valid: True
  $ rpmget -c my_config.ini
  INFO:rpmget:Using input file my_config.ini
  INFO:root:Processing 3 valid url(s)
  INFO:rpmget.utils:python3-py3tftp-1.3.0-1.el9.noarch.rpm size: 35486
  100%|███████████████████████████████████████| 34.7k/34.7k [00:00<00:00, 422kB/s]
  ...

Or, download URL arguments to the current directory with no config file
required::

  $ rpmget https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/diskcache-5.6.3/python3-diskcache-5.6.3-1.el9.noarch.rpm
  INFO:root:Processing 1 valid url(s)
  INFO:rpmget.utils:Processing file: python3-diskcache-5.6.3-1.el9.noarch.rpm
  INFO:rpmget.utils:python3-diskcache-5.6.3-1.el9.noarch.rpm size: 76875
  100%|███████████████████████████████████████| 75.1k/75.1k [00:00<00:00, 508kB/s]
  INFO:root:Downloaded 1 file(s)

See the `Tox workflows`_ section below *and* the ``tox.ini`` file for more
details.

Install requirements
--------------------

Python and tox are required for development or testing workflows (the
following Python dependencies are installed automatically).

Python dependencies:

* httpx
* munch
* tqdm
* Cerberus
* platformdirs

Non-Python dependencies:

* at least one of ['rpm', 'yum', 'dnf'] is required to install rpms
* ``createrepo_c`` is required to create/maintain a common metadata
  repository from a tree of rpm packages


Command Interface
-----------------

The minimum usage requirement is an INI-style configuration file with URLs
pointing to RPM_ files. Use the ``--dump-config`` argument shown below for
a small example config. You *must* provide your own config file, either via
argument as shown below, or set in the RPMGET_CFG environment variable.

Most of the arguments are orthogonal to the ``--configfile`` argument; you
can even omit the latter argument if you set the environment variable.

Note each of the rpm URLs in the example point to GitHub release pages.
The CLI uses the standard Python ``argparse`` module::

  $ tox -e dev
  $ source .venv/bin/activate
  $ rpmget -h
  usage: rpmget [-h] [--version] [-S] [-t] [-u] [-v] [-d] [-q] [-D] [-c FILE]
                [URL ...]

  Download manager for rpm files

  positional arguments:
    URL                   download (valid) URLs to current directory with no
                          config (default: None)

  options:
    -h, --help            show this help message and exit
    --version             show program's version number and exit
    -S, --show            display user config (default: False)
    -t, --test            run sanity checks (default: False)
    -u, --update          update repos with createrepo (default: False)
    -v, --validate        run schema validation on active config (default:
                          False)
    -d, --debug           display more processing info (default: False)
    -q, --quiet           display less processing info (default: False)
    -D, --dump-config     dump active configuration to stdout (default: False)
    -c, --configfile FILE
                          path to ini-style configuration file (default: None)

The example config uses extended interpolation and ${VAR} style notation
but the simplest example config requires only an option value with a URL
string. Note the simple example below has the minimum required keys and
options; the ``repo_args`` key is the only one allowed to have an empty
value.

A simple example might look something like this::

  [rpmget]
  repo_dir = ~/repos/el9
  top_dir = rpmbuild
  layout = tree
  pkg_tool = dnf
  repo_tool = createrepo_c
  repo_args =

  [my stuff]
  packages =
      https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/hexdump-3.5.3/python3-hexdump-3.5.3-1.el9.noarch.rpm
      https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/diskcache-5.6.3/python3-diskcache-5.6.3-1.el9.noarch.rpm

To install the above downloaded rpms in a RockyLinux9 environment, run
something like the following::

  $ sudo dnf install -y rpmbuild/*.rpm

Note the above example could easily use a separate option-key for each URL
but the default configparser allows multiline strings, so we take advantage
of that.

.. _RPM: https://en.wikipedia.org/wiki/RPM_Package_Manager#Binary_format


Dev tools
~~~~~~~~~

Local tool dependencies to aid in development; install them for
maximum enjoyment.

Doorstop
--------

Document configurations and corresponding YAML or markdown items are
maintained in the following directory structure::

  $ tree reqs/ docs/swd/ tests/docs/
  reqs/
  ├── .doorstop.yml
  └── REQ001.yml
  docs/swd/
  ├── assets
  │   ├── .gitkeep
  │   └── rpmget_dependency_graph.svg
  ├── .doorstop.yml
  └── SDD001.md
  tests/docs/
  ├── .doorstop.yml
  └── TST001.yml

The doorstop_ tool has been added to project [dev] "extras" as well as the
tox dev and docs environments. If a doorstop package is not available for
your environment, then use the "dev" environment for working with doorstop_
documents, eg::

  tox -e dev
  source .venv/bin/activate
  (.venv) doorstop
  building tree...
  loading documents...
  validating items...

  REQ
  │
  ├── TST
  │
  └── SDD

Please see the `doorstop Quick Start`_ for an overview of the relevant
doorstop commands.

.. _doorstop Quick Start: https://doorstop.readthedocs.io/en/latest/getting-started/quickstart.html
.. _doorstop: https://doorstop.readthedocs.io/en/latest/index.html

Tox workflows
-------------

As long as you have git and at least Python 3.8, then you can install
and use tox_.  After cloning the repository, you can run the repo
checks with the ``tox`` command.  It will build a virtual python
environment for each installed version of python with all the python
dependencies and run the specified commands, eg:

::

  $ git clone https://github.com/sarnold/rpmget
  $ cd rpmget/
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

  $ git clone git@github.com:sarnold/rpmget.git
  $ cd rpmget/
  $ pre-commit install

It's usually a good idea to update the hooks to the latest version::

    pre-commit autoupdate


SBOM and license info
~~~~~~~~~~~~~~~~~~~~~

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

.. _tox: https://github.com/tox-dev/tox
.. _reuse-tool: https://github.com/fsfe/reuse-tool
.. _REUSE: https://reuse.software/spec-3.3/
.. _sbom4python: https://github.com/anthonyharrison/sbom4python
.. _gitchangelog: https://github.com/sarnold/gitchangelog
.. _pre-commit: http://pre-commit.com/
.. _setuptools_scm: https://setuptools-scm.readthedocs.io/en/stable/


.. |ci| image:: https://github.com/sarnold/rpmget/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/sarnold/rpmget/actions/workflows/ci.yml
    :alt: CI Status

.. |wheels| image:: https://github.com/sarnold/rpmget/actions/workflows/wheels.yml/badge.svg
    :target: https://github.com/sarnold/rpmget/actions/workflows/wheels.yml
    :alt: Wheel Status

.. |badge| image:: https://github.com/sarnold/rpmget/actions/workflows/pylint.yml/badge.svg
    :target: https://github.com/sarnold/rpmget/actions/workflows/pylint.yml
    :alt: Pylint Status

.. |release| image:: https://github.com/sarnold/rpmget/actions/workflows/release.yml/badge.svg
    :target: https://github.com/sarnold/rpmget/actions/workflows/release.yml
    :alt: Release Status

.. |bandit| image:: https://github.com/sarnold/rpmget/actions/workflows/bandit.yml/badge.svg
    :target: https://github.com/sarnold/rpmget/actions/workflows/bandit.yml
    :alt: Security check - Bandit

.. |cov| image:: https://raw.githubusercontent.com/sarnold/rpmget/badges/main/test-coverage.svg
    :target: https://github.com/sarnold/rpmget/actions/workflows/coverage.yml
    :alt: Test coverage

.. |pylint| image:: https://raw.githubusercontent.com/sarnold/rpmget/badges/main/pylint-score.svg
    :target: https://github.com/sarnold/rpmget/actions/workflows/pylint.yml
    :alt: Pylint Score

.. |license| image:: https://img.shields.io/badge/license-MIT-blue
    :target: https://github.com/sarnold/rpmget/blob/main/LICENSE
    :alt: License

.. |tag| image:: https://img.shields.io/github/v/tag/sarnold/rpmget?color=green&include_prereleases&label=latest%20release
    :target: https://github.com/sarnold/rpmget/releases
    :alt: GitHub tag

.. |python| image:: https://img.shields.io/badge/python-3.9+-blue.svg
    :target: https://www.python.org/downloads/
    :alt: Python

.. |reuse| image:: https://img.shields.io/badge/REUSE-compliant-blue.svg
    :target: https://reuse.software/spec-3.3/
    :alt: REUSE status

.. |pre| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
