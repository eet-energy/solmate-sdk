"""Contains the high-level synchronous API client."""

import asyncio

from .apiclient import SolMateAPIClient, LocalSolMateAPIClient

DEFAULT_DEVICE_ID = "solmate-sdk"
SOL_URI = "wss://sol.eet.energy:9124"

class SyncSolMateAPIClient(SolMateAPIClient):
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
    
    def __init__(self, serialnum: str, uri=SOL_URI, loop: asyncio.AbstractEventLoop=None):
        """Initializes the instance given a serial number and auth_token (signature).
        Leaves the underlying connection object uninitialised.
        """
        super().__init__(serialnum, uri)
        self.loop = loop
        if not self.loop:
            self.loop = asyncio.get_event_loop()

    def connect(self):
        """Attempts to connect to the server and initialize the client."""
        self.loop.run_until_complete(super()._async_connect())

    def _request(self, route, data):
        """Method to make requests to the API."""
        return self.loop.run_until_complete(super()._async_request(route, data))
    
    def login(self, user_password, device_id=DEFAULT_DEVICE_ID) -> str:
        """Method to generate the authentication token from the serialnumber + password."""
        return self.loop.run_until_complete(super()._async_login(user_password, device_id))
            
    def check_uri(self, auth_token, device_id):
        """Handles redirections using verification of uri and dummy request gaining redirection info"""
        self.loop.run_until_complete(super()._async_check_uri(auth_token, device_id))
        
    def authenticate(self, auth_token, device_id=DEFAULT_DEVICE_ID):
        """Given the authentication token, try to authenticate this websocket connection.
        Subsequent method calls to protected methods are unlocked this way.
        """
        self.loop.run_until_complete(super()._async_authenticate(auth_token, device_id))

    def quickstart(self, password=None, device_id=DEFAULT_DEVICE_ID):
        """Connect, login, authenticate and store the token for future use!"""
        self.loop.run_until_complete(super()._async_quickstart(password, device_id))

    def get_software_version(self):
        """Returns the actually installed software version"""
        return self.loop.run_until_complete(super()._async_request("get_solmate_info", {}))

    def get_live_values(self):
        """Return current live values of the respective SolMate as a dictionary (pv power, battery state, injection)."""
        return self.loop.run_until_complete(super()._async_request("live_values", {}))

    def get_recent_logs(self, days=None, start_time=None):
        """Returns the latest logs on the sol server"""
        import datetime
        if not days:
            days = 1
        if not start_time:
            start_time = datetime.datetime.now() - datetime.timedelta(days)
        end_time = start_time + datetime.timedelta(days)
        return self.loop.run_until_complete(super()._async_request("logs", {
            "timeframes": [
                {"start": start_time.isoformat()[:19],
                 "end": end_time.isoformat()[:19],
                 "resolution": 4}
            ]}))

    def get_milestones_savings(self, days=1):
        """Returns the latest milestones saving"""
        return self.loop.run_until_complete(super()._async_request("milestones_savings", {"days":days}))


    def get_user_settings(self):
        """Returns user settings which are valid at the moment"""
        return self.loop.run_until_complete(super()._async_request("get_user_settings", {}))

    def get_injection_settings(self):
        """Shows your injection settings."""
        return self.loop.run_until_complete(super()._async_request("get_injection_settings", {}))

    def get_grid_mode(self):
        """Returns grid mode i.e. Offgrid mode ('island mode') or Ongrid mode"""
        return self.loop.run_until_complete(super()._async_request("get_grid_mode", {}))

    def check_online(self):
        """Check whether the respective SolMate is currently online."""
        return self.loop.run_until_complete(super()._async_request("check_online", {"serial_num": self.serialnum}))["online"]

    def set_max_injection(self, maximum_power):
        """Sets user defined maximum injection power which is applied if SolMates battery is ok with it"""
        return self.loop.run_until_complete(super()._async_request("set_user_maximum_injection", {"injection": maximum_power}))

    def set_min_injection(self, minimum_power):
        """Sets user defined minimum injection power which is applied if SolMates battery is ok with it"""
        return self.loop.run_until_complete(super()._async_request("set_user_minimum_injection", {"injection": minimum_power}))

    def set_min_battery_percentage(self, minimum_percentage):
        """Sets user defined minimum battery percentage"""
        return self.loop.run_until_complete(super()._async_request("set_user_minimum_battery_percentage", {"battery_percentage": minimum_percentage}))

    def set_AP_mode(self):
        """This function opens the local Access Point (AP) of SolMate and leaves client (CLI) mode. This means you will
        have to connect to your SolMates WIFI "SolMate <serialnumber>". However, if SolMate has a wired connection as
        well online availability remains"""
        return self.loop.run_until_complete(super()._async_request("revert_to_ap", {}))
    
    def close(self):
        """Correctly close the underlying connection."""
        self.loop.run_until_complete(super()._async_close())


class SyncLocalSolMateAPIClient(LocalSolMateAPIClient):
    """Like SolMateAPIClient, however in local mode some extra routes are available

    In the local mode there is no load_balancer between you and your SolMate - though self.uri_verified needs to be set

    Furthermore, it is necessary to authenticate again using a special device_id. You may need to clear your authstore
    file (if you tested the online API first)
    """
    def __init__(self, serialnum: str, uri=SOL_URI, loop: asyncio.AbstractEventLoop=None):
        super().__init__(serialnum, uri)
        self.loop = loop
        if not self.loop:
            self.loop = asyncio.get_event_loop()

    def list_wifis(self):
        """Lists actually available and non hidden SSIDs"""
        return self.loop.run_until_complete(super()._async_list_wifis())

    def connect_to_wifi(self, ssid, password):
        """Switches to other ssid or to the same - THE ACTUAL CONNECTION WILL BE BROKEN AFTER THAT
         A TimeOutError will be raised rather than the ConnectionClosedOnPurpose error"""
        self.loop.run_until_complete(super()._async_connect_to_wifi(ssid, password))

    def check_online(self):
        """Check whether the respective SolMate is currently online.
        The local api has no check_online route, it is online if you can connect to the local uri.
        Please call connect() or quickstart(...) before."""
        self.loop.run_until_complete(super()._async_check_online())
