import argparse
import array
import os
import sys

from env import Vars, envDefault
from helpers import get_logger
from src import AudibleTools, Daemon, DaemonConfig


def main(prog: str, args: array):
    parser = argparse.ArgumentParser(prog=prog, description='Monitor a directory for new files and triggers mp3 conversion when found')
    parser.add_argument('-o', '--out', default=envDefault(Vars.OUTPUT_DIR, ''),
        help='The base path for the output directory for the mp3s')
    parser.add_argument('--author-dir', default=envDefault(Vars.USE_AUTHOR_DIR, True), action=argparse.BooleanOptionalAction,
        help='Whether or not to create an author parent directory for the mp3 files')
    parser.add_argument('--title-dir', default=envDefault(Vars.USE_TITLE_DIR, True), action=argparse.BooleanOptionalAction,
        help='Whether or not to create a book title directory for the mp3 files')
    parser.add_argument('-b', '--activation-bytes', default=envDefault(Vars.ACTIVATION_BYTES, ''),
        help='The activation bytes used to decrypt audible DRM (automatic probe if not passed)')
    parser.add_argument('-t', '--threads', default=envDefault(Vars.THREADS, 1), type=int,
        help='The number of processors')
    parser.add_argument('-i', '--interval', default=envDefault(Vars.INTERVAL, 5), type=int,
        help='The interval in seconds to check for new files')
    parser.add_argument('-v', '--verbose', default=envDefault(Vars.VERBOSITY, 0), action='count')
    parser.add_argument('path', default=envDefault(Vars.INPUT_DIR, ''),
        help='The directory that we are going to monitor')

    options = parser.parse_args(args)

    if options.path is None or not options.path.strip():
        parser.print_usage()
        sys.exit(1)

    logger = get_logger(__name__, options.verbose)
    audible = AudibleTools(options.out, logger)

    config = DaemonConfig(
        activation_bytes=options.activation_bytes,
        output_dir=options.out,
        create_author_dir=options.author_dir,
        create_title_dir=options.title_dir,
        interval=options.interval,
        threads=options.threads,
    )

    try:
        Daemon(config=config, audible=audible, logger=logger).run(options.path)
    except Exception as e:
        logger.exception(e)

if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1:])
