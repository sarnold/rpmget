"""
Utility functions.
"""

import logging
from pathlib import Path
from shutil import which
from typing import List
from urllib.parse import urlparse

import httpx
from tqdm import tqdm


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
        print(f'size: {total}')

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
    logging.info('Found rpm files: %s', file_list)
    return file_list
