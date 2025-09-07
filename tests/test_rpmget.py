import logging
import os
import sys
import warnings
from argparse import ArgumentParser
from shlex import split

import pytest

import rpmget
from rpmget import (
    CFG,
    CfgParser,
    CfgSectionError,
    __version__,
    find_rpm_urls,
    url_is_valid,
)
from rpmget.rpmget import (
    main_arg_parser,
    parse_command_line,
    process_config_loop,
    self_test,
    show_paths,
)
from rpmget.utils import get_filelist, manage_repo

RPMFILES = """
[rpmget]
repo_dir = rpmrepo/el9
top_dir = rpms
layout = tree
pkg_tool = yum
repo_tool = createrepo_c
repo_args = --compatibility
httpx_timeout = 15.0

[stuff]
files =
    https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/py3tftp-1.3.0/python3-py3tftp-1.3.0-1.el9.noarch.rpm
    https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/procman-0.6.1/python3-procman-0.6.1-1.el9.noarch.rpm
    https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/pygtail-0.14.0.3/python-pygtail-0.14.0.3-1.el9.src.rpm
"""

NOTCFG = """
[rpmget]
repo_dir = ~/repos//el9
top_dir = rpms
layout = tree
rpm_tool = dnf
httpx_timeout = 15.0
"""

BADURL = """
[rpmget]
repo_dir = rpmrepo/el9
top_dir = rpms
layout = tree
pkg_tool = rpm
repo_tool = createrepo_c
repo_args = --compatibility
httpx_timeout = 15.0

[stuff]
file = https://some[place.it/rpms/fake.rpm
"""


@pytest.mark.dependency()
@pytest.mark.network()
@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_process_config_loop(tmpdir_session):
    """
    Tests implementation of main processing loop.
    """
    parser = CfgParser()
    cfg_str = RPMFILES
    parser.read_string(cfg_str)
    d = tmpdir_session / "sub"
    res = process_config_loop(config=parser, temp_path=d)
    print(res)
    assert len(res) == 3


@pytest.mark.dependency(depends=["test_process_config_loop"])
@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_manage_repo(tmpdir_session, caplog):
    """
    Verifies REQ009
    """
    parser = CfgParser()
    cfg_str = RPMFILES
    parser.read_string(cfg_str)
    d = tmpdir_session / "sub"
    caplog.clear()
    caplog.set_level(logging.DEBUG)
    manage_repo(parser, debug=True, temp_path=d)
    assert "cmdline: createrepo_c --compatibility --verbose" in caplog.text
    dirlist = os.listdir(d / 'rpmrepo/el9/RPMS')
    print(f'\ncreaterepo generated repodata: {dirlist}')
    assert 'repodata' in dirlist
    caplog.clear()
    manage_repo(config=parser, debug=True, temp_path=d)
    assert "cmdline: createrepo_c --compatibility --update" in caplog.text
    # print(caplog.text)
    rpms = [f for f in get_filelist(d) if 'rpmrepo' in f]
    print(f"rpm files: {rpms}")


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_manage_repo_no_bin(tmp_path, monkeypatch):
    parser = CfgParser()
    cfg_str = RPMFILES
    parser.read_string(cfg_str)
    d = tmp_path / "other"
    monkeypatch.setenv("PATH", "/usr/local/bin")
    manage_repo(config=parser, temp_path=d)
    rpms = [f for f in get_filelist(d)]
    print(rpms)
    assert rpms == []


def test_url_is_valid():
    parser = CfgParser()
    cfg_str = RPMFILES
    parser.read_string(cfg_str)
    assert parser["rpmget"]["repo_dir"] is not None
    rpms_str = parser["stuff"]["files"]
    print(rpms_str)
    urls = [x for x in rpms_str.splitlines() if x != '']
    for url in urls:
        assert url_is_valid(url)


def test_url_is_valid_no(caplog):
    parser = CfgParser()
    cfg_str = BADURL
    parser.read_string(cfg_str)
    rpms_str = parser["stuff"]["file"]
    print(rpms_str)
    urls = [x for x in rpms_str.splitlines() if x != '']
    assert not url_is_valid(urls[0])
    print(caplog.records)
    assert 'Must be a valid URL ending in .rpm' in str(caplog.records[0])


def test_parse_command_line(capsys):
    cmd_str = 'rpmget --version'
    argv = split(cmd_str)
    with pytest.raises(SystemExit):
        arguments = parse_command_line(argv)
        print(arguments)
        assert __version__ in arguments


def test_main_arg_parser(capsys):
    parser = main_arg_parser()
    print(parser)
    assert isinstance(parser, ArgumentParser)
    assert "Download manager for rpm files" in parser.description


def test_self_test(capfd, tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.ini"
    p.write_text(CFG, encoding="utf-8")
    self_test(p)
    out, err = capfd.readouterr()
    print(f'out: {out}')
    assert p.name in out


def test_self_test_not_valid(caplog, tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.ini"
    p.write_text(NOTCFG, encoding="utf-8")
    self_test(p)
    print(caplog.text)
    assert "ERROR" in caplog.text
    assert "False" in caplog.text


def test_self_test_none(capfd):
    with warnings.catch_warnings(record=True) as w:
        self_test(None)
        out, err = capfd.readouterr()
        assert 'rpmget' in out
        assert len(w) == 1
        assert issubclass(w[-1].category, RuntimeWarning)
        assert "Cannot verify" in str(w[-1].message)


def test_show_paths(capfd):
    show_paths(None)
    out, err = capfd.readouterr()
    print(f'out: {out}')
    assert "rpmget" in out


def test_find_rpm_urls():
    parser = CfgParser()
    cfg_str = CFG
    parser.read_string(cfg_str)
    res = find_rpm_urls(parser)
    print(res)
    assert len(res) == 4
    for url in res:
        assert url_is_valid(url)
