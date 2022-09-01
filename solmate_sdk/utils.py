"""Utilities for the other modules.
Methods included here should only depend on built-in and third party modules.
"""

import datetime
import json

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class BadRequest(Exception):
    """Exception that the server may throw when receiving invalid requests.
    The API Client will throw this exception when it receives such an error.
    """


class MoreCapableEncoder(json.JSONEncoder):
    """An extended JSONEncoder also capable of encoding datetime objects (using the DATETIME_FORMAT)."""

    def default(self, o):
        """Extends the method of the base class"""
        if isinstance(o, datetime.datetime):
            return o.strftime(DATETIME_FORMAT)
        return super().default(o)
