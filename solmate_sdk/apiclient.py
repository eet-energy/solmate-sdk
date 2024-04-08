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
from .utils import BadRequest, ConnectionClosedOnPurpose, bad_request_handling, retry

CONFIG_DIRECTORY = pathlib.Path.home() / ".config" / "solmate-sdk"
AUTHSTORE_FILE = CONFIG_DIRECTORY / "authstore.json"
DEFAULT_DEVICE_ID = "solmate-sdk"
LOCAL_AUTHSTORE_FILE = CONFIG_DIRECTORY / "local_authstore.json"
LOCAL_ACCESS_DEVICE_ID = "local_webinterface"
SOL_URI = "wss://sol.eet.energy:9124"


class SolMateAPIClient:
    """Class-based API Client for the Sol and SolMate Websocket API.
    This client provides synchronous endpoint methods on top of the asynchronous ones (actually used in the background).

    Simple Usage:

        ```python
        client = SolMateAPIClient("S1K0506...00X")
        client.quickstart()
        print(f"Current live values of your SolMate: {client.get_live_values()}")
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

    async def _connect(self):
        """Asynchronously attempts to connect to the server and initialize the client."""
        if self.conn is not None:
            await self.conn.close()

        sock = await websockets.client.connect(self.uri)
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

    def check_uri(self, auth_token, device_id):
        """Handles redirections using verification of uri and dummy request gaining redirection info"""
        if not self.uri_verified:
            print("Verifiying uri")
            try:
                data = self.request(
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
            token = self.login(password, device_id)
            CONFIG_DIRECTORY.mkdir(parents=True, exist_ok=True)
            with open(self.authstore_file, "w", encoding="utf-8") as file:
                authstore[self.serialnum] = token
                json.dump(authstore, file)
            print(f"Stored credentials of {self.serialnum}.")
            print(f"Already stored credentials are: ", [sn for sn in authstore.keys()])
        if not self.uri_verified:
            print("uri nor verified yet - checking uri for redirection - SolMate might be on a different port")
            self.check_uri(token, device_id)
            self.connect()  # Connect to redirection address
        self.authenticate(token, device_id)

    @bad_request_handling()
    def get_software_version(self):
        """Returns the actually installed software version"""
        return self.request("get_solmate_info", {})

    @retry(2, BadRequest, 1)
    def get_live_values(self):
        """Return current live values of the respective SolMate as a dictionary (pv power, battery state, injection)."""
        return self.request("live_values", {})

    def get_recent_logs(self, days=None, start_time=None):
        """Returns the latest logs on the sol server"""
        import datetime

        if not days:
            days = 1
        if not start_time:
            start_time = datetime.datetime.now() - datetime.timedelta(days)
        end_time = start_time + datetime.timedelta(days)
        return self.request(
            "logs",
            {"timeframes": [{"start": start_time.isoformat()[:19], "end": end_time.isoformat()[:19], "resolution": 4}]},
        )

    def get_milestones_savings(self, days=1):
        """Returns the latest milestones saving"""
        return self.request("milestones_savings", {"days": days})

    def get_user_settings(self):
        """Returns user settings which are valid at the moment"""
        return self.request("get_user_settings", {})

    def get_injection_settings(self):
        """Shows your injection settings."""
        return self.request("get_injection_settings", {})

    def get_grid_mode(self):
        """Returns grid mode i.e. Offgrid mode ('island mode') or Ongrid mode"""
        return self.request("get_grid_mode", {})

    def check_online(self):
        """Check whether the respective SolMate is currently online."""
        return self.request("check_online", {"serial_num": self.serialnum})["online"]

    def set_max_injection(self, maximum_power):
        """Sets user defined maximum injection power which is applied if SolMates battery is ok with it"""
        return self.request("set_user_maximum_injection", {"injection": maximum_power})

    @bad_request_handling()
    def set_min_injection(self, minimum_power):
        """Sets user defined minimum injection power which is applied if SolMates battery is ok with it"""
        return self.request("set_user_minimum_injection", {"injection": minimum_power})

    def set_min_battery_percentage(self, minimum_percentage):
        """Sets user defined minimum battery percentage"""
        return self.request("set_user_minimum_battery_percentage", {"battery_percentage": minimum_percentage})

    def set_AP_mode(self):
        """This function opens the local Access Point (AP) of SolMate and leaves client (CLI) mode. This means you will
        have to connect to your SolMates WIFI "SolMate <serialnumber>". However, if SolMate has a wired connection as
        well online availability remains"""
        return self.request("revert_to_ap", {})

    def get_api_info(self):
        """Query all the available api calls."""
        self.request("get_api_info", {})

    def get_boost_injection(self):
        """Get the boost injection settings from the solmate."""
        return self.request("get_boost_injection", {})

    def set_boost_injection(self, set_time_in_secs: int, set_wattage: int):
        """
        Set the boost injection. If "set_time" is greater than 0 the boost will be activate. The actual wattage of
        the boost might differ due to inverter restrictions.
        """
        return self.request("set_boost_injection", {"time": set_time_in_secs, "wattage": set_wattage})

    def get_injection_profiles(self):
        """Get all the injection profiles from the solmate."""
        return self.request("get_injection_profiles", {})

    def set_injection_profiles(self, new_injection_profiles: dict, new_injection_profiles_timestamp: str):
        """
        Set the injection profiles on the solmate. This will overwrite all existing profiles. The new timestamp
        needs to be newer than the local timestamp on the solmate in order to update them. Timestamp format needs to be
        in "%Y-%m-%dT%H:%M:%S.%fZ" which is defined in solmate-sdk/utils.py as DATETIME_FORMAT_INJECTION_PROFILES for
        convenience.
        """
        return self.request(
            "set_injection_profiles",
            {
                "injection_profiles": new_injection_profiles,
                "injection_profiles_timestamp": new_injection_profiles_timestamp,
            },
        )

    def apply_injection_profile(self, injection_profile_id: str):
        """Apply the injection profile with the id of 'injection_profile_id'."""
        return self.request("apply_injection_profile", {"id": injection_profile_id})

    def close(self):
        """Correctly close the underlying connection."""
        if self.conn is None:
            raise RuntimeError("Connection has not yet been initialised.")
        asyncio.get_event_loop().run_until_complete(self.conn.close())


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

    def list_wifis(self):
        """Lists actually available and non hidden SSIDs"""
        return self.request("list_wifis", {})

    def connect_to_wifi(self, ssid, password):
        """Switches to other ssid or to the same - THE ACTUAL CONNECTION WILL BE BROKEN AFTER THAT
        A TimeOutError will be raised rather than the ConnectionClosedOnPurpose error"""
        self.request("connect_to_wifi", {"ssid": ssid, "password": password})
        raise ConnectionClosedOnPurpose

    def check_online(self):
        """Check whether the respective SolMate is currently online.
        The local api has no check_online route, it is online if you can connect to the local uri.
        Please call connect() or quickstart(...) before."""
        return self.conn != None
