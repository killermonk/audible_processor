import argparse
import logging
import sys
from array import array
from glob import glob
from parser.parser import Parser, ParserConfig

from helpers import get_logger


def file_generator(files):
    for path in files:
        for f in glob(path):
            yield f

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
    parser.add_argument('-f', '--force', default=False, action='store_true',
        help='Force the parsing to continue if a recoverable error is encountered')
    parser.add_argument('-b', '--activation-bytes',
        help='The activation bytes used to decrypt audible DRM. Automatic probe if not passed.')
    parser.add_argument('-v', '--verbose', default=0, action='count')
    parser.add_argument('file', nargs='+', action='extend',
        help='The file that we are going to convert')

    options = parser.parse_args(args)

    logger = get_logger(__name__, options.verbose)

    for file in file_generator(options.file):
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
            if logger.isEnabledFor(logging.DEBUG):
                logger.exception(e)
            else:
                logger.error(e)

if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1:])
