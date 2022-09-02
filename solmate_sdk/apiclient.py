"""Contains the high-level API client."""

import asyncio
import base64
import getpass
import hashlib
import json
import pathlib
from typing import Optional

import websockets.client

from .connection import SolConnection
from .utils import BadRequest

CONFIG_DIRECTORY = pathlib.Path.home() / ".config" / "solmate-sdk"
AUTHSTORE_FILE = CONFIG_DIRECTORY / "authstore.json"
DEFAULT_DEVICE_ID = "solmate-sdk"


class SolMateAPIClient:
    """Class-based API Client for the Sol and SolMate Websocket API.
    This client provides synchronous endpoint methods on top of the asynchronous ones (actually used in the background).

    Simple Usage:

        ```python
        client = SolMateAPIClient("S1K0506...00X")
        client.quickstart()
        print(f"Current live values of your SolMate: {client.get_live_values()}")
        ```
    """

    def __init__(self, serialnum: str):
        """Initializes the instance given a serial number and auth_token (signature).
        Leaves the underlying connection object uninitialised.
        """
        self.serialnum: str = serialnum
        self.conn: Optional[SolConnection] = None
        self.authenticated: bool = False

    async def _connect(self):
        """Asynchronously attempts to connect to the server and initialize the client."""
        sock = await websockets.client.connect("wss://sol.eet.energy:9124")
        self.conn = SolConnection(sock)

    def connect(self):
        """Synchronously attempts to connect to the server and initialize the client."""
        asyncio.get_event_loop().run_until_complete(self._connect())

    def request(self, route, data):
        """Synchronous method to make requests to the API."""
        if self.conn is None:
            raise RuntimeError("Connection has not yet been initialised.")
        return asyncio.get_event_loop().run_until_complete(self.conn.request(route, data))

    def login(self, user_password, device_id=DEFAULT_DEVICE_ID) -> str:
        """Generates the authentication token from the serialnumber + password."""
        try:
            response = self.request(
                "login",
                {
                    "serial_num": self.serialnum,
                    "user_password_hash": base64.encodebytes(
                        hashlib.sha256(user_password.encode()).digest()
                    ).decode(),  # the stage-1 hash of the user password
                    "device_id": device_id,
                },
            )
        except BadRequest as err:
            raise err
        if not response["success"]:
            raise RuntimeError("Unauthenticated :(")
        return response["signature"]

    def authenticate(self, auth_token, device_id=DEFAULT_DEVICE_ID):
        """Given the authentication token, try to authenticate this websocket connection.
        Subsequent method calls to protected methods are unlocked this way.
        """
        try:
            self.request(
                "authenticate",
                {
                    "serial_num": self.serialnum,
                    "signature": auth_token,
                    "device_id": device_id,
                },
            )
        except BadRequest as err:
            raise ValueError("Invalid Serial Number?") from err

    def quickstart(self, password=None, device_id=DEFAULT_DEVICE_ID):
        """Connect, login, authenticate and store the token for future use!"""
        self.connect()
        token: Optional[str] = None
        if AUTHSTORE_FILE.exists():
            with open(AUTHSTORE_FILE, encoding="utf-8") as file:
                authstore = json.load(file)
            if self.serialnum in authstore:
                token = authstore[self.serialnum]
        else: 
            authstore = {}
        if token is None:
            print(f"Please enter the user password of your SolMate {self.serialnum}.")
            print(f"The credentials will then be stored for future use in {AUTHSTORE_FILE}! :)")
            password = getpass.getpass("Your SolMate's user password: ")
            token = self.login(password, device_id)
            CONFIG_DIRECTORY.mkdir(exist_ok=True)
            with open(AUTHSTORE_FILE, "w", encoding="utf-8") as file:
                authstore[self.serialnum] = token
                json.dump(authstore, file)
            print(f"Stored credentials of {self.serialnum}.")
            print(f"Already stored credentials are: ", [sn for sn in authstore.keys()])
        self.authenticate(token, device_id)

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
        asyncio.get_event_loop().run_until_complete(self.conn.close())
