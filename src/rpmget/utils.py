"""
Utility functions.
"""

import hashlib
import json
import logging
import os
import subprocess as sp
from datetime import datetime
from pathlib import Path
from shlex import split
from shutil import copy, which
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from platformdirs import PlatformDirs
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
    for p in [
        str(Path(p).relative_to(src_dir)) for p in get_filelist(src_dir, resolve=False)
    ]:
        logger.debug('Found glob: %s', p)
        # if os.path.isfile(os.path.join(src_dir, p)):
        os.makedirs(os.path.join(dst_dir, os.path.dirname(p)), exist_ok=True)
        copy(os.path.join(src_dir, p), os.path.join(dst_dir, p))


def download_progress_bin(
    url: str, dst: str, layout: str, timeout: float, mdata: Dict
) -> str:
    """
    Download a single binary with progress meter and default timeout.
    Create arch dir or top_dir depending on layout setting

    :param url: URL to download
    :param dst: top-level destination directory
    :param layout: config layout
    :param timeout: httpx client timeout
    :param mdata: manifest data if available
    :returns: name of downloaded file
    """
    fsize: int = -1
    head_size: int = 0
    arch_path: str = ''
    rpm_file: str = urlparse(url).path.rsplit("/", maxsplit=1)[1]
    rpm_arch: str = rpm_file.rsplit('.', maxsplit=2)[-2]
    if layout == "tree":
        arch_path = 'SRPMS' if rpm_arch == 'src' else f'RPMS/{rpm_arch}'
    download_file: Path = Path(dst) / arch_path / rpm_file
    download_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info('Processing file: %s', download_file.name)
    remove_borked_file: bool = False
    return_file_name: str = str(download_file.resolve())
    if mdata:
        fsize = mdata["files"][download_file.name]["size"]
        logger.debug('Size from manifest: %s', fsize)
        with httpx.Client(follow_redirects=True) as cli:
            resp = cli.head(url)
            head_size = int(resp.headers.get('Content-Length'))
        logger.debug('Size from HEAD request: %s', head_size)
    current_size: int = 0
    if download_file.exists():
        current_size = download_file.stat().st_size
    keep_existing_file = head_size == fsize and head_size == current_size

    if keep_existing_file:
        return "ResourceSkipped"

    client = httpx.Client(follow_redirects=True)
    with client.stream("GET", url, timeout=timeout) as response:
        total = response.headers.get("Content-Length")
        logger.info('%s size: %s', download_file.name, total)
        with download_file.open("wb") as file_handle:
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
                return_file_name = "ResourceError"

    if remove_borked_file:
        download_file.unlink()

    return return_file_name


def compare_file_data(old: Dict, new: Dict) -> Dict:
    """
    Compare two dictionaries and return the difference result.

    :param old: old dict
    :param new: new dict
    :returns: any differences found
    """
    delta: Dict = {}
    if not old == new:
        for key, old_val in old.items():
            new_val = new[key]
            if old_val != new_val:
                delta.update({key: new_val})
    return delta


def get_file_data(path: Path) -> Tuple[str, Dict]:
    """
    Get manifest data for a single rpm file from input path and return
    a dictionary full of metadata. Current keys are given below.

    :param path: file target
    :returns: file metadata
    """
    name = path.name
    mtime = get_file_mtime(path)
    sha = get_file_hash(path)
    size = path.stat().st_size

    return name, {
        'digest': sha,
        'mtime': mtime,
        'name': name,
        'size': size,
    }


