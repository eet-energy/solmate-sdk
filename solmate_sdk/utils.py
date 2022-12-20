"""Utilities for the other modules.
Methods included here should only depend on built-in and third party modules.
"""

import datetime
import functools
import json
import time
from websockets import ConnectionClosed

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def bad_request_handling():
    """A decorator that deals with BadRequest exceptions"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = 1
            r = 0
            num_retries = 2
            while True:
                try:
                    return func(*args, **kwargs)
                except BadRequest as exc:
                    r += 1
                    if delay:
                        time.sleep(delay)
                    if r >= num_retries:
                        print("This route is not supported on this SolMate yet")
                        break
        return wrapper
    return decorator


def retry(num_retries, exception_type, delay=0.0):
    """A decorator that retries a function num_retries times"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exception_type as exc:
                    r += 1
                    if delay:
                        time.sleep(delay)
                    if r >= num_retries:
                        raise exc

        return wrapper

    return decorator


class BadRequest(Exception):
    """Exception that the server may throw when receiving invalid requests.
    The API Client will throw this exception when it receives such an error.
    """


class ConnectionClosedOnPurpose(ConnectionClosed):
    """Exception to be thrown on purpose i.e. during switching of wlan routers"""


class MoreCapableEncoder(json.JSONEncoder):
    """An extended JSONEncoder also capable of encoding datetime objects (using the DATETIME_FORMAT)."""

    def default(self, o):
        """Extends the method of the base class"""
        if isinstance(o, datetime.datetime):
            return o.strftime(DATETIME_FORMAT)
        return super().default(o)
