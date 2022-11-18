import audible
import os
import pathlib
from dataclasses import dataclass
from logging import Logger

AUTH_FILE = '.auth'


def _get_auth_locale() -> str:
    """Get the locale for the authenticator"""
    return os.getenv('LOCALE') or 'us'

@dataclass
class AudibleTools:
    """Class for handling audible interactions"""
    search_dir: str
    logger: Logger

    def _validate_search_dir(self) -> str:
        """Validate that the output dir is valid. Create the author/title dirs if required."""
        self.logger.info('Validating output directory %s', self.search_dir)
        search = pathlib.Path(self.search_dir)

        # validate base dir exists and is a directory and is writable
        self.logger.debug('Checking if \'{}\' exists'.format(search))
        if not search.is_dir():
            raise NotADirectoryError('\'{}\' is not a directory'.format(search))
        self.logger.debug('Checking if \'{}\' is writable'.format(search))
        if not os.access(search, os.W_OK):
            raise PermissionError('\'{}\' is not writable'.format(search))

    def auth_file_exists(self) -> bool:
        auth_file = os.path.join(self.search_dir, AUTH_FILE)
        return auth_file if os.path.exists(auth_file) else None

    def get_activation_bytes(self) -> str:
        """Get the activation bytes that we have stored"""
        ofile = os.path.join(self.search_dir, AUTH_FILE)
        if os.path.exists(ofile):
            with open(ofile, 'r') as f:
                return f.readline().strip()

        return None

    def get_activation_bytes_from_audible(self):
        """Login in to audible and get activation bytes"""
        self._validate_search_dir()

        auth = audible.Authenticator.from_login_external(locale = _get_auth_locale())
        bytes = auth.get_activation_bytes()

        ofile = os.path.join(self.search_dir, AUTH_FILE)
        with open(ofile, 'w') as f:
            f.write(bytes)

        auth.deregister_device()
