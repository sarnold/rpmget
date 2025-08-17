import logging
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
    url_is_valid,
)
from rpmget.rpmget import (
    main_arg_parser,
    parse_command_line,
    self_test,
    show_paths,
)

RPMFILES = """
[rpmget]
top_dir = rpms
layout = flat
pkg_tool = yum
#rpm_tool = rpm

[stuff]
files =
    https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/py3tftp-1.3.0/python3-py3tftp-1.3.0-1.el9.noarch.rpm
    https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/procman-0.6.1/python3-procman-0.6.1-1.el9.noarch.rpm
"""

NOTCFG = """
[rpmget]
top_dir = rpms
layout = tree
rpm_tool = dnf
"""

BADURL = """
[rpmget]
top_dir = rpms
layout = tree
pkg_tool = rpm

[stuff]
file = https://some[place.it/rpms/fake.rpm
"""


def test_url_is_valid():
    parser = CfgParser()
    cfg_str = RPMFILES
    parser.read_string(cfg_str)
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
