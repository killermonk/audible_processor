import multiprocessing as mp
import os.path
import time
from logging import Logger
from os import walk
from typing import List

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer

from monitor.config import DaemonConfig
from monitor.file_processor import file_processor

class ProcessPool:
    """Helper class to start multiple processes"""
    _pool: List[mp.Process]

    def __init__(self, size, target=None, name=None, daemon=None, args=(), kwargs={}) -> None:
        self._pool = [mp.Process(target=target, name=name, daemon=daemon, args=args, kwargs=kwargs) for _ in range(size)]

    def start(self):
        for p in self._pool: p.start()

    def close(self):
        for p in self._pool: p.close()

    def terminate(self):
        for p in self._pool: p.terminate()

    def join(self):
        for p in self._pool: p.join()

    def is_alive(self):
        return all(p.is_alive() for p in self._pool)

class Daemon:
    """Class to monitor a directory and parse any files in it"""
    config: DaemonConfig
    logger: Logger

    _queue: mp.Queue

    def __init__(self, config: DaemonConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger

        self._queue = mp.Queue()

    def run(self, path: str):
        observer = processor = None

        try:
            observer = self._start_file_observer(path)
            processor = self._start_file_processor()

            # Loop through existing files in the path and add them to the queue
            self._queue_existing_files(path)

            while True:
                time.sleep(1)

                # If either process has die, terminate
                if not observer.is_alive() or not processor.is_alive():
                    break
        except KeyboardInterrupt:
            self.logger.info('stopping')
        finally:
            # Kill sub processes and wait until they stop
            if observer and observer.is_alive():
                observer.stop()
                observer.join()

            if processor and processor.is_alive():
                processor.terminate()
                processor.join()
                processor.close()

    def _get_on_create_handler(self):
        def on_create(event):
            self.logger.info('monitoring \'{}\' for steady state'.format(event.src_path))

            new_size = os.path.getsize(event.src_path)
            while True:
                old_size = new_size
                time.sleep(5)
                new_size = os.path.getsize(event.src_path)

                if old_size == new_size:
                    self.logger.info('monitoring \'{}\' finished'.format(event.src_path))
                    break

            self._queue.put(event.src_path)

        return on_create

    def _start_file_observer(self, path: str) -> Observer:
        event_handler = RegexMatchingEventHandler(
            regexes=['^.*\.aax$'],
            ignore_regexes=[],
            ignore_directories=True,
            case_sensitive=False,
        )

        event_handler.on_created = self._get_on_create_handler()

        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)

        self.logger.info('watching \'{}\''.format(path))
        observer.start()

        return observer

    def _start_file_processor(self) -> ProcessPool:
        self.logger.info('Starting file processor')

        lock = mp.Lock()
        pool = ProcessPool(
            self.config.threads,
            target=file_processor,
            args=(self.config, self._queue, lock, self.logger.level))

        pool.start()
        return pool

    def _queue_existing_files(self, path: str):
        for (dirpath, _, filenames) in walk(path):
            for file in filenames:
                if len(file) > 4 and file[-4:].lower() == '.aax':
                    self._queue.put(os.path.join(dirpath, file))
