"""Contains the high-level API client."""

import asyncio
from typing import Optional

import websockets.client

from .connection import SolConnection
from .utils import BadRequest


class SolMateAPIClient:
    """Class-based API Client for the Sol and SolMate Websocket API.

    Usage:

        ```python
        client = SolMateAPIClient("S1K0506...00X")
        client.connect()
        print(f"Current live values of your SolMate: {client.get_live_values()}")
        ```
    """

    def __init__(self, serialnum):
        """Initializes the instance given a serial number and auth_token (signature).
        Leaves the underlying connection object uninitialised.
        """
        self.conn: Optional[SolConnection] = None
        self.serialnum: str = serialnum

    async def _connect(self, auth_token, device_id="solmate-sdk"):
        """Asynchronously attempts to connect to the server and initialize the client."""
        sock = await websockets.client.connect("wss://sol.eet.energy:9124")
        self.conn = SolConnection(sock)
        try:
            await self.conn.request(
                "authenticate",
                {"serial_num": self.serialnum, "signature": auth_token, "device_id": device_id},
            )
        except BadRequest as err:
            raise ValueError("Invalid Serial Number?") from err

    def connect(self, auth_token, device_id="solmate-sdk"):
        """Synchronously attempts to connect to the server and initialize the client."""
        asyncio.run(self._connect(auth_token, device_id))

    def request(self, route, data):
        """Synchronous method to make requests to the API."""
        if self.conn is None:
            raise RuntimeError("Connection has not yet been initialised.")
        return asyncio.run(self.conn.request(route, data))

    def get_live_values(self):
        """Return current live values of the respective SolMate as a dictionary (pv power, battery state, injection)."""
        return self.request("live_values", {})

    def check_online(self):
        """Check whether the respective SolMate is currently online."""
        return self.request("check_online", {"serial_num": self.serialnum})["online"]

    def close(self):
        """Correctly close the underlying connection."""
        if self.conn is None:
            raise RuntimeError("Connection has not yet been initialised.")
        asyncio.run(self.conn.close())
