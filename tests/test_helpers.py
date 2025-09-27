import logging
import os
import sys
from pathlib import Path

import pytest

from rpmget import (
    CFG,
    RPM_TREE,
    CfgParser,
    FileTypeError,
    __version__,
    create_layout,
    create_macros,
    load_config,
)
from rpmget.utils import (
    check_for_rpm,
    compare_file_data,
    download_progress_bin,
    get_file_data,
    get_filelist,
    get_user_cachedir,
)

GH_URL = 'https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/py3tftp-1.3.0/python3-py3tftp-1.3.0-1.el9.noarch.rpm'
NAME = 'python3-py3tftp-1.3.0-1.el9.noarch.rpm'
BAD_URL = 'https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/foobar-1.3.0/python3-foobar-1.3.0-1.el9.noarch.rpm'
# fmt: off
GOOD_MFT = {'digest': 'e5f379164680427663679cf550b19e07146f63258ba8aacc18789a6ed8675f9a', 'mtime': '09-14-2025 15:05:32', 'name': 'python3-daemonizer-1.1.3-1.el9.noarch.rpm', 'size': 32376}
BAD_MFT = {'digest': 'a6f379164680427663679cf550b19e07146f63258ba8aacc18789a6ed8675f9a', 'mtime': '09-14-2025 15:05:32', 'name': 'python3-daemonizer-1.1.3-1.el9.noarch.rpm', 'size': 32376}
# fmt: on


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_create_macros():
    """
    Test macro string contents as part of REQ007 validation.
    """
    res = create_macros("rpmbuild")
    print(res)
    assert "%packager" in res


def test_compare_file_data():
    """
    Compare metadata dictionaries.
    """
    diff_good = compare_file_data(GOOD_MFT, GOOD_MFT)
    print(f'\nNO difference: {diff_good}')
    assert not diff_good
    assert isinstance(diff_good, dict)
    diff_bad = compare_file_data(GOOD_MFT, BAD_MFT)
    print(f'YES difference: {diff_bad}')
    assert diff_bad
    assert 'digest' in diff_bad


def test_get_user_cachedir():
    res = get_user_cachedir()
    print(res)
    assert isinstance(res, str)
    assert "rpmget" in res


def test_get_file_data(tmp_path):
    """
    Tests rpm file metadata; verifies file metadata portion of REQ012.
    """
    d = tmp_path / "digest"
    d.mkdir()
    p = d / "test.ini"
    p.write_text(CFG, encoding="utf-8")

    _, pfile = load_config(str(p))

    _, res = get_file_data(pfile)
    print(res)
    assert isinstance(res, dict)
    keys = ['digest', 'mtime', 'name', 'size']
    for key in keys:
        assert key in res


def test_cfg_parser():
    parser = CfgParser()
    assert hasattr(parser, '_empty_lines_in_values')
    assert parser._empty_lines_in_values == False


def test_def_config():
    parser = CfgParser()
    parser.read_string(CFG)
    print(list(parser.items()))
    rpms_str = parser["Toolbox"]["tb_rpms"]
    assert isinstance(rpms_str, str)
    print(rpms_str)
    rpms = [x for x in rpms_str.splitlines() if x != '']
    print(f'size: {len(rpms)}')
    print(f'type: {type(rpms)}')
    print(rpms)


def test_load_config_default():
    popts, pfile = load_config()

    assert pfile is None or isinstance(pfile, Path)
    print(repr(popts))
    assert isinstance(popts, CfgParser)


def test_load_config_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.ini"
    p.write_text(CFG, encoding="utf-8")

    popts, pfile = load_config(str(p))

    assert isinstance(pfile, Path)
    assert isinstance(popts, CfgParser)


