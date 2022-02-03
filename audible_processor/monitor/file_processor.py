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

STATE_FILE = 'processor.ini'

class FileStatus(Enum):
    DISCOVERED = 1
    ERROR = 2
    PROCESSED = 5

@contextmanager
def atomic_lock(lock: mp.Lock):
    lock.acquire()
    try:
        yield
    finally:
        lock.release()

def _load_state() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(STATE_FILE)
    return config

def _get_state(path: str) -> Dict[str, Any]:
    state = _load_state()
    abs_path = os.path.abspath(path)
    return state[abs_path] if state.has_section(abs_path) else {}

def _update_state(lock: mp.Lock, path: str, **kwargs):
    abs_path = os.path.abspath(path)
    with atomic_lock(lock):
        state = _load_state()
        if state.has_section(abs_path):
            state[abs_path] = { **state[abs_path], **kwargs }
        else:
            state[abs_path] = kwargs
        _save_state(state)

def _save_state(state: configparser.ConfigParser):
    with open(STATE_FILE, 'w') as file:
        state.write(file)

def file_processor(config: DaemonConfig, queue: mp.Queue, lock: mp.Lock):
    print('creating logger')
    logger = logging.getLogger('monitor:file_processor')
    logger.setLevel(logging.DEBUG)

    def should_process_file(file: str) -> bool:
        """Determine if we should process the given file"""
        # Check if file has already been processed
        state = _get_state(file)
        return False if state.get('status', None) == FileStatus.PROCESSED else True

    def process_file(file: str):
        logger.debug('Updating state to discovered for \'{}\''.format(file))
        _update_state(lock, file, status=FileStatus.DISCOVERED, last_updated=datetime.now())

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
            # Parser(parser_config, logger).run()
            raise Exception("cannot process")
            _update_state(lock, file, status=FileStatus.PROCESSED, last_updated=datetime.now())
        except Exception as e:
            logger.error(e)
            _update_state(lock, file, status=FileStatus.ERROR, last_updated=datetime.now())

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

