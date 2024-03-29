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
    """Async base class for the API client.
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

    async def _async_connect(self):
        """Attempts to connect to the server and initialize the client."""
        if self.conn is not None:
            await self.conn.close()
        
        sock = await websockets.client.connect(self.uri)
        self.conn = SolConnection(sock)

    async def _async_request(self, route, data):
        """Method to make requests to the API."""
        if self.conn is None:
            raise RuntimeError("Connection has not yet been initialised.")
        return await self.conn.request(route, data)

    async def _async_login(self, user_password, device_id=DEFAULT_DEVICE_ID) -> str:
        """Method to generate the authentication token from the serialnumber + password."""
        try:
            response = await self._async_request(
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

    async def _async_check_uri(self, auth_token, device_id):
        """Handles redirections using verification of uri and dummy request gaining redirection info"""
        if not self.uri_verified:
            print("Verifiying uri")
            try:
                data = await self._async_request(
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

    async def _async_authenticate(self, auth_token, device_id=DEFAULT_DEVICE_ID):
        """Given the authentication token, try to authenticate this websocket connection.
        Subsequent method calls to protected methods are unlocked this way.
        """
        try:
            await self._async_request(
                "authenticate",
                {
                    "serial_num": self.serialnum,
                    "signature": auth_token,
                    "device_id": device_id,
                },
            )
        except BadRequest as err:
            raise ValueError("Invalid Serial Number?") from err

    async def _async_quickstart(self, password=None, device_id=DEFAULT_DEVICE_ID):
        """Connect, login, authenticate and store the token for future use!"""
        await self._async_connect()
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
            if password == None:
                password = getpass.getpass("Your SolMate's user password: ")
            token = await self._async_login(password, device_id)
            CONFIG_DIRECTORY.mkdir(exist_ok=True)
            with open(self.authstore_file, "w", encoding="utf-8") as file:
                authstore[self.serialnum] = token
                json.dump(authstore, file)
            print(f"Stored credentials of {self.serialnum}.")
            print(f"Already stored credentials are: ", [sn for sn in authstore.keys()])
        if not self.uri_verified:
            print("uri nor verified yet - checking uri for redirection - SolMate might be on a different port")
            await self._async_check_uri(token, device_id)
            await self._async_connect()  # Connect to redirection address
        await self._async_authenticate(token, device_id)

    @bad_request_handling()
    async def _async_get_software_version(self):
        """Returns the actually installed software version"""
        return await self._async_request("get_solmate_info", {})

    @bad_request_handling()
    async def _async_get_live_values(self):
        """Return current live values of the respective SolMate as a dictionary (pv power, battery state, injection)."""
        return await self._async_request("live_values", {})

    @bad_request_handling()
    async def _async_get_recent_logs(self, days=None, start_time=None):
        """Returns the latest logs on the sol server"""
        import datetime
        if not days:
            days = 1
        if not start_time:
            start_time = datetime.datetime.now() - datetime.timedelta(days)
        end_time = start_time + datetime.timedelta(days)
        return await self._async_request("logs", {
            "timeframes": [
                {"start": start_time.isoformat()[:19],
                 "end": end_time.isoformat()[:19],
                 "resolution": 4}
            ]})

    @bad_request_handling()
    async def _async_get_milestones_savings(self, days=1):
        """Returns the latest milestones saving"""
        return await self._async_request("milestones_savings", {"days":days})

    @bad_request_handling()
    async def _async_get_user_settings(self):
        """Returns user settings which are valid at the moment"""
        return await self._async_request("get_user_settings", {})

    @bad_request_handling()
    async def _async_get_injection_settings(self):
        """Shows your injection settings."""
        return await self._async_request("get_injection_settings", {})

    @bad_request_handling()
    async def _async_get_grid_mode(self):
        """Returns grid mode i.e. Offgrid mode ('island mode') or Ongrid mode"""
        return await self._async_request("get_grid_mode", {})

    @bad_request_handling()
    async def _async_check_online(self):
        """Check whether the respective SolMate is currently online."""
        return (await self._async_request("check_online", {"serial_num": self.serialnum}))["online"]

    @bad_request_handling()
    async def _async_set_max_injection(self, maximum_power):
        """Sets user defined maximum injection power which is applied if SolMates battery is ok with it"""
        return await self._async_request("set_user_maximum_injection", {"injection": maximum_power})

    @bad_request_handling()
    async def _async_set_min_injection(self, minimum_power):
        """Sets user defined minimum injection power which is applied if SolMates battery is ok with it"""
        return await self._async_request("set_user_minimum_injection", {"injection": minimum_power})

    @bad_request_handling()
    async def _async_set_min_battery_percentage(self, minimum_percentage):
        """Sets user defined minimum battery percentage"""
        return await self._async_request("set_user_minimum_battery_percentage", {"battery_percentage": minimum_percentage})

    @bad_request_handling()
    async def _async_set_AP_mode(self):
        """This function opens the local Access Point (AP) of SolMate and leaves client (CLI) mode. This means you will
        have to connect to your SolMates WIFI "SolMate <serialnumber>". However, if SolMate has a wired connection as
        well online availability remains"""
        return await self._async_request("revert_to_ap", {})

    async def _async_close(self):
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
    def __init__(self, serialnum: str, uri=SOL_URI):
        super().__init__(serialnum, uri)
        self.device_id = LOCAL_ACCESS_DEVICE_ID
        self.uri_verified = True  # on local access no redirection is possible and the test for it is misunderstood
        self.authstore_file = LOCAL_AUTHSTORE_FILE

    @bad_request_handling()
    async def _async_list_wifis(self):
        """Lists actually available and non hidden SSIDs"""
        return await self._async_request("list_wifis", {})

    @bad_request_handling()
    async def _async_connect_to_wifi(self, ssid, password):
        """Switches to other ssid or to the same - THE ACTUAL CONNECTION WILL BE BROKEN AFTER THAT
         A TimeOutError will be raised rather than the ConnectionClosedOnPurpose error"""
        await self._async_request("connect_to_wifi", {"ssid": ssid, "password": password})
        raise ConnectionClosedOnPurpose

    async def _async_check_online(self):
        """Check whether the respective SolMate is currently online.
        The local api has no check_online route, it is online if you can connect to the local uri.
        Please call connect() or quickstart(...) before."""
        return self.conn != None
