import configparser
import logging
import multiprocessing as mp
import os.path
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from parser.parser import Parser, ParserConfig
from queue import Empty
from typing import Any, Dict

from monitor.config import DaemonConfig

STATE_FILE = '.books.ini'

class FileStatus(Enum):
    DISCOVERED = 1
    ERROR = 2
    PROCESSED = 5

class LogPrefixAdapter(logging.LoggerAdapter):
    def __init__(self, prefix: str, logger: logging.Logger, extra=None):
        self._prefix = prefix
        super().__init__(logger, extra)

    def process(self, msg, kwargs):
        return '{}{}'.format(self._prefix, msg), kwargs

@contextmanager
def atomic_lock(lock: mp.Lock):
    lock.acquire()
    try:
        yield
    finally:
        lock.release()

def str_truncate(s: str, to_len: int, suffix: str = '...'):
    return s if len(s) <= to_len + len(suffix) else '{}{}'.format(s[:to_len], suffix)

class StateManager:
    lock: mp.Lock
    _path: str

    def __init__(self, output_dir: str, lock: mp.Lock) -> None:
        self.lock = lock
        self._path = os.path.join(output_dir, STATE_FILE)

    def _load_state(self):
        config = configparser.ConfigParser()
        config.read(self._path)
        return config

    def _save_state(self, state: configparser.ConfigParser):
        with open(self._path, 'w') as file:
            state.write(file)

    def get_state(self, path: str) -> Dict[str, Any]:
        state = self._load_state()
        abs_path = os.path.abspath(path)
        return state[abs_path] if state.has_section(abs_path) else {}

    def update_state(self, path: str, **kwargs):
        abs_path = os.path.abspath(path)
        with atomic_lock(self.lock):
            state = self._load_state()
            if state.has_section(abs_path):
                state[abs_path] = { **state[abs_path], **kwargs }
            else:
                state[abs_path] = kwargs
            self._save_state(state)

def file_processor(config: DaemonConfig, queue: mp.Queue, lock: mp.Lock, log_level: int = logging.DEBUG):
    logger = logging.getLogger('monitor:file_processor')
    logger.setLevel(log_level)

    manager = StateManager(config.output_dir, lock)

    def should_process_file(file: str) -> bool:
        """Determine if we should process the given file"""
        state = manager.get_state(file)
        return False if state.get('status', None) == str(FileStatus.PROCESSED) else True

    def process_file(file: str):
        """Do the work to initialize and run the Processor"""
        logger.debug('Updating state to discovered for \'{}\''.format(file))
        manager.update_state(file, status=FileStatus.DISCOVERED, start_date=datetime.now())

        # Make a new logger to use for this processor
        basename = os.path.basename(file)
        prefix = str_truncate(basename, 10)
        sub_logger = LogPrefixAdapter('{}-'.format(prefix), logger)

        parser_config = ParserConfig(
            input_file=file,
            output_dir=config.output_dir,
            activation_bytes=config.activation_bytes,
            create_author_dir=config.create_author_dir,
            author_override='',
            create_title_dir=config.create_title_dir,
            title_override='',
            force=True,
        )

        try:
            Parser(config=parser_config, logger=sub_logger).run()
            manager.update_state(file, status=FileStatus.PROCESSED, end_date=datetime.now())
        except Exception as e:
            logger.error(e)
            manager.update_state(file, status=FileStatus.ERROR, end_date=datetime.now())

    """Worker function to process a file"""
    try:
        while True:
            try:
                to_process = queue.get(timeout=0.25)
                logger.debug('Received file \'{}\''.format(to_process))
            except Empty:
                continue # short polls

            if should_process_file(to_process):
                logger.debug('Sending \'{}\' for processing'.format(to_process))
                process_file(to_process)
            else:
                logger.debug('Skipping \'{}\'. Already processed.'.format(to_process))
    except KeyboardInterrupt:
        logger.debug('Stopping file processor')

