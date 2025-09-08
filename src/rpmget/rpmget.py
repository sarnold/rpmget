"""
rpmget main init, run, and self-test functions.
"""

import argparse
import importlib
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import List, Optional, Tuple

from . import (
    CfgParser,
    CfgSectionError,
    InvalidURLError,
    __version__,
    check_url_str,
    find_rpm_urls,
    load_config,
    url_is_valid,
    validate_config,
)
from .utils import download_progress_bin, manage_repo

# from logging_tree import printout  # debug logger environment


def self_test(fname: Optional[Path]):
    """
    Basic sanity check using ``import_module`` and ``load_config``.
    """
    print("Python version:", sys.version)
    print("-" * 80)

    modlist = ['rpmget.__init__', 'rpmget.utils']
    for modname in modlist:
        try:
            print(f'Checking module {modname}')
            mod = importlib.import_module(modname)
            print(mod.__doc__)

        except (NameError, KeyError, ModuleNotFoundError) as exc:
            logging.error("FAILED: %s", repr(exc))

    cfg, cfg_file = load_config(str(fname)) if fname else load_config()
    try:
        res = validate_config(cfg)  # SDD004
        logging.info("cfg valid: %s", res)
    except CfgSectionError:
        logging.error("cfg valid: False")

    print(f"file: {cfg_file}")
    if not cfg_file:
        warnings.warn(f"Cannot verify user file {cfg_file}", RuntimeWarning, stacklevel=2)

    print("-" * 80)


def show_paths(fname: Optional[Path]):
    """
    Display user configuration path if defined.
    """
    print("Python version:", sys.version)
    print("-" * 80)

    modname = 'rpmget'
    try:
        mod = importlib.import_module(modname)
        print(mod.__doc__)

        print("User cfg file:")
        _, cfg = mod.load_config(str(fname)) if fname else mod.load_config()
        cfgfile = cfg.resolve() if cfg else None
        print(f'  {cfgfile}')

    except (NameError, KeyError, ModuleNotFoundError) as exc:
        logging.error("FAILED: %s", repr(exc))

    print("-" * 80)


