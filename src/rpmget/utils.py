"""
Utility functions.
"""

import logging
import os
from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from shutil import which
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from tqdm import tqdm

from . import CFG

logger = logging.getLogger('rpmget')


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


def check_for_rpm(pgm: str = 'rpm') -> str:
    """
    Make sure we can find the ``rpm`` binary in the user environment
    and return a path string.

    :returns: program path string
    """
    rpm_path = which(pgm)
    if not rpm_path:
        print('Cannot continue, no path found for rpm')
        raise FileNotFoundError("rpm not found in PATH")
    return rpm_path


def download_progress_bin(url: str, dst: str, timeout: float = 10.0) -> str:
    """
    Download a single binary with progress meter.
    """
    rpm_file: str = urlparse(url).path.rsplit("/", maxsplit=1)[1]
    download_file: Path = Path(dst) / rpm_file
    Path(dst).mkdir(parents=True, exist_ok=True)

    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
        total = int(response.headers["Content-Length"])
        logger.debug('File size: %s', total)

        with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as progress:
            num_bytes_downloaded = response.num_bytes_downloaded
            for chunk in response.iter_bytes():
                download_file.write_bytes(chunk)
                progress.update(response.num_bytes_downloaded - num_bytes_downloaded)
                num_bytes_downloaded = response.num_bytes_downloaded

    return download_file.name


def get_filelist(dirname: str, filepattern: str = '*.rpm') -> List[str]:
    """
    Get path objects matching ``filepattern`` starting at ``dirname`` and
    return a list of matching paths for any files found.

    :param dirname: directory name to search in
    :param filepattern: extension of the form ``*.<ext>``
    :returns: file path strings
    """
    file_list = []
    filenames = Path(dirname).rglob(filepattern)
    for pfile in list(filenames):
        file_list.append(str(pfile))
    logger.info('Found rpm files: %s', file_list)
    return file_list


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
