import ffmpeg
import logging
import os
import pathlib
from pathvalidate import sanitize_filepath
from dataclasses import dataclass
from logging import Logger
from typing import List

from src import AudibleTools


SUPPORTED_INPUT_TYPES = ['aax', 'aac', 'm4b']

class UnknownTypeException(Exception):
    """An exception to communicate that a file type is unknown"""
    def __init__(self, file: str, wanted: List[str]) -> None:
        super().__init__('\'{}\' does not have a known type ({})'.format(file, ', '.join(wanted)))

@dataclass
class ParserConfig:
    """Class for handling the config for a given parsing operation"""
    activation_bytes: str
    input_file: str
    output_dir: str
    create_author_dir: bool
    author_override: str
    create_title_dir: bool
    title_override: str
    force: bool

@dataclass
class Chapter:
    title: str
    start: str
    end: str

    @staticmethod
    def from_probe(probe):
        return Chapter(title=probe['tags']['title'], start=probe['start_time'], end=probe['end_time'])

@dataclass
class MetaData:
    author: str
    title: str
    activation_bytes: str
    chapters: list[Chapter]

def _get_file_ext(path):
    return pathlib.Path(path).suffix.lower().lstrip('.') # lowercase and strip leading '.'

def _get_file_name(path):
    return pathlib.Path(path).stem

