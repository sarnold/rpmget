import json
import logging
import os
import sys
import warnings
from argparse import ArgumentParser
from pathlib import Path
from shlex import split

import pytest
from munch import Munch

import rpmget
from rpmget import (
    CFG,
    CfgParser,
    CfgSectionError,
    InvalidURLError,
    __version__,
    find_rpm_urls,
    url_is_valid,
)
from rpmget.rpmget import (
    collect_valid_urls,
    main_arg_parser,
    parse_command_line,
    process_config_loop,
    process_urls,
    self_test,
    show_paths,
)
from rpmget.utils import (
    compare_manifest_data,
    get_filelist,
    load_manifest,
    manage_repo,
    process_file_manifest,
    read_manifest,
)

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

MAN_DATA = """
{
  "config": "test_file_manifest.ini",
  "files": {
    "python-pygtail-0.14.0.3-1.el9.src.rpm": {
      "digest": "26dfd0e4fa5730a2ada17e6ce63079119b10e1cae9e41ca3274779043f2e7a6c",
      "mtime": "09-20-2025 17:21:10",
      "name": "python-pygtail-0.14.0.3-1.el9.src.rpm",
      "size": 36460
    },
    "python3-procman-0.6.1-1.el9.noarch.rpm": {
      "digest": "0c3e73f7f6b88effe9e2931309b9859f31758a6a7d54479c29031059dc4fa6ac",
      "mtime": "09-20-2025 17:21:10",
      "name": "python3-procman-0.6.1-1.el9.noarch.rpm",
      "size": 37682
    },
    "python3-py3tftp-1.3.0-1.el9.noarch.rpm": {
      "digest": "dd6dc41b99a326970e53f216e6f76cb4aba5d6f0321bab63192da0a4a463e69c",
      "mtime": "09-20-2025 17:21:10",
      "name": "python3-py3tftp-1.3.0-1.el9.noarch.rpm",
      "size": 35486
    }
  }
}
"""

MAN_DICT = {
    'config': 'test_file_manifest.ini',
    'files': {
        'python-pygtail-0.14.0.3-1.el9.src.rpm': {
            'digest': '26dfd0e4fa5730a2ada17e6ce63079119b10e1cae9e41ca3274779043f2e7a6c',
            'mtime': '09-20-2025 17:21:10',
            'name': 'python-pygtail-0.14.0.3-1.el9.src.rpm',
            'size': 36460,
        },
        'python3-procman-0.6.1-1.el9.noarch.rpm': {
            'digest': '0c3e73f7f6b88effe9e2931309b9859f31758a6a7d54479c29031059dc4fa6ac',
            'mtime': '09-20-2025 17:21:10',
            'name': 'python3-procman-0.6.1-1.el9.noarch.rpm',
            'size': 37682,
        },
        'python3-py3tftp-1.3.0-1.el9.noarch.rpm': {
            'digest': 'dd6dc41b99a326970e53f216e6f76cb4aba5d6f0321bab63192da0a4a463e69c',
            'mtime': '09-20-2025 17:21:10',
            'name': 'python3-py3tftp-1.3.0-1.el9.noarch.rpm',
            'size': 35486,
        },
    },
}

NEW_DICT = {
    'config': 'test_file_manifest.ini',
    'files': {
        'python-pygtail-0.14.0.3-1.el9.src.rpm': {
            'digest': '26dfd0e4fa5730a2ada17e6ce63079119b10e1cae9e41ca3274779043f2e7a6c',
            'mtime': '09-20-2025 17:21:10',
            'name': 'python-pygtail-0.14.0.3-1.el9.src.rpm',
            'size': 36460,
        },
        'python3-procman-0.6.1-1.el9.noarch.rpm': {
            'digest': '0c3e73f7f6b88effe9e2931309b9859f31758a6a7d54479c29031059dc4fa6ac',
            'mtime': '09-20-2025 17:21:10',
            'name': 'python3-procman-0.6.1-1.el9.noarch.rpm',
            'size': 37682,
        },
        'python3-py3tftp-1.3.0-1.el9.noarch.rpm': {
            'digest': 'aa6dc41b99a326970e53f216e6f76cb4aba5d6f0321bab63192da0a4a463e69c',
            'mtime': '09-20-2025 17:21:10',
            'name': 'python3-py3tftp-1.3.0-1.el9.noarch.rpm',
            'size': 35486,
        },
    },
}

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

BOGUS_TGT = 'https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/foobar-1.3.0/python3-foobar-1.3.0-1.el9.noarch.rpm'
BOGUS_URL = 'https://some[place.com/rpms/fake.rpm'


