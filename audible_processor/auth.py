import argparse
import array
import sys

from env import Vars, envDefault
from helpers import get_logger
from src import AudibleTools


def main(prog: str, args: array):
    parser = argparse.ArgumentParser(prog=prog, description='Monitor a directory for new files and triggers mp3 conversion when found')
    parser.add_argument('-o', '--out', default=envDefault(Vars.OUTPUT_DIR, ''),
        help='The base path for the output directory for the mp3s')
    parser.add_argument('-v', '--verbose', default=envDefault(Vars.VERBOSITY, 0), action='count')

    options = parser.parse_args(args)

    logger = get_logger(__name__, options.verbose)

    AudibleTools(options.out, logger).get_activation_bytes_from_audible()

if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1:])
