Changelog
=========


0.2.1 (2025-09-07)
------------------

Changes
~~~~~~~
- Expose httpx session timeout in required config section. [Stephen L
  Arnold]

  * update docs, docstrings, test data, validation schema
- Add createrepo binary and arg strings to config, update reqs. [Stephen
  L Arnold]

  * also update default and example configs, update tests and docstrings
- Refactor download context, invert check, remove while loop. [Stephen L
  Arnold]


0.2.0 (2025-09-06)
------------------

New
~~~
- Add support for createrepo_c repo maintenance. [Stephen L Arnold]

  * update project docs, add related code and tests
  * add required default config item to define repo_dir
  * update bandit config, allow safe subprocess usage

Changes
~~~~~~~
- Add and update doorstop doc items, links, and references. [Stephen L
  Arnold]

Fixes
~~~~~
- Improve error handling, fix example config, add a test. [Stephen L
  Arnold]

  * check response status code and content length
  * remove empty/bogus files and return error string
  * add a test for invalid (remote) file name/path
  * not sure i like the while loop solution
- Refactor httpx client bits, check for content, use file context.
  [Stephen L Arnold]

  * this cleaned up github release downloads, but also revealed some
    rpm file errors using the example config
- Refactor manage_repo and update tests. [Stephen L Arnold]

  * cleanup some readme, docstring, and reuse bits
- Refactor copy_rpms to workaround missing glob args below py310.
  [Stephen L Arnold]

  * mark the createrepo_c tests as linux-only


0.1.0 (2025-08-24)
------------------

New
~~~
- Add processing loop function with a test, review SDD diagram chg.
  [Stephen L Arnold]

  * set minimum dep versions equal to el9 package versions
  * fix release workflow, flesh out readme
  * cleanup some config bits and doc strings
- Create directory layout based on config options. [Stephen L Arnold]

  * update validation schema to include allowed values
  * add tests for create_layout
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
- Update changelog for release, tweak config. [Stephen L Arnold]
- Add full example cfg for toolbox repo, cleanup reqs text. [Stephen L
  Arnold]

  * remove unused dependency from packaging and swd doc
  * (re)render dependency diagram and cleanup some doc strings
- Add more cfg/url handling and tests, update doorstop docs. [Stephen L
  Arnold]
- Refactor validation bits and tests. [Stephen L Arnold]

  * factor out url validation into its own function
  * update tests and test data
- Add more doorstop doc items, document layout reqs. [Stephen L Arnold]
- Add macros file creation in rpm tree mode. [Stephen L Arnold]

  * mark create_macros test as linux only
- Add/update more doorstop doc items and readme. [Stephen L Arnold]
- Expand reqs and swd docs, update sources for traceability. [Stephen L
  Arnold]
- Refactor argparse bits for testability, update docs. [Stephen L
  Arnold]
- Flesh out basic design items, link core bits to parent. [Stephen L
  Arnold]
- Required section name is now rpmget, update src and tests. [Stephen L
  Arnold]

  * we only validate [rpmget] section and any found URL values
  * whether to use DEFAULT section is now a user choice
- Close initial diagram PR and recycle for diagram updates. [Stephen L
  Arnold]

  * (re)review doorstop doc updates
- Add more doorstop bits, flesh out doc tree. [Stephen L Arnold]

  * add the doc and diagram processing scripts and target assets dirs
  * update doc sources and tox, correct some typos, generate changelog
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
- [create-pull-request] automated change. [github-actions[bot]]
- [create-pull-request] automated change. [github-actions[bot]]


0.0.0 (2025-07-16)
------------------

Changes
~~~~~~~
- Initial un-template commit, add config for pep8speaks. [Stephen L
  Arnold]

Other
~~~~~
- Initial commit. [Steve Arnold]