@pytest.fixture()
def change_test_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)


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
    res = process_config_loop(config=parser, mdata={}, temp_path=d)
    print(res)
    assert len(res) == 3
    for file in res:
        assert Path(file).is_absolute()
    res2 = process_config_loop(config=parser, mdata=MAN_DICT, temp_path=d)
    print(res2)


def test_process_config_loop_invalid(tmpdir_session):
    """
    Tests implementation of main processing loop.
    """
    parser = CfgParser()
    cfg_str = NOTCFG
    parser.read_string(cfg_str)
    d = tmpdir_session / "sub"
    res = process_config_loop(config=parser, mdata={}, temp_path=d)
    print(res)
    assert res == []


@pytest.mark.network()
@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_process_file_manifest(tmpdir_session, caplog):
    """
    Test manifest processing.
    """
    parser = CfgParser()
    cfg_str = RPMFILES
    parser.read_string(cfg_str)
    d = tmpdir_session / "sub"
    files = process_config_loop(config=parser, mdata={}, temp_path=d)
    print(f'manifest files {files}')
    cfg_name = "test_file_manifest.ini"
    # p.write_text(RPMFILES, encoding="utf-8")
    c = tmpdir_session / "cache" / "rpmget"
    process_file_manifest(files, cfg_name, str(c))
    res = get_filelist(tmpdir_session, fileglob='*.json')
    assert 'rpmget' in res[0]
    print(f'\nGenerated manifest: {res[0]}')
    process_file_manifest(files, cfg_name, str(c))
    with Path(res[0]).open("r") as f:
        data = json.load(f)
    # print(data)
    attr_data = Munch.fromDict(data)
    print(attr_data.files.toDict())


def test_read_manifest(tmpdir_session, caplog):
    """
    Test reading manifest from file.
    """
    c = tmpdir_session / "cache" / "rpmget"
    c.mkdir(parents=True, exist_ok=True)
    mfile = c / 'test_file_manifest.ini.json'
    mfile.write_text(MAN_DATA)
    print(mfile)
    assert 'rpmget' in str(mfile)
    assert isinstance(mfile, Path)
    data = read_manifest(mfile, str(c))
    assert isinstance(data, dict)
    print(data)


def test_load_manifest(tmpdir_session, caplog):
    """
    Test reading manifest from file.
    """
    c = tmpdir_session / "cache" / "rpmget"
    c.mkdir(parents=True, exist_ok=True)
    cname = 'test_file_manifest.ini'
    data = load_manifest(cname, str(c))
    assert isinstance(data, dict)
    assert data["config"] == cname
    print(data)


def test_compare_manifest_data(tmpdir_session, caplog):
    """
    Test reading manifest from file.
    """
    c = tmpdir_session / "cache" / "rpmget"
    mfile = c / 'test_file_manifest.ini.json'
    print(mfile)
    data = read_manifest(mfile, str(c))
    assert isinstance(data, dict)
    # print(data)
    res = compare_manifest_data(data, NEW_DICT)
    assert res[0] == {
        'digest': 'aa6dc41b99a326970e53f216e6f76cb4aba5d6f0321bab63192da0a4a463e69c'
    }
    print(res)
    NEW_DICT["config"] = 'test_file_manifest.cfg'
    res2 = compare_manifest_data(data, NEW_DICT)
    assert res2[0] == 'test_file_manifest.cfg'
    print(res2)


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
    print(caplog.text)
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


@pytest.mark.network()
def test_process_urls(caplog, change_test_dir):
    """
    Tests implementation of url processing loop; satisfies REQ010.
    """
    parser = CfgParser()
    cfg_str = RPMFILES
    parser.read_string(cfg_str)
    urls = [s for s in parser['stuff']['files'].splitlines() if s]
    urls.append(BOGUS_URL)
    urls.append(BOGUS_TGT)
    print(urls)
    assert isinstance(urls, list)
    assert len(urls) == 5

    caplog.clear()
    with caplog.at_level(logging.INFO):
        res = process_urls(urls)
    print(res)
    print(caplog.text)
    assert isinstance(res, list)
    assert len(res) == 4


def test_process_urls_invalid(caplog):
    """
    Tests implementation of url processing loop.
    """
    parser = CfgParser()
    cfg_str = BADURL
    parser.read_string(cfg_str)
    urls = [s for s in parser['stuff']['file'].splitlines() if s]
    print(urls)
    with pytest.raises(InvalidURLError) as excinfo:
        res = process_urls(urls)
    print(excinfo)


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
