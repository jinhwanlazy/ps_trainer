import argparse
import sys
import traceback
import logging

from . import __logfile__, __datadir__
from ps_trainer.cmd import get_command_list

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs=1, choices=list(get_command_list().keys()))
    parser.add_argument('-v', '--verbose', action="store_true")
    args = parser.parse_args()
    return args


def init_logger(verbose):
    logging.basicConfig(
        filename=__logfile__,
        encoding='utf-8',
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s:%(message)s',
    )
    stdout_handler = logging.StreamHandler(sys.stdout)
    if verbose:
        stdout_handler.setLevel(logging.DEBUG)
    else:
        stdout_handler.setLevel(logging.INFO)
    logger = logging.getLogger()
    logger.addHandler(stdout_handler)
    logger.debug(f'data directory: {__datadir__}')
    logger.debug(f'log filepath: {__logfile__}')


def main():
    args = get_args()
    init_logger(args.verbose)
    get_command_list()[args.command[0]]()
        

if __name__ == '__main__':
    main()