def test_load_config_bogus(monkeypatch):
    monkeypatch.setenv("RPMGET_CFG", "testme.txt")
    with pytest.raises(FileTypeError) as excinfo:
        _, pfile = load_config()
    assert 'Invalid file extension' in str(excinfo.value)
    assert 'testme.txt' in str(excinfo.value)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_check_for_rpm():
    rpm_path = check_for_rpm()
    print(rpm_path)
    assert 'rpm' in rpm_path
    assert 'bin' in rpm_path
    assert isinstance(rpm_path, str)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_check_for_rpm_bogus(monkeypatch, capfd):
    monkeypatch.setenv("PATH", "/usr/local/bin")
    with pytest.raises(FileNotFoundError) as excinfo:
        _ = check_for_rpm()
    print(str(excinfo.value))
    assert "program not found in PATH" in str(excinfo.value)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only")
def test_check_for_rpm_other(capfd):
    cr_path = check_for_rpm('createrepo_c')
    print(cr_path)
    assert 'createrepo_c' in cr_path


@pytest.mark.dependency()
@pytest.mark.network()
def test_download_progress_bin(tmpdir_session):
    dst_dir = tmpdir_session / 'rpms'
    test_file_name = download_progress_bin(GH_URL, dst_dir, 'flat', 10.0, {})
    assert test_file_name.endswith(NAME)


@pytest.mark.dependency(depends=["test_download_progress_bin"])
def test_get_filelist_down(caplog, tmpdir_session):
    dst_dir = tmpdir_session / 'rpms'
    with caplog.at_level(logging.INFO):
        files = get_filelist(dst_dir)
    print(files)
    print(caplog.text)
    assert len(files) == 1
    assert Path(files[0]).is_absolute()
    assert files[0].endswith(NAME)


@pytest.mark.dependency()
@pytest.mark.network()
def test_download_progress_tree(tmpdir_session):
    dst_dir = tmpdir_session / 'rpmbuild'
    create_layout(str(dst_dir), 'tree')
    test_file_name = download_progress_bin(GH_URL, dst_dir, 'tree', 15.0, {})
    assert test_file_name.endswith(NAME)


@pytest.mark.dependency(depends=["test_download_progress_tree"])
def test_get_filelist_tree(tmpdir_session):
    dst_dir = tmpdir_session / 'rpmbuild'
    files = get_filelist(dst_dir)
    print(files)
    assert len(files) == 1
    assert files[0].endswith(NAME)


@pytest.mark.network()
def test_download_progress_bogus(tmp_path):
    dst_dir = tmp_path / 'rpmbuild'
    create_layout(str(dst_dir), 'tree')
    test_file_name = download_progress_bin(BAD_URL, dst_dir, 'tree', 5.0, {})
    assert test_file_name == "ResourceError"


def test_create_layout_flat(tmp_path):
    """
    Test layout = tree as part of REQ006 validation.
    """
    d = tmp_path / 'rpmbuild'
    create_layout(str(d), 'flat')
    print(d)
    for root, dirs, files in os.walk(str(d)):
        print(root)
        assert dirs == []
        assert files == []


def test_create_layout_tree(tmp_path):
    """
    Test layout = tree as part of REQ006, REQ007, and REQ008 validation.
    """
    d = tmp_path / 'rpmbuild'
    create_layout(str(d), 'tree')
    print(d)
    files = sorted(os.listdir(str(d)))
    print(files)
    assert files == [
        '.rpmmacros',
        'BUILD',
        'BUILDROOT',
        'RPMS',
        'SOURCES',
        'SPECS',
        'SRPMS',
    ]


def test_get_filelist(tmpdir_session):
    dst_dir = tmpdir_session / 'rpmbuild/RPMS/noarch'
    dst_dir.mkdir(parents=True, exist_ok=True)
    p = dst_dir / "test1.noarch.rpm"
    p.write_bytes(os.urandom(1024))
    files = get_filelist(dst_dir)
    print(files)
    for file in files:
        assert Path(file).suffix == '.rpm'
        assert Path(file).is_absolute()
    rfiles = get_filelist(dst_dir, False)
    print(rfiles)
