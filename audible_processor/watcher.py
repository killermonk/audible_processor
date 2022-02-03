import argparse
import array
import multiprocessing as mp
import sys

from helpers import get_logger
from monitor.config import DaemonConfig
from monitor.daemon import Daemon


def main(prog: str, args: array):
    parser = argparse.ArgumentParser(prog=prog, description='Monitor a directory for new files and triggers mp3 conversion when found')
    parser.add_argument('-o', '--out', default='',
        help='The base path for the output directory for the mp3s')
    parser.add_argument('--author-dir', default=True, action=argparse.BooleanOptionalAction,
        help='Whether or not to create an author parent directory for the mp3 files')
    parser.add_argument('--title-dir', default=True, action=argparse.BooleanOptionalAction,
        help='Whether or not to create a book title directory for the mp3 files')
    parser.add_argument('-b', '--activation-bytes',
        help='The activation bytes used to decrypt audible DRM. Automatic probe if not passed.')
    parser.add_argument('-t', '--threads', default=1, type=int,
        help='The number of processors.')
    parser.add_argument('-v', '--verbose', default=0, action='count')
    parser.add_argument('path',
        help='The directory that we are going to monitor')

    options = parser.parse_args(args)

    logger = get_logger(__name__, options.verbose)

    config = DaemonConfig(
        activation_bytes=options.activation_bytes,
        output_dir=options.out,
        create_author_dir=options.author_dir,
        create_title_dir=options.title_dir,
        threads=options.threads,
    )

    try:
        Daemon(config=config, logger=logger).run(options.path)
    except Exception as e:
        logger.exception(e)

if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1:])
