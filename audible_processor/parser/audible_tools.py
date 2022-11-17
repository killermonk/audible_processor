import json
import urllib.request
from dataclasses import dataclass
from logging import Logger
from urllib.error import HTTPError

# They added reCaptcha so this no longer works
BASE_URL = 'https://api.audible-converter.ml/api/v2/activation'

@dataclass
class AudibleTools:
    """Basic API interface to the Audible Tools"""
    logger: Logger

    def get_activation_bytes(self, checksum: str) -> str:
        url = '{}/{}'.format(BASE_URL, checksum)

        headers = {
            'User-Agent': 'AudiobookProcessor',
            'Origin': 'AudiobookProcessor',
        }

        self.logger.debug('Fetching activation bytes from {}'.format(url))
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                data = json.load(response)
                self.logger.debug('API Response: {}'.format(data))

                if data['success']:
                    bytes = data['activationBytes']
                    self.logger.debug('Activation Bytes: {}'.format(bytes))
                    return bytes
                else:
                    raise HTTPError(url, 500, "API failure", {}, None)
        except Exception as e:
            raise Exception('Failed to fetch activation bytes: {}'.format(str(e))) from e
