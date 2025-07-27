"""
rpmget main init, run, and self-test functions.
"""

import argparse
import importlib
import logging
import sys
import warnings
from pathlib import Path
from typing import Optional

from . import __version__, load_config

# from logging_tree import printout  # debug logger environment


def self_test(fname: Optional[Path]):
    """
    Basic sanity check using ``import_module``.
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

    _, cfg_file = load_config(str(fname)) if fname else load_config()
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
        ucfg, cfg = mod.load_config(str(fname)) if fname else mod.load_config()
        cfgfile = cfg.resolve() if cfg else None
        print(f'  {cfgfile}')

    except (NameError, KeyError, ModuleNotFoundError) as exc:
        logging.error("FAILED: %s", repr(exc))

    print("-" * 80)


def main(argv=None):  # pragma: no cover
    """
    Collect and process command options/arguments and init app dirs,
    then launch the file manager.
    """
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Download manager for rpm files',
    )
    parser.add_argument('--version', action="version", version=f"%(prog)s {__version__}")
    parser.add_argument('-S', '--show', help='display user config', action='store_true')
    parser.add_argument('-t', '--test', help='run sanity checks', action='store_true')
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

    args = parser.parse_args()

    # basic logging setup must come before any other logging calls
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(stream=sys.stdout, level=log_level)
    logger = logging.getLogger('rpmget')
    # printout()  # logging_tree

    ufile: Optional[Path]
    infile = args.file
    if infile and not Path(infile).exists():
        logger.error('Input file %s not found!', infile)
        sys.exit(1)
    if infile:
        ufile = Path(infile)
        ucfg, _ = load_config(ufile=infile)
    else:
        ucfg, ufile = load_config()

    if args.test:
        self_test(ufile)
        sys.exit(0)
    if args.show:
        show_paths(ufile)
        sys.exit(0)
    if args.dump:
        ucfg.write(sys.stdout)
        sys.exit(0)

    if len(argv) == 1 and (ufile is None or not ufile.exists()):
        logger.error('No cfg file found; use the --dump arg or create a cfg file')
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
