import logging
import warnings

import pytest
from cerberus import Validator

from rpmget import (
    SCHEMA,
    CfgParser,
    CfgSectionError,
    load_config,
    validate_config,
)

DEFCFG = """
[rpmget]
top_dir = rpms
layout = flat
pkg_tool = rpm
"""

NOTCFG = """
[rpmget]
top_dir = rpms
layout = true
rpm_tool = dnf
"""

NOURL = """
[rpmget]
top_dir = rpms
layout = tree
pkg_tool = rpm

[stuff]
file = this/is/not/a/url.txt
"""

BADURL = """
[rpmget]
top_dir = rpms
layout = tree
pkg_tool = rpm

[stuff]
file = https:/someplace.it/rpms/fake.rpm
"""

BADLAYOUT = """
[rpmget]
top_dir = rpms
layout = true
pkg_tool = rpm

[stuff]
file = http://somewhere.over/the/rainbow.rpm
other = not_a_url
"""

HASRPM = """
[rpmget]
top_dir = rpms
layout = flat
pkg_tool = rpm

[stuff]
file = http://somewhere.over/the/rainbow.rpm
other = not_a_url
"""

USRCFG = """
[Common]
url_type = https
host = github.com
owner = VCTLabs
repo = el9-rpm-toolbox

arch = noarch
dist = el9
ext = rpm
release = 1

url_base = ${url_type}://${host}/${owner}/${repo}/releases/download
url_post = ${release}.${dist}.${arch}.${ext}

[Toolbox]
dae_tag = daemonizer-1.1.3
dc_tag = diskcache-5.6.3
hex_tag = hexdump-3.5.2
hon_tag = honcho-2.0.0.1
tui_tag = picotui-1.2.3.1
proc_tag = procman-0.6.0
atftp_tag = py3tftp-1.3.0
pyg_tag = pygtail-0.14.0.2
ctl_tag = pyprctrl-0.1.3
serv_tag = pyserv-1.8.4
stop_tag = stoppy-1.0.5
tftp_tag = tftpy-0.8.6.1
tc_tag = timed-count-2.0.0

tb_rpms =
  ${Common:url_base}/${atftp_tag}/python3-${atftp_tag}-${Common:url_post}
  ${Common:url_base}/${tftp_tag}/python3-${tftp_tag}-${Common:url_post}
  ${Common:url_base}/${dc_tag}/python3-${dc_tag}-${Common:url_post}
  ${Common:url_base}/${dae_tag}/python3-${dae_tag}-${Common:url_post}
  ${Common:url_base}/${hex_tag}/python3-${hex_tag}-${Common:url_post}
  ${Common:url_base}/${hon_tag}/python3-${hon_tag}-${Common:url_post}
  ${Common:url_base}/${proc_tag}/python3-${proc_tag}-${Common:url_post}
  ${Common:url_base}/${pyg_tag}/python3-${pyg_tag}-${Common:url_post}
  ${Common:url_base}/${ctl_tag}/python3-${ctl_tag}-${Common:url_post}
  ${Common:url_base}/${tc_tag}/python3-${tc_tag}-${Common:url_post}
  ${Common:url_base}/${tui_tag}/python3-${tui_tag}-${Common:url_post}
  ${Common:url_base}/${stop_tag}/python3-${stop_tag}-${Common:url_post}
  ${Common:url_base}/${serv_tag}/python3-${serv_tag}-${Common:url_post}
"""


def test_cfg_bad_layout():
    parser = CfgParser()
    cfg_str = BADLAYOUT
    parser.read_string(cfg_str)
    with pytest.raises(CfgSectionError) as excinfo:
        res = validate_config(parser, SCHEMA)
    print(excinfo.value)
    assert 'Validation errors found in defaults' in str(excinfo.value)


def test_cfg_no_default_section():
    parser = CfgParser()
    parser.read_string(USRCFG)
    with pytest.raises(CfgSectionError) as excinfo:
        res = validate_config(parser, SCHEMA)
    assert 'Config section [rpmget]' in str(excinfo.value)


def test_cfg_missing_required_default():
    parser = CfgParser()
    cfg_str = NOTCFG + '\n' + USRCFG
    parser.read_string(cfg_str)
    with pytest.raises(CfgSectionError) as excinfo:
        res = validate_config(parser, SCHEMA)
    assert 'Validation errors found' in str(excinfo.value)


def test_cfg_no_valid_url():
    parser = CfgParser()
    cfg_str = NOURL
    parser.read_string(cfg_str)
    with pytest.raises(CfgSectionError) as excinfo:
        res = validate_config(parser, SCHEMA)
    assert 'must contian a valid URL' in str(excinfo.value)


def test_cfg_bad_valid_url():
    parser = CfgParser()
    cfg_str = BADURL
    parser.read_string(cfg_str)
    with pytest.raises(CfgSectionError) as excinfo:
        res = validate_config(parser, SCHEMA)
    assert 'Invalid URL scheme' in str(excinfo.value)


def test_cfg_minimum_valid_url():
    parser = CfgParser()
    cfg_str = HASRPM
    parser.read_string(cfg_str)
    res = validate_config(parser, SCHEMA)
    assert res is True


def test_cfg_valid_default_config():
    config, _ = load_config()
    print(config.sections())
    res = validate_config(config, SCHEMA)
    assert res is True