def main_arg_parser() -> argparse.ArgumentParser:
    """
    Function to parse command line arguments

    :param args: list of argument strings to parse
    :returns: parsed arguments
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Download manager for rpm files',
    )
    parser.add_argument('--version', action="version", version=f"%(prog)s {__version__}")
    parser.add_argument('-S', '--show', help='display user config', action='store_true')
    parser.add_argument('-t', '--test', help='run sanity checks', action='store_true')
    parser.add_argument(
        '-u', '--update', help='update repos with createrepo', action='store_true'
    )
    parser.add_argument(
        '-v',
        '--validate',
        help='run schema validation on active config',
        action='store_true',
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="display more processing info",
    )
    parser.add_argument(
        '-D',
        '--dump-config',
        help="dump active configuration to stdout",
        action='store_true',
        dest="dump",
    )
    parser.add_argument(
        "-c",
        "--configfile",
        dest="file",
        action="store",
        default=None,
        type=str,
        help="path to ini-style configuration file",
    )
    parser.add_argument(
        'url',
        nargs='*',
        metavar="URL",
        type=str,
        help="download (valid) URLs to current directory with no config",
    )

    return parser


def parse_command_line(argv):
    """
    Parse command line arguments. See -h option

    :param argv: arguments on the command line include caller file name
    :return arguments: parsed command line arguments
    """
    parser = main_arg_parser()

    return parser.parse_args(argv[1:])


def process_config_loop(config: CfgParser, temp_path: Optional[Path] = None) -> List[str]:
    """
    Main processing loop for user config data; enables self-validation and
    partial config parsing before processing urls.

    :param config: loaded CfgParser
    :param temp_path: temp Path to be prepended to top_dir

    :returns: list of downloaded filenames
    """
    files: List = []
    urls: List = []

    try:
        res = validate_config(config, stop_on_error=False)
        logging.debug('Current config is valid: %s', res)
    except CfgSectionError as exc:
        logging.error('%s', repr(exc))

    cfg_top = os.path.expanduser(config['rpmget']['top_dir'])
    top_dir = str(temp_path / cfg_top) if temp_path else cfg_top
    layout = config['rpmget']['layout']
    timeout = config.getfloat('rpmget', 'httpx_timeout')

    urls = find_rpm_urls(config)
    for url in urls:
        fname = download_progress_bin(url, top_dir, layout, timeout)
        files.append(fname)
    logging.debug('Downloaded file(s): %s', files)
    logging.info('Downloaded %d file(s)', len(files))
    return files


def collect_valid_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
    """
    Collect valid URL strings.

    :param urls: one or more URL strings
    :returns: lists of valid and bogus URLs
    """
    valid_urls: List = []
    bogus_urls: List = []

    for url in urls:
        if check_url_str(url) and url_is_valid(url):
            logging.debug('Found valid url: %s', url)
            valid_urls.append(url)
        else:
            logging.debug('Found bogus url: %s', url)
            bogus_urls.append(url)
    logging.info('Found %d bogus url(s)', len(bogus_urls))
    logging.info('Found %d valid url(s)', len(valid_urls))

    return valid_urls, bogus_urls


def process_urls(urls: List[str]) -> List[str]:
    """
    Process valid URL strings.

    :param urls: one or more URL strings
    :returns: list of downloaded filenames and/or errors
    """
    files: List = []
    vurls: List = []

    vurls, _ = collect_valid_urls(urls)
    if not vurls:
        msg = f"No valid URLs found in input urls: {urls}"
        raise InvalidURLError(msg)

    for url in vurls:
        fname = download_progress_bin(url, '.', 'flat', 15.0)
        files.append(fname)
    logging.debug('Downloaded file(s): %s', files)
    logging.info('Downloaded %d file(s)', len(files))

    return files


def main() -> None:  # pragma: no cover
    """
    Collect and process command options/arguments and setup logging,
    check for user config, then launch the file/download manager.

    :param args: argument
    """
    args = parse_command_line(sys.argv)

    # basic logging setup must come before any other logging calls
    httpx_level = logging.DEBUG if args.debug else logging.WARNING
    logging.getLogger('httpx').setLevel(httpx_level)
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(stream=sys.stdout, level=log_level)
    logger = logging.getLogger('rpmget')
    # printout()  # logging_tree

    if args.url and args.file:
        logger.warning('Config file %s is ignored when processing URL args', args.file)
    if args.url:
        try:
            _ = process_urls(args.url)
            sys.exit(0)
        except InvalidURLError as exc:
            logger.warning('No files downloaded: %s', repr(exc))
            sys.exit(1)

    ufile: Optional[Path]
    infile = args.file
    if infile and not Path(infile).exists():
        logger.error('Input file %s not found!', infile)
        sys.exit(1)
    if infile:
        ucfg, _ = load_config(ufile=infile)
        ufile = Path(infile)
    else:
        ucfg, ufile = load_config()

    if len(sys.argv) == 1 and (ufile is None or not ufile.exists()):
        logger.error('No cfg file found; use the --dump arg or create a cfg file')
        sys.exit(1)
    logger.info('Using input file %s', ufile)

    if args.test:
        self_test(ufile)
        sys.exit(0)
    if args.show:
        show_paths(ufile)
        sys.exit(0)
    if args.dump:
        ucfg.write(sys.stdout)
        sys.exit(0)
    if args.validate:
        try:
            res = validate_config(ucfg)
            logger.info('User config is valid: %s', res)
            sys.exit(0)
        except CfgSectionError as exc:
            logger.error('%s', repr(exc))
            sys.exit(1)

    if args.update:
        manage_repo(ucfg)
        sys.exit(0)

    _ = process_config_loop(ucfg)


if __name__ == "__main__":
    main()  # pragma: no cover
