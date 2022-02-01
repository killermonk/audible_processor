import argparse
import logging
import sys
from array import array

from src.parser import Parser, ParserConfig


def _get_logger(verbosity: int) -> logging.Logger:
    if verbosity == 0:
        log_level = logging.WARNING
        formatter = logging.Formatter('%(message)s')
    elif verbosity == 1:
        log_level = logging.INFO
        formatter = logging.Formatter('%(levelname)s - %(message)s')
    elif verbosity >= 2:
        log_level = logging.DEBUG
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger

def main(prog: str, args: array):
    parser = argparse.ArgumentParser(prog=prog, description='Convert an audiobook into chapterized mp3s')
    parser.add_argument('-o', '--out', default='',
        help='The base path for the output directory for the mp3s')
    parser.add_argument('-a', '--author',
        help='Override the author name for the output folders')
    parser.add_argument('--author-dir', default=True, action=argparse.BooleanOptionalAction,
        help='Whether or not to create an author parent directory for the mp3 files')
    parser.add_argument('-t', '--title',
        help='Override the book title name for the output folders')
    parser.add_argument('--title-dir', default=True, action=argparse.BooleanOptionalAction,
        help='Whether or not to create a book title directory for the mp3 files')
    parser.add_argument('-v', '--verbose', default=0, action='count')
    parser.add_argument('-f', '--force', default=False, action='store_true',
        help='Force the parsing to continue if a recoverable error is encountered')
    parser.add_argument('-b', '--activation-bytes',
        help='The activation bytes used to decrypt audible DRM. Automatic probe if not passed.')
    parser.add_argument('file', nargs='+', action='extend',
        help='The file that we are going to convert')

    options = parser.parse_args(args)

    logger = _get_logger(options.verbose)

    for file in options.file:
        config = ParserConfig(
            activation_bytes=options.activation_bytes,
            input_file=file,
            output_dir=options.out,
            author_override=options.author,
            create_author_dir=options.author_dir,
            title_override=options.title,
            create_title_dir=options.title_dir,
            force=options.force,
        )

        try:
            Parser(config=config, logger=logger).run()
        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1:])
