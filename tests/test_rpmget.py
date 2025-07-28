import logging
import warnings

import pytest

import rpmget
from rpmget import CFG
from rpmget.rpmget import self_test, show_paths

NOTCFG = """
[DEFAULT]
top_dir = rpms
layout = true
rpm_tool = dnf
"""


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