def get_file_hash(path: Path) -> str:
    """
    :param path: file target
    :returns: file digest using sha256
    """
    buf_size = 65536
    sha = hashlib.sha256()

    with open(path, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            sha.update(data)
    return sha.hexdigest()


def get_file_mtime(path: Path) -> str:
    """
    :param path: file target
    :returns: formatted time string
    """
    return datetime.fromtimestamp(path.stat().st_mtime).strftime('%m-%d-%Y %H:%M:%S')


def get_user_cachedir():
    """
    Return user cache directory per platform.

    :returns: user_cache_dir path as string
    """
    dirs = PlatformDirs("rpmget", "nerdboy")
    return dirs.user_cache_dir


def get_filelist(
    dirname: str, resolve: bool = True, fileglob: str = '*.rpm'
) -> List[str]:
    """
    Get path objects matching ``fileglob`` starting at ``dirname`` and
    return a list of resolved path strings of any files found. Set the
    ``resolve`` parameter to False to return relative paths when input
    path is relative.

    :param dirname: directory name to start search in
    :param fileglob: extension of the form ``*.<ext>``
    :returns: file path strings
    """
    file_list = []
    ext = fileglob.rsplit('.', maxsplit=1)[1]
    filenames = Path(dirname).rglob(fileglob)
    for pfile in list(filenames):
        path = pfile.resolve() if resolve else pfile
        file_list.append(str(path))
    logger.info('Found %d %s file(s)', len(file_list), ext)
    logger.debug('Found %s file(s): %s', ext, file_list)
    return file_list


def wrap_file_manifest(fdata: Dict[str, Dict], cfgname: str) -> Dict:
    """
    Wrap file data for json export.

    :param fdata: list of manifest dicts
    :param cfgname: parent config name
    :returns: data for json
    """

    return {
        'config': cfgname,
        'files': fdata,
    }


def create_manifest_data(files: List[str], cfile: str) -> Dict:
    """
    Create new manifest data from a list of downloaded files and return
    a nested dictionary.

    :param files: list of downloaded filenames
    :param cfile: matching config filename
    :returns: manifest data
    """
    paths = [Path(p) for p in sorted(files)]
    logger.debug('Found rpm paths: %s', paths)
    # print(f'Found rpm paths: {paths}')

    file_data: Dict = {}
    for path in paths:
        name, data = get_file_data(path)
        file_data[name] = data
    mdata = wrap_file_manifest(file_data, cfile)
    return mdata


def read_manifest(mfile: Path, temp_path: str = "") -> Dict:
    """
    Read a manifest file and return the data.

    :param mfile: manifest file
    :param temp_path: use temp_path if provided
    :returns: manifest data
    """
    in_data: Dict
    man_path = temp_path if temp_path else get_user_cachedir()
    man_file = Path(man_path) / (mfile.name)
    with man_file.open() as dfile:
        in_data = json.load(dfile)
    return in_data


def write_manifest(mdata: Dict, mfile: Path):
    """
    Write a new manifest file where the name is derived from the
    associated config file name.

    :param mdata: manifest data
    :param mfile: manifest file
    """
    mfile.parent.mkdir(parents=True, exist_ok=True)
    out = json.dumps(mdata, indent=2, sort_keys=True)
    mfile.write_text(out)


def compare_manifest_data(old: Dict, new: Dict) -> List:
    """
    Compare full manifest data.

    :param old: manifest data
    :param new: manifest data
    """
    msgs: List = []
    if not old["config"] == new["config"]:
        logger.warning(
            'Config mismatch: %s not equal to %s', old["config"], new["config"]
        )
        msgs.append(new["config"])
        return msgs
    old_files = list(old['files'].values())
    new_files = list(new['files'].values())
    for o, n in zip(old_files, new_files):
        diff = compare_file_data(o, n)
        if not diff:
            logger.debug('No differences in file data: %s', n["name"])
            continue
        logger.debug('Manifest changes: %s', diff)
        msgs.append(diff)
    return msgs


def load_manifest(cfile: str, temp_path: str = "") -> Dict:
    """
    If available, load a manifest file *before* config loop run.

    :param cfile: matching config filename
    :param temp_path: use temp_path if provided
    """
    manifest_data: Dict = {}
    man_path = temp_path if temp_path else get_user_cachedir()
    manifest = Path(man_path) / f"{cfile}.json"
    if manifest.exists():
        manifest_data = read_manifest(manifest, temp_path)
    return manifest_data


def process_file_manifest(
    files: List[str], cfile: str, temp_path: str = ""
) -> List[Dict]:
    """
    Process manifest file after successful config loop run.

    :param files: list of downloaded filenames
    :param cfile: matching config filename
    :param temp_path: use temp_path if provided
    :returns: list of differences
    """
    results: List = []
    man_path = temp_path if temp_path else get_user_cachedir()
    manifest = Path(man_path) / f"{cfile}.json"
    verb = "Found" if manifest.exists() else "Creating"
    logger.info('%s manifest: %s', verb, str(manifest))

    current_data = create_manifest_data(files, cfile)
    if not manifest.exists():
        write_manifest(current_data, manifest)
        results.append(str(manifest))
    else:
        previous_data = read_manifest(manifest, temp_path)
        results = compare_manifest_data(previous_data, current_data)
        logger.debug('Manifest processing result: %s', results)
        if results:
            write_manifest(current_data, manifest)
            logger.info('Updated manifest: %s', str(manifest))
    return results


def manage_repo(config: CfgParser, debug: bool = False, temp_path: Optional[Path] = None):
    """
    Create or update rpm repository using createrepo tool. Requires an
    existing rpm tree with one or more packages. Satisfies REQ009.

    :param config: loaded CfgParser instance
    :param debug: enables verbose on ``repo_tool``
    :param temp_path: prepended to config paths (mainly for testing)
    """
    cr_name: str = config['rpmget']['repo_tool']
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
    logger.info('Found rpm src paths: %s', rpm_paths)

    for path in rpm_paths:
        copy_rpms(
            str(path),
            os.path.join(os.path.join(repo_path, path.stem), 'Packages'),
        )

    cr_srcs_path = Path(repo_path) / top_src.stem
    cr_bins_path = Path(repo_path) / top_bin.stem

    cr_paths = [p for p in (cr_srcs_path, cr_bins_path) if p.exists()]

    for path in cr_paths:
        cr_str = config['rpmget']['repo_args']
        dbg_str = "--verbose" if debug else ''
        if path.joinpath('repodata', 'repomd.xml').exists():
            cr_str = cr_str + " --update"
        cr_cmd = f'{cr_name} {cr_str} {dbg_str} {str(path.absolute())}'

        try:
            logger.debug('cmdline: %s', cr_cmd)
            res = sp.check_output(split(cr_cmd), stderr=sp.STDOUT, text=True)
            logger.debug('cmd result: %s', res)
        except sp.CalledProcessError as exc:
            logger.error('proc error: %s', exc)
