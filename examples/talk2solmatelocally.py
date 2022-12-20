from getpass import getpass
from time import sleep

import solmate_sdk
from solmate_sdk.utils import retry
from websockets.exceptions import ConnectionClosedError
from asyncio.exceptions import TimeoutError

client = solmate_sdk.LocalSolMateAPIClient("X2S1K0506A00000001")
# Use your SolMates local IP Address here on port 9124 i.e. ws://<IP>:9124 if it is connected to your WLAN already
# Use ws://192.168.4.1:9124/ if you are connected to your SolMate via its Access Point ("SolMate <serialnumber>")
client.uri = "ws://192.168.0.138:9124/"


@retry(10, TimeoutError, 100)  # to handle WLAN switching
@retry(10, ConnectionClosedError, 30)
def run_continuously():
    client.quickstart()

    if input("Want to change wifi before we start\n\n Make sure to have SolMate FW >= 0.4.2-d").lower() == "y":
        # This will eventually trigger a TimeoutError an the whole process is redone in the new wifi
        print(f"Choose your desired WIFI {client.serialnum}: ")
        wifi = input(f"Type in your WIFI from: {client.list_wifis()}")
        password = getpass(f"Enter your WIFI key")
        if wifi != "" and password != "":
            print(f"Solmate {client.serialnum}: {client.connect_to_wifi(wifi, password)}")

    while True:
        print(f"Solmate {client.serialnum}: {client.list_wifis()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_live_values()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_recent_logs()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_software_version()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_grid_mode()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_user_settings()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_injection_settings()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.set_min_injection(0)}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_injection_settings()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.set_max_injection(50)}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_injection_settings()}")
        sleep(10)


if __name__ == "__main__":
    run_continuously()
