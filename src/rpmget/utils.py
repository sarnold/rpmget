"""
Utility functions.
"""

import glob
import logging
import os
import re
import subprocess as sp
from pathlib import Path
from shlex import split
from shutil import copy, which
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from tqdm import tqdm

from . import CfgParser

logger = logging.getLogger('rpmget.utils')


def check_for_rpm(pgm: str = 'rpm') -> str:
    """
    Make sure we can find the ``rpm`` binary in the user environment
    and return a path string.

    :returns: program path string
    """
    rpm_path = which(pgm)
    if not rpm_path:
        logger.error('Cannot continue, no path found for %s', pgm)
        raise FileNotFoundError(f"{pgm}: program not found in PATH")
    return rpm_path


def copy_rpms(src_dir: str, dst_dir: str):
    """
    Copy .rpm globs while preserving arch dirs.
    """
    for p in glob.glob('**', recursive=True, root_dir=src_dir):
        if os.path.isfile(os.path.join(src_dir, p)) and re.search('\\.rpm', p):
            os.makedirs(os.path.join(dst_dir, os.path.dirname(p)), exist_ok=True)
            copy(os.path.join(src_dir, p), os.path.join(dst_dir, p))


def download_progress_bin(url: str, dst: str, layout: str, timeout: float = 10.0) -> str:
    """
    Download a single binary with progress meter and default timeout.
    Create arch dir or top_dir depending on layout setting

    :param url: URL to download
    :param dst: top-level destination directory
    :param timeout: httpx client timeout
    :returns: name of downloaded file
    """
    arch_path: str = ''
    rpm_file: str = urlparse(url).path.rsplit("/", maxsplit=1)[1]
    rpm_arch: str = rpm_file.rsplit('.', maxsplit=2)[-2]
    if layout == "tree":
        arch_path = 'SRPMS' if rpm_arch == 'src' else f'RPMS/{rpm_arch}'
    download_file: Path = Path(dst) / arch_path / rpm_file
    download_file.parent.mkdir(parents=True, exist_ok=True)

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


def manage_repo(config: CfgParser, temp_path: Optional[Path] = None):
    """
    Create or update rpm repository using createrepo tool. Requires an
    existing rpm tree with one or more packages.
    """
    if config['rpmget']['repo_dir'] == '':
        raise FileNotFoundError("repo_dir cannot be an empty string")

    cr_name = "createrepo_c"
    cr_path = ""
    try:
        cr_path = check_for_rpm(cr_name)
    except FileNotFoundError as exc:
        logger.error('%s', repr(exc))
        return

    cfg_top = os.path.expanduser(config['rpmget']['top_dir'])
    top_path = str(temp_path / cfg_top) if temp_path else cfg_top
    cfg_repo = os.path.expanduser(config['rpmget']['repo_dir'])
    repo_path = str(temp_path / cfg_repo) if temp_path else cfg_repo

    top_src = Path(top_path) / 'SRPMS'
    top_bin = Path(top_path) / 'RPMS'

    if os.path.exists(top_src) and get_filelist(str(top_src)):
        copy_rpms(
            os.path.join(top_path, 'SRPMS'),
            os.path.join(os.path.join(repo_path, 'SRPMS'), 'Packages'),
        )

    if os.path.exists(top_bin) and get_filelist(str(top_bin)):
        copy_rpms(
            os.path.join(top_path, 'RPMS'),
            os.path.join(os.path.join(repo_path, 'RPMS'), 'Packages'),
        )

    if cr_path:
        cr_srcs_path = Path(repo_path) / 'SRPMS'
        cr_bins_path = Path(repo_path) / 'RPMS'
        cr_str = "--compatibility --verbose --update"
        cr_srcs = f'{cr_name} {cr_str} {str(cr_srcs_path.absolute())}'
        cr_bins = f'{cr_name} {cr_str} {str(cr_bins_path.absolute())}'

        if cr_srcs_path.resolve().exists():
            try:
                logger.debug('srcs cmdline: %s', cr_srcs)
                res = sp.check_output(split(cr_srcs), stderr=sp.STDOUT, text=True)
                logger.debug('srcs: %s', res)
            except sp.CalledProcessError as exc:
                logger.error('srcs: %s', exc)

        if cr_bins_path.resolve().exists():
            try:
                logger.debug('bins cmdline: %s', cr_bins)
                res = sp.check_output(split(cr_bins), stderr=sp.STDOUT, text=True)
                logger.debug('bins: %s', res)
            except sp.CalledProcessError as exc:
                logger.error('bins: %s', exc)
