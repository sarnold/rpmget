"""
rpmget workflow helper via httpx and configparser.
"""

import logging
import os
from configparser import ConfigParser, ExtendedInterpolation
from importlib.metadata import version
from pathlib import Path
from typing import Optional, Tuple

__version__ = version('rpmget')

__all__ = [
    "__version__",
    "CFG",
    "FileTypeError",
    "CfgParser",
    "load_config",
]

CFG = """
[Common]
top_dir = rpms
pkg_tool = rpm
flat_layout = true

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


class FileTypeError(Exception):
    """
    Raise when the file extension is not in the allowed extensions list::

      ['.ini', '.cfg', '.conf']
    """

    __module__ = Exception.__module__


class CfgParser(ConfigParser):
    """
    Simple subclass with extended interpolation and no empty lines in
    values.
    """

    def __init__(self, *args, **kwargs):
        """
        Init with specific non-default options.
        """
        super().__init__(
            *args,
            **kwargs,
            interpolation=ExtendedInterpolation(),
            empty_lines_in_values=False,
        )


def load_config(ufile: str = '') -> Tuple[CfgParser, Optional[Path]]:
    """
    Read the configuration file and load the data. If ENV path or local
    file is not found in current directory, the default cfg will be loaded.
    Note that passing ``ufile`` as a parameter overrides the above default.

    :param ufile: path string for config file
    :returns: cfg parser and file Path-or-None
    :raises FileTypeError: if the input file is not in the allowed list
                           ['.ini', '.cfg', '.conf']
    """
    extensions = ['.ini', '.cfg', '.conf']
    ucfg = os.getenv('RPMGET_CFG', default='')

    cfgfile = Path(ucfg) if ucfg else Path(ufile) if ufile else None

    if cfgfile and cfgfile.suffix not in extensions:
        msg = f'Invalid file extension: {cfgfile.name}'
        raise FileTypeError(msg)

    config = CfgParser()
    if not cfgfile:
        config.read_string(CFG)
    else:
        config.read_file(open(cfgfile))
        logging.debug('Using config: %s', str(cfgfile.resolve()))

    return config, cfgfile
