"""
rpmget workflow helper via httpx and configparser.
"""

import logging
import os
from configparser import ConfigParser, ExtendedInterpolation
from importlib.metadata import version
from pathlib import Path
from string import Template
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from cerberus import Validator

__version__ = version('rpmget')

__all__ = [
    "__version__",
    "CfgParser",
    "CfgSectionError",
    "FileTypeError",
    "create_macros",
    "load_config",
    "validate_config",
]

SCHEMA = {
    'top_dir': {'type': 'string', 'empty': False},
    'layout': {'type': 'string', 'anyof_regex': ['^flat', '^tree']},
    'pkg_tool': {'type': 'string', 'anyof_regex': ['^rpm', '^yum', '^dnf']},
}

CFG = """
[rpmget]
top_dir = rpmbuild
layout = flat
pkg_tool = rpm

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

RPM_TREE = ["BUILD", "BUILDROOT", "RPMS", "SOURCES", "SPECS", "SRPMS"]

RPM_TPL = """%packager ${user}
%_topdir ${home}/${top_dir}
%_tmppath ${home}/${top_dir}/tmp
"""

CTX = {
    'home': '',
    'user': '',
    'top_dir': '',
}


def create_macros(topdir: str) -> str:
    """
    Render a string template.
    """
    CTX.update(
        {
            'home': str(Path.home()),
            'user': Path.home().stem,
            'top_dir': os.path.relpath(Path(topdir), str(Path.home())),
        }
    )
    return Template(RPM_TPL).substitute(CTX)


class FileTypeError(Exception):
    """
    Raise if the file extension is not in the allowed extensions list::

      ['.ini', '.cfg', '.conf']
    """

    __module__ = Exception.__module__


class CfgSectionError(Exception):
    """
    Raise if the config section DEFAULT does not exist, normally at
    the top of the config file. This section must exist and contain
    the required options::

      [rpmget]
      top_dir = rpms
      layout = true
      pkg_tool = rpm

    Also raised for invalid or missing URL in any section.
    """

    __module__ = Exception.__module__


class CfgParser(ConfigParser):
    """
    Simple subclass with extended interpolation and no empty lines in
    values (see design item SDD002).
    """

    def __init__(self, *args, **kwargs):
        """
        Init with required non-default options.
        """
        super().__init__(
            *args,
            **kwargs,
            interpolation=ExtendedInterpolation(),
            empty_lines_in_values=False,
        )


def create_layout(topdir: str, layout: str):
    """
    Create layout for destination directory based on the ``layout`` cfg
    parameter, either flat or the standard RPM tree. Satisfies both
    REQ006 and REQ007.

    :param topdir: destination directory for downloaded rpms
    :param layout: type of destination directory layout
    """
    if layout == 'flat':
        Path(topdir).mkdir(parents=True, exist_ok=True)
    if layout == 'tree':
        macros = Path(topdir) / '.rpmmacros'
        for name in RPM_TREE:
            path = Path(topdir) / name
            path.mkdir(parents=True, exist_ok=True)
        text = create_macros(topdir)
        macros.write_text(text)


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
        with open(cfgfile, 'r') as configfile:  # pylint: disable=unspecified-encoding
            config.read_file(configfile)
        logging.debug('Using config: %s', str(cfgfile.resolve()))

    return config, cfgfile


def url_is_valid(rpm_url: str) -> bool:
    """
    Validate rpm URL string using urlparse and rpm extension check.

    ;param rpm_url: full url string ending in .rpm
    :returns: True if checks pass
    """
    url_valid: bool = False
    try:
        parsed_url = urlparse(rpm_url)
        logging.debug('Parsed URL: %s', repr(parsed_url))
        if not all([parsed_url.scheme, parsed_url.netloc, rpm_url.endswith('.rpm')]):
            msg = f'Invalid URL scheme, address, or file target in {parsed_url}'
            raise CfgSectionError(msg)
        url_valid = True
    except ValueError:
        logging.error("Must be a valid URL ending in .rpm: %s", rpm_url)
    return url_valid


def validate_config(config: CfgParser, schema: Dict) -> bool:
    """
    Validate minimum config sections and make sure [rpmget] section exists
    with required options (see design item SDD003).

    :param cfg_parse: loaded CfgParser instance
    :param schema: cerberus schema dict
    :returns: boolean ``is_valid`` flag
    """
    is_valid = False
    if 'rpmget' not in config.sections():
        msg = f'Config section [rpmget] is required: {config.sections()}'
        raise CfgSectionError(msg)

    data = config['rpmget']
    v = Validator()
    v.allow_unknown = True
    v.require_all = True
    default_is_valid = v.validate(data, schema)

    if not default_is_valid:
        msg = f'Validation errors found in defaults: {v.errors}'
        raise CfgSectionError(msg)

    for section in config.sections():
        for option in config.options(section):
            value = config.get(section, option)
            if 'http' in value:
                if '.rpm' in value:
                    string_val = config[section][option]
                    urls = [x for x in string_val.splitlines() if x != '']
                    for url in urls:
                        is_valid = url_is_valid(url)
                        if not is_valid:
                            break

    if not is_valid:
        msg = 'At least one URL string failed to validate'
        raise CfgSectionError(msg)

    return is_valid
