"""
Utility functions.
"""

import logging
import os
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
    Copy .rpm globs while preserving arch dirs. This now replicates what
    glob.glob(root_dir=src_dir) does. Stem directories are each rpm tree
    with rpm files, ie SRPMS and RPMS.

    :param src_dir: source dir is top_dir with stem
    :param dst_dir: destination dir is repo_dir with stem
    """
    for p in [str(Path(p).relative_to(src_dir)) for p in get_filelist(src_dir)]:
        logger.debug('Found glob: %s', p)
        if os.path.isfile(os.path.join(src_dir, p)):
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
    client = httpx.Client(follow_redirects=True)

    remove_borked_file: bool = False
    return_file_name: str = download_file.name
    with download_file.open("wb") as file_handle:
        with client.stream("GET", url, timeout=timeout) as response:
            total = response.headers.get("Content-Length")
            logger.info('%s size: %s', download_file.name, total)
            if response.status_code == 200:
                if total is None:
                    content = response.content
                    file_handle.write(content)
                else:
                    with tqdm(
                        total=int(total), unit_scale=True, unit_divisor=1024, unit="B"
                    ) as progress:
                        num_bytes_downloaded = response.num_bytes_downloaded
                        for chunk in response.iter_bytes():
                            file_handle.write(chunk)
                            progress.update(
                                response.num_bytes_downloaded - num_bytes_downloaded
                            )
                            num_bytes_downloaded = response.num_bytes_downloaded
            else:
                logging.error("Failed to download %s", url)
                remove_borked_file = True
                return_file_name = "File Error"

    if remove_borked_file:
        download_file.unlink()

    return return_file_name


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
    logger.info('Found %d rpm files', len(file_list))
    logger.debug('Found rpm files: %s', file_list)
    return file_list


def manage_repo(config: CfgParser, temp_path: Optional[Path] = None):
    """
    Create or update rpm repository using createrepo tool. Requires an
    existing rpm tree with one or more packages. Satisfies REQ009.
    """
    cr_name = "createrepo_c"
    try:
        check_for_rpm(cr_name)
    except FileNotFoundError as exc:
        logger.error('%s', repr(exc))
        return

    cfg_top = os.path.expanduser(config['rpmget']['top_dir'])
    top_path = str(temp_path / cfg_top) if temp_path else cfg_top
    cfg_repo = os.path.expanduser(config['rpmget']['repo_dir'])
    repo_path = str(temp_path / cfg_repo) if temp_path else cfg_repo

    top_src = Path(top_path) / 'SRPMS'
    top_bin = Path(top_path) / 'RPMS'

    rpm_paths = [p for p in (top_src, top_bin) if p.exists() and get_filelist(str(p))]

    for path in rpm_paths:
        copy_rpms(
            str(path),
            os.path.join(os.path.join(repo_path, path.stem), 'Packages'),
        )

    cr_srcs_path = Path(repo_path) / top_src.stem
    cr_bins_path = Path(repo_path) / top_bin.stem

    cr_paths = [p for p in (cr_srcs_path, cr_bins_path) if p.exists()]

    for path in cr_paths:
        cr_str = "--compatibility --verbose"
        if path.joinpath('repodata', 'repomd.xml').exists():
            cr_str = cr_str + " --update"
        cr_cmd = f'{cr_name} {cr_str} {str(path.absolute())}'

        try:
            logger.debug('cmdline: %s', cr_cmd)
            res = sp.check_output(split(cr_cmd), stderr=sp.STDOUT, text=True)
            logger.debug('cmd result: %s', res)
        except sp.CalledProcessError as exc:
            logger.error('proc error: %s', exc)
