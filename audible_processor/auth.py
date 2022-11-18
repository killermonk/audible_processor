import argparse
import array
import sys

from src import AudibleTools
from helpers import get_logger

def main(prog: str, args: array):
    parser = argparse.ArgumentParser(prog=prog, description='Monitor a directory for new files and triggers mp3 conversion when found')
    parser.add_argument('-o', '--out', default='',
        help='The base path for the output directory for the mp3s')
    parser.add_argument('-v', '--verbose', default=0, action='count')

    options = parser.parse_args(args)

    logger = get_logger(__name__, options.verbose)

    AudibleTools(options.out, logger).get_activation_bytes_from_audible()

if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1:])
