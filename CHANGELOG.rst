Changelog
=========


0.0.1.dev15+g99b8538.d20250802
------------------------------

New
~~~
- Add config file validation in self-test and commandline arg. [Stephen
  L Arnold]

  * add baseline config validation using DEFAULT schema and url check
  * add cerberus dep for validate function, add mypy config
  * add validation tests for new function, add commandline arg, add
    config validation to self-test with logging output
- Add main entrypoint with initial args, move cfg handling. [Stephen L
  Arnold]
- Add cfg file handling and tests, update def_config and tox envs.
  [Stephen L Arnold]
- Add ConfigParser subclass and default ini cfg string with tests.
  [Stephen L Arnold]

  * CfgParser() sets REQ002 defaults but still accepts the normal options
- Add url fetching and file finding with tests, update readme. [Stephen
  L Arnold]

Changes
~~~~~~~
- Cleanup some docstrings and log messages, update project files.
  [Stephen L Arnold]
- Cleanup entrypoint and type hints, add tests. [Stephen L Arnold]
- Revert ci platform matrix and mark tests. [Stephen L Arnold]

  * skip rpm checks on non-linux platforms, allow other tests
- Add pytest mark for network test, add check for rpm cmd. [Stephen L
  Arnold]

  * add rpm dep install in github workflows, remove non-linux platforms
- Update tox deps and pre-commit hooks, cleanup some lint. [Stephen L
  Arnold]
- Add doorstop parent document, update readme and workflow. [Stephen L
  Arnold]

Other
~~~~~
- Merge pull request #6 from sarnold/entrypoint. [Steve Arnold]

  configs and entrypoint
- Merge pull request #5 from sarnold/new-project-bits. [Steve Arnold]

  New project bits
- Merge pull request #3 from sarnold/new-project-bits. [Steve Arnold]

  workflows


0.0.0 (2025-07-16)
------------------

Changes
~~~~~~~
- Initial un-template commit, add config for pep8speaks. [Stephen L
  Arnold]

Other
~~~~~
- Merge pull request #1 from VCTLabs/untemplate-bits. [Steve Arnold]

  initial project bits
- Initial commit. [Steve Arnold]
