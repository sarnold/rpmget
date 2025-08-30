"""
rpmget workflow helper via httpx and configparser.
"""

import logging
import os
from configparser import ConfigParser, ExtendedInterpolation
from importlib.metadata import version
from pathlib import Path
from string import Template
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from cerberus import Validator

__version__ = version('rpmget')

__all__ = [
    "__version__",
    "CfgParser",
    "CfgSectionError",
    "FileTypeError",
    "check_url_str",
    "create_macros",
    "find_rpm_urls",
    "load_config",
    "url_is_valid",
    "validate_config",
]

SCHEMA = {
    'repo_dir': {'type': 'string'},
    'top_dir': {'type': 'string', 'empty': False},
    'layout': {'type': 'string', 'anyof_regex': ['^flat', '^tree']},
    'pkg_tool': {'type': 'string', 'anyof_regex': ['^rpm', '^yum', '^dnf']},
}

CFG = """
[rpmget]
repo_dir = ~/repos
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
dc_tag = diskcache-5.6.3
hex_tag = hexdump-3.5.2
hon_tag = honcho-2.0.0.1
proc_tag = procman-0.6.0

tb_rpms =
  ${Common:url_base}/${dc_tag}/python3-${dc_tag}-${Common:url_post}
  ${Common:url_base}/${hex_tag}/python3-${hex_tag}-${Common:url_post}
  ${Common:url_base}/${hon_tag}/python3-${hon_tag}-${Common:url_post}
  ${Common:url_base}/${proc_tag}/python3-${proc_tag}-${Common:url_post}
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


class FileTypeError(Exception):
    """
    Raise if the file extension is not in the allowed extensions list::

      ['.ini', '.cfg', '.conf']
    """

    __module__ = Exception.__module__


class CfgSectionError(Exception):
    """
    Raise if the config section [rpmget] does not exist, normally at
    the top of the config file. This section must exist and contain
    the required keys and valid values::

      [rpmget]
      repo_dir
      top_dir = rpms
      layout = tree
      pkg_tool = rpm

    Also raised for invalid URL errors.
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
            allow_no_value=True,
        )


def check_url_str(str_val: str) -> bool:
    """
    Simple string check for http ... .rpm
    """
    return str_val.startswith('http') and str_val.endswith('.rpm')


def create_layout(topdir: str, layout: str):
    """
    Create layout for destination directory based on the ``layout`` cfg
    parameter, either flat or the standard RPM tree. Satisfies all of
    the current layout items: REQ006, REQ007, and REQ008.

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


def find_rpm_urls(config: CfgParser) -> List[str]:
    """
    Find all the (hopefully valid) URLs.
    """
    valid_urls: List = []
    sections: List[str] = config.sections()
    sections.append("DEFAULT")
    for section in sections:
        for _, value in config.items(section):
            urls = [x for x in value.splitlines() if x != '']
            for url in urls:
                if check_url_str(url) and url_is_valid(url):
                    valid_urls.append(url)
    return valid_urls


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
        if not all([parsed_url.scheme, parsed_url.netloc]):
            msg = f'Invalid URL scheme, address, or file target in {parsed_url}'
            raise CfgSectionError(msg)
        url_valid = True
    except ValueError:
        logging.error("Must be a valid URL ending in .rpm: %s", rpm_url)
    return url_valid


def validate_config(config: CfgParser, stop_on_error: bool = True) -> bool:
    """
    Validate minimum config sections and make sure [rpmget] section exists
    with required options (see design item SDD003).

    :param cfg_parse: loaded CfgParser instance
    :param stop_on_error: boolean flag
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
    default_is_valid = v.validate(data, SCHEMA)

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
                        is_valid = check_url_str(url) and url_is_valid(url)
                        if not is_valid and stop_on_error:
                            break

    if not is_valid:
        msg = 'At least one URL string failed to validate'
        raise CfgSectionError(msg)

    return is_valid