@dataclass
class Parser:
    """Class for handling the parsing of an audiobook file"""
    config: ParserConfig
    logger: Logger
    audible: AudibleTools

    def run(self):
        self.logger.warning('Processing %s...', self.config.input_file)

        self._validate_activation_bytes()
        self._validate_input_file()
        meta = self._probe_meta()

        output_dir = self._validate_output_dir(meta)

        self._format_audio(meta, output_dir)

    def _validate_activation_bytes(self):
        activation_bytes = self.config.activation_bytes or self.audible.get_activation_bytes()
        if activation_bytes is None:
            raise Exception('Activation bytes not found')
        self.activation_bytes = [b.strip() for b in activation_bytes.split(',')]

    def _validate_input_file(self):
        """Validate that the input file is valid"""
        self.logger.info('Validating input file %s', self.config.input_file)
        input = pathlib.Path(self.config.input_file)

        # validate extension
        ext = _get_file_ext(self.config.input_file)
        self.logger.debug('Verifying input extension %s', ext)
        if not ext in SUPPORTED_INPUT_TYPES:
            raise UnknownTypeException(self.config.input_file, SUPPORTED_INPUT_TYPES)

        # validate it exists and is a file and is readable
        self.logger.debug('Checking if \'{}\' exists'.format(input))
        if not input.exists():
            raise FileNotFoundError('\'{}\' does not exist'.format(input))
        self.logger.debug('Checking if \'{}\' is a file'.format(input))
        if not input.is_file():
            raise FileNotFoundError('\'{}\' is not a file'.format(input))
        self.logger.debug('Checking if \'{}\' is readable'.format(input))
        if not os.access(input, os.R_OK):
            raise PermissionError('\'{}\' is not readable'.format(input))

    def _validate_output_dir(self, meta: MetaData) -> str:
        """Validate that the output dir is valid. Create the author/title dirs if required."""
        self.logger.info('Validating output directory %s', self.config.output_dir)
        output = pathlib.Path(self.config.output_dir)

        # validate base dir exists and is a directory and is writable
        self.logger.debug('Checking if \'{}\' exists'.format(output))
        if not output.is_dir():
            raise NotADirectoryError('\'{}\' is not a directory'.format(output))
        self.logger.debug('Checking if \'{}\' is writable'.format(output))
        if not os.access(output, os.W_OK):
            raise PermissionError('\'{}\' is not writable'.format(output))

        def join_path(dir: str) -> pathlib.Path:
            new_out = output.joinpath(sanitize_filepath(dir))
            # if it doesn't exist, create it
            self.logger.debug('Checking if \'{}\' exists'.format(new_out))
            if not new_out.exists():
                self.logger.debug('Creating nested output folder \'{}\''.format(new_out))
                os.mkdir(new_out)
            self.logger.debug('Checking if \'{}\' is writable'.format(new_out))
            if not os.access(new_out, os.W_OK):
                raise PermissionError('\'{}\' is not writable'.format(new_out))

            return new_out

        if self.config.create_author_dir:
            author = self.config.author_override or meta.author
            self.logger.debug('Using author \'{}\''.format(author))
            output = join_path(author)
        if self.config.create_title_dir:
            title = self.config.title_override or meta.title
            self.logger.debug('Using title \'{}\''.format(title))
            output = join_path(title)

        self.logger.info('Full output dir: \'{}\''.format(output))
        return str(output)

    def _probe_meta(self) -> MetaData:
        """Probe for the metadata of the file"""
        self.logger.info('Probing meta data')

        activation_bytes = None
        for _activation_bytes in self.activation_bytes:
            try:
                info = ffmpeg.probe(self.config.input_file, show_chapters=None, activation_bytes=_activation_bytes)

                format = (info['format']['tags']['major_brand'] or _get_file_ext(self.config.input_file)).strip()
                self.logger.debug('Probed format %s', format)

                title = info['format']['tags']['title'] or info['format']['tags']['album'] or _get_file_name(self.config.input_file)
                self.logger.debug('Probed title %s', title)

                author = info['format']['tags']['artist'] or info['format']['tags']['album_artist'] or 'Unknown'
                self.logger.debug('Probed author %s', author)

                raw_chapters = info['chapters'] or []
                chapters = [Chapter.from_probe(c) for c in raw_chapters]
                self.logger.debug('Probed %d chapters', len(chapters))

                # Success, exit with these bytes
                activation_bytes = _activation_bytes
                break
            except Exception as e:
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.exception(e)

                # Binaries not found
                if type(e) == FileNotFoundError:
                    raise Exception('Unable to probe for metadata. Please ensure ffmpeg and ffprobe are installed and on the path.') from e
                # ffmpeg error
                elif type(e) == ffmpeg.Error:
                    stderr = str(e.stderr).lower()
                    # Invalid Activation Bytes, try again
                    if 'mismatch in checksums' in stderr:
                        continue

                    raise Exception('Unable to probe for metadata. Error running ffprobe.') from e
                # Other Error
                else:
                    raise Exception('Unable to probe for metadata. Error running ffprobe.') from e

        if activation_bytes is None:
            raise Exception('Unable to find valid activation bytes for decoding file.')

        return MetaData(
            author=self.config.author_override or author,
            title=self.config.title_override or title,
            activation_bytes=activation_bytes,
            chapters=chapters,
        )

    def _format_audio(self, meta: MetaData, outdir: str):
        self.logger.warning('Saving mp3s to {}'.format(outdir))

        capture_output = False if self.logger.isEnabledFor(logging.DEBUG) else True

        self.logger.debug('Extracting cover art')
        (
            ffmpeg
                .input(self.config.input_file, y=None, activation_bytes=meta.activation_bytes)
                .output(os.path.join(outdir, 'cover.jpg'), an=None, vcodec='copy')
                .run(capture_stdout=capture_output, capture_stderr=capture_output)
        )

        # Run a parse command for each chapter
        num_chapters = len(meta.chapters)

        padding = 1
        t = num_chapters
        while t > 10:
            padding += 1
            t /= 10

        for num, chapter in enumerate(meta.chapters):
            track = num+1
            self.logger.warning('Processing chapter \'{}\' ({} of {})'.format(chapter.title, track, num_chapters))

            filename = '{} - {}.mp3'.format(str(track).rjust(padding, '0'), chapter.title)

            input_args = {
                'y': None,
                'activation_bytes': meta.activation_bytes
            }

            output_args = {
                'codec': 'libmp3lame',
                'vn': None,
                'ss': chapter.start,
                'to': chapter.end,
                'map_metadata': 0,
                'map_chapters': -1,
                'id3v2_version': 3,
                'metadata:g:0': 'title={}'.format(chapter.title),
                'metadata:g:1': 'track={}'.format(track),
                'metadata:g:2': 'album={}'.format(meta.title),
                'metadata:g:3': 'artist={}'.format(meta.author),
            }

            outfile = os.path.join(outdir, filename)
            self.logger.debug('Saving chapter to {}'.format(outfile))

            (
                ffmpeg
                    .input(self.config.input_file, **input_args)
                    .output(outfile, **output_args)
                    .run(capture_stdout=capture_output, capture_stderr=capture_output)
            )

        self.logger.warning('Done')
