import multiprocessing as mp
import os.path
import time
from logging import Logger
from os import walk
from typing import List

from watchdog.events import RegexMatchingEventHandler, LoggingEventHandler
from watchdog.observers import Observer

from src import AudibleTools
from .config import DaemonConfig
from .file_processor import file_processor


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

class AudibleFileWatcher(RegexMatchingEventHandler):
    def __init__(self, queue: mp.Queue, logger: Logger) -> None:
        super().__init__(regexes=['^.*\.aax$'], ignore_regexes=[], ignore_directories=True, case_sensitive=False)

        self.queue = queue
        self.logger = logger

    def on_create(self, event):
        self.logger.info('monitoring \'{}\' for steady state'.format(event.src_path))

        new_size = os.path.getsize(event.src_path)
        while True:
            old_size = new_size
            time.sleep(5)
            new_size = os.path.getsize(event.src_path)

            if old_size == new_size:
                self.logger.info('monitoring \'{}\' finished'.format(event.src_path))
                break

        self.queue.put(event.src_path)


class Daemon:
    """Class to monitor a directory and parse any files in it"""
    config: DaemonConfig
    audible: AudibleTools
    logger: Logger

    _queue: mp.Queue

    def __init__(self, config: DaemonConfig, audible: AudibleTools, logger: Logger) -> None:
        self.config = config
        self.audible = audible
        self.logger = logger

        self._queue = mp.Queue()

    def run(self, path: str):
        observer = processor = None

        # Wait until an auth file exists before attempt to start
        self._wait_for_auth()

        try:
            observer = self._start_file_observer(path)
            processor = self._start_file_processor()

            # Loop through existing files in the path and add them to the queue
            self._queue_existing_files(path)

            while True:
                time.sleep(1)

                # If either process has died, terminate
                if not observer.is_alive() or not processor.is_alive():
                    self.logger.info('Observer or processor died, stopping')
                    break
        except KeyboardInterrupt:
            self.logger.info('stopping')
        finally:
            self.logger.info('shutting down')
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

    def _wait_for_auth(self):
        if not self.config.activation_bytes:
            self.logger.debug('Validating auth exists')
            try:
                first = True
                while self.audible.auth_file_exists() == None:
                    if first:
                        self.logger.warning('Waiting for auth file to be created')
                        first = False
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.warning('stopping')
                raise

    def _start_file_observer(self, path: str) -> Observer:
        # event_handler = RegexMatchingEventHandler(
        #     regexes=['^.*\.aax$'],
        #     ignore_regexes=[],
        #     ignore_directories=True,
        #     case_sensitive=False,
        # )

        # event_handler.on_created = self._get_on_create_handler()

        observer = Observer()
        observer.schedule(LoggingEventHandler(self.logger), path, recursive=True)
        # observer.schedule(event_handler, path, recursive=True)
        # observer.schedule(AudibleFileWatcher(self._queue, self.logger), path, recursive=True)

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
