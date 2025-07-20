import os
from pathlib import Path

import pytest

from rpmget import version
from rpmget.utils import (
    check_for_rpm,
    download_progress_bin,
    get_filelist,
)

GH_URL = 'https://github.com/VCTLabs/el9-rpm-toolbox/releases/download/py3tftp-1.3.0/python3-py3tftp-1.3.0-1.el9.noarch.rpm'
NAME = 'python3-py3tftp-1.3.0-1.el9.noarch.rpm'


def test_check_for_rpm():
    rpm_path = check_for_rpm()
    print(rpm_path)
    assert 'rpm' in rpm_path
    assert 'bin' in rpm_path
    assert isinstance(rpm_path, str)


def test_check_for_rpm_bogus(monkeypatch, capfd):
    monkeypatch.setenv("PATH", "/usr/local/bin")
    with pytest.raises(FileNotFoundError) as excinfo:
        _ = check_for_rpm()
    print(str(excinfo.value))
    assert "rpm not found in PATH" in str(excinfo.value)


@pytest.mark.dependency()
@pytest.mark.network()
def test_download_progress_bin(tmpdir_session):
    dst_dir = tmpdir_session / 'rpms'
    test_file_name = download_progress_bin(GH_URL, dst_dir)
    assert test_file_name == NAME


@pytest.mark.dependency(depends=["test_download_progress_bin"])
def test_get_filelist_down(tmpdir_session):
    dst_dir = tmpdir_session / 'rpms'
    files = get_filelist(dst_dir)
    print(files)
    assert len(files) == 1
    assert files[0].endswith(NAME)


def test_get_filelist(tmp_path):
    dst_dir = tmp_path / 'rpms'
    dst_dir.mkdir()
    p = dst_dir / "test1.rpm"
    p.write_bytes(os.urandom(1024))
    files = get_filelist(dst_dir)
    print(files)
    for file in files:
        assert Path(file).suffix == '.rpm'
