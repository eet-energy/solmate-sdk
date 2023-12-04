"""Contains the high-level asynchronous API client."""

import base64
import getpass
import hashlib
import json
import pathlib
from typing import Optional

import websockets.client

from .connection import SolConnection
from .utils import BadRequest, ConnectionClosedOnPurpose, bad_request_handling

CONFIG_DIRECTORY = pathlib.Path.home() / ".config" / "solmate-sdk"
AUTHSTORE_FILE = CONFIG_DIRECTORY / "authstore.json"
DEFAULT_DEVICE_ID = "solmate-sdk"
LOCAL_AUTHSTORE_FILE = CONFIG_DIRECTORY / "local_authstore.json"
LOCAL_ACCESS_DEVICE_ID = "local_webinterface"
SOL_URI = "wss://sol.eet.energy:9124"


class SolMateAPIClient:
    """Class-based API Client for the Sol and SolMate Websocket API.
    This client provides asynchronous endpoint methods.

    Simple Usage:

        ```python
        client = SolMateAPIClient("S1K0506...00X")
        await client.quickstart()
        print(f"Current live values of your SolMate: {await client.get_live_values()}")
        ```
    Note when using LocalSolMateAPIClient instead of SolMateAPIClient, you need to add the local
    hostname of the Solmate which you get from your local DHCP. Use the hostname and not the IP address,
    else local and server access cant be distinguished. The hostname will most likely start with 'sun2plug'.
    
        client = LocalSolMateAPIClient("S1K0506...00X", "ws://<your-local-solmate-hostname:9124")
    """

    def __init__(self, serialnum: str, uri=SOL_URI):
        """Initializes the instance given a serial number and auth_token (signature).
        Leaves the underlying connection object uninitialised.
        """
        self.serialnum: str = serialnum
        self.conn: Optional[SolConnection] = None
        self.authenticated: bool = False
        self.uri_verified: bool = False
        self.uri = uri
        self.device_id = DEFAULT_DEVICE_ID
        self.authstore_file = AUTHSTORE_FILE

    async def connect(self):
        """Attempts to connect to the server and initialize the client."""
        sock = await websockets.client.connect(self.uri)
        self.conn = SolConnection(sock)

    async def _request(self, route, data):
        """Method to make requests to the API."""
        if self.conn is None:
            raise RuntimeError("Connection has not yet been initialised.")
        return await self.conn.request(route, data)

    async def login(self, user_password, device_id=DEFAULT_DEVICE_ID) -> str:
        """Method to generate the authentication token from the serialnumber + password."""
        try:
            response = await self._request(
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

    async def check_uri(self, auth_token, device_id):
        """Handles redirections using verification of uri and dummy request gaining redirection info"""
        if not self.uri_verified:
            print("Verifiying uri")
            try:
                data = await self._request(
                    "authenticate",
                    {
                        "serial_num": self.serialnum,
                        "signature": auth_token,
                        "device_id": device_id,
                    },
                )
                print(data)
                if not data["redirect"] in (self.uri, None):
                    print("Redirected - switching to new uri - uri of SolMate changed retry whatever you have done")
                    self.uri = data["redirect"]
                    print("New uri", self.uri)
                    self.uri_verified = True
                else:
                    self.uri_verified = True
            except BadRequest as err:
                raise ValueError("Invalid Serial Number?") from err

    async def authenticate(self, auth_token, device_id=DEFAULT_DEVICE_ID):
        """Given the authentication token, try to authenticate this websocket connection.
        Subsequent method calls to protected methods are unlocked this way.
        """
        try:
            await self._request(
                "authenticate",
                {
                    "serial_num": self.serialnum,
                    "signature": auth_token,
                    "device_id": device_id,
                },
            )
        except BadRequest as err:
            raise ValueError("Invalid Serial Number?") from err

    async def quickstart(self, password=None, device_id=DEFAULT_DEVICE_ID):
        """Connect, login, authenticate and store the token for future use!"""
        await self.connect()
        token: Optional[str] = None
        if self.authstore_file.exists():
            with open(self.authstore_file, encoding="utf-8") as file:
                authstore = json.load(file)
            if self.serialnum in authstore:
                token = authstore[self.serialnum]
        else:
            authstore = {}
        if token is None:
            print(f"Please enter the user password of your SolMate {self.serialnum}.")
            print(f"The credentials will then be stored for future use in {self.authstore_file}! :)")
            password = getpass.getpass("Your SolMate's user password: ")
            token = await self.login(password, device_id)
            CONFIG_DIRECTORY.mkdir(exist_ok=True)
            with open(self.authstore_file, "w", encoding="utf-8") as file:
                authstore[self.serialnum] = token
                json.dump(authstore, file)
            print(f"Stored credentials of {self.serialnum}.")
            print(f"Already stored credentials are: ", [sn for sn in authstore.keys()])
        if not self.uri_verified:
            print("uri nor verified yet - checking uri for redirection - SolMate might be on a different port")
            await self.check_uri(token, device_id)
            await self.connect()  # Connect to redirection address
        await self.authenticate(token, device_id)

    @bad_request_handling()
    async def get_software_version(self):
        """Returns the actually installed software version"""
        return await self._request("get_solmate_info", {})

    @bad_request_handling()
    async def get_live_values(self):
        """Return current live values of the respective SolMate as a dictionary (pv power, battery state, injection)."""
        return await self._request("live_values", {})

    @bad_request_handling()
    async def get_recent_logs(self, days=None, start_time=None):
        """Returns the latest logs on the sol server"""
        import datetime
        if not days:
            days = 1
        if not start_time:
            start_time = datetime.datetime.now() - datetime.timedelta(days)
        end_time = start_time + datetime.timedelta(days)
        return await self._request("logs", {
            "timeframes": [
                {"start": start_time.isoformat()[:19],
                 "end": end_time.isoformat()[:19],
                 "resolution": 4}
            ]})

    @bad_request_handling()
    async def get_milestones_savings(self, days=1):
        """Returns the latest milestones saving"""
        return await self._request("milestones_savings", {"days":days})

    @bad_request_handling()
    async def get_user_settings(self):
        """Returns user settings which are valid at the moment"""
        return await self._request("get_user_settings", {})

    @bad_request_handling()
    async def get_injection_settings(self):
        """Shows your injection settings."""
        return await self._request("get_injection_settings", {})

    @bad_request_handling()
    async def get_grid_mode(self):
        """Returns grid mode i.e. Offgrid mode ('island mode') or Ongrid mode"""
        return await self._request("get_grid_mode", {})

    @bad_request_handling()
    async def check_online(self):
        """Check whether the respective SolMate is currently online."""
        return await self._request("check_online", {"serial_num": self.serialnum})["online"]

    @bad_request_handling()
    async def set_max_injection(self, maximum_power):
        """Sets user defined maximum injection power which is applied if SolMates battery is ok with it"""
        return await self._request("set_user_maximum_injection", {"injection": maximum_power})

    @bad_request_handling()
    async def set_min_injection(self, minimum_power):
        """Sets user defined minimum injection power which is applied if SolMates battery is ok with it"""
        return await self._request("set_user_minimum_injection", {"injection": minimum_power})

    @bad_request_handling()
    async def set_min_battery_percentage(self, minimum_percentage):
        """Sets user defined minimum battery percentage"""
        return await self._request("set_user_minimum_battery_percentage", {"battery_percentage": minimum_percentage})

    @bad_request_handling()
    async def set_AP_mode(self):
        """This function opens the local Access Point (AP) of SolMate and leaves client (CLI) mode. This means you will
        have to connect to your SolMates WIFI "SolMate <serialnumber>". However, if SolMate has a wired connection as
        well online availability remains"""
        return await self._request("revert_to_ap", {})

    async def close(self):
        """Correctly close the underlying connection."""
        if self.conn is None:
            raise RuntimeError("Connection has not yet been initialised.")
        await self.conn.close()


class LocalSolMateAPIClient(SolMateAPIClient):
    """Like SolMateAPIClient, however in local mode some extra routes are available

    In the local mode there is no load_balancer between you and your SolMate - though self.uri_verified needs to be set

    Furthermore, it is necessary to authenticate again using a special device_id. You may need to clear your authstore
    file (if you tested the online API first)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_id = LOCAL_ACCESS_DEVICE_ID
        self.uri_verified = True  # on local access no redirection is possible and the test for it is misunderstood
        self.authstore_file = LOCAL_AUTHSTORE_FILE

    @bad_request_handling()
    async def list_wifis(self):
        """Lists actually available and non hidden SSIDs"""
        return await self._request("list_wifis", {})

    @bad_request_handling()
    async def connect_to_wifi(self, ssid, password):
        """Switches to other ssid or to the same - THE ACTUAL CONNECTION WILL BE BROKEN AFTER THAT
         A TimeOutError will be raised rather than the ConnectionClosedOnPurpose error"""
        await self._request("connect_to_wifi", {"ssid": ssid, "password": password})
        raise ConnectionClosedOnPurpose

    async def check_online(self):
        """Check whether the respective SolMate is currently online.
        The local api has no check_online route, it is online if you can connect to the local uri.
        Please call connect() or quickstart(...) before."""
        return self.conn != None
