"""Contains the high-level asynchronous API client."""

import base64
import getpass
import hashlib
import json
from typing import Optional

from .apiclient import SolMateAPIClient, LocalSolMateAPIClient

DEFAULT_DEVICE_ID = "solmate-sdk"
SOL_URI = "wss://sol.eet.energy:9124"


class AsyncSolMateAPIClient(SolMateAPIClient):
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
        super().__init__(serialnum, uri)

    async def connect(self):
        """Attempts to connect to the server and initialize the client."""
        return await super()._async_connect()

    async def _request(self, route, data):
        """Method to make requests to the API."""
        return await super()._async_request(route, data)

    async def login(self, user_password, device_id=DEFAULT_DEVICE_ID) -> str:
        """Method to generate the authentication token from the serialnumber + password."""
        return await super()._async_login(user_password, device_id)

    async def check_uri(self, auth_token, device_id):
        """Handles redirections using verification of uri and dummy request gaining redirection info"""
        return await super()._async_check_uri(auth_token, device_id)

    async def authenticate(self, auth_token, device_id=DEFAULT_DEVICE_ID):
        """Given the authentication token, try to authenticate this websocket connection.
        Subsequent method calls to protected methods are unlocked this way.
        """
        return await super()._async_authenticate(auth_token, device_id)

    async def quickstart(self, password=None, device_id=DEFAULT_DEVICE_ID):
        """Connect, login, authenticate and store the token for future use!"""
        return await super()._async_quickstart(password, device_id)

    async def get_software_version(self):
        """Returns the actually installed software version"""
        return await super()._async_get_software_version()

    async def get_live_values(self):
        """Return current live values of the respective SolMate as a dictionary (pv power, battery state, injection)."""
        return await self._request("live_values", {})

    async def get_recent_logs(self, days=None, start_time=None):
        """Returns the latest logs on the sol server"""
        return await super()._async_get_recent_logs(days, start_time)

    async def get_milestones_savings(self, days=1):
        """Returns the latest milestones saving"""
        return await super()._async_get_milestones_savings(days)

    async def get_user_settings(self):
        """Returns user settings which are valid at the moment"""
        return await super()._async_get_user_settings()

    async def get_injection_settings(self):
        """Shows your injection settings."""
        return await super()._async_get_injection_settings()

    async def get_grid_mode(self):
        """Returns grid mode i.e. Offgrid mode ('island mode') or Ongrid mode"""
        return await super()._async_get_grid_mode()

    async def check_online(self):
        """Check whether the respective SolMate is currently online."""
        return await super()._async_check_online()

    async def set_max_injection(self, maximum_power):
        """Sets user defined maximum injection power which is applied if SolMates battery is ok with it"""
        return await super()._async_set_max_injection(maximum_power)

    async def set_min_injection(self, minimum_power):
        """Sets user defined minimum injection power which is applied if SolMates battery is ok with it"""
        return await super()._async_set_min_injection(minimum_power)

    async def set_min_battery_percentage(self, minimum_percentage):
        """Sets user defined minimum battery percentage"""
        return await super()._async_set_min_battery_percentage(minimum_percentage)

    async def set_AP_mode(self):
        """This function opens the local Access Point (AP) of SolMate and leaves client (CLI) mode. This means you will
        have to connect to your SolMates WIFI "SolMate <serialnumber>". However, if SolMate has a wired connection as
        well online availability remains"""
        return await super()._async_set_AP_mode()

    async def close(self):
        """Correctly close the underlying connection."""
        return await super()._async_close()


class AsyncLocalSolMateAPIClient(LocalSolMateAPIClient):
    """Like SolMateAPIClient, however in local mode some extra routes are available

    In the local mode there is no load_balancer between you and your SolMate - though self.uri_verified needs to be set

    Furthermore, it is necessary to authenticate again using a special device_id. You may need to clear your authstore
    file (if you tested the online API first)
    """
    def __init__(self, serialnum: str, uri=SOL_URI):
        super().__init__(serialnum, uri)

    async def list_wifis(self):
        """Lists actually available and non hidden SSIDs"""
        return await super()._async_list_wifis()

    async def connect_to_wifi(self, ssid, password):
        """Switches to other ssid or to the same - THE ACTUAL CONNECTION WILL BE BROKEN AFTER THAT
         A TimeOutError will be raised rather than the ConnectionClosedOnPurpose error"""
        return await super()._async_connect_to_wifi(ssid, password)

    async def check_online(self):
        """Check whether the respective SolMate is currently online.
        The local api has no check_online route, it is online if you can connect to the local uri.
        Please call connect() or quickstart(...) before."""
        return self.conn != None
