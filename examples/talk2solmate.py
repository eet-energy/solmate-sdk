from time import sleep
import solmate_sdk
from solmate_sdk.utils import retry
from websockets.exceptions import ConnectionClosedError

client = solmate_sdk.SolMateAPIClient("test1")


@retry(10, ConnectionClosedError, 30)
def run_continuously():
    client.quickstart()
    while True:
        print(f"Solmate {client.serialnum}: {client.get_live_values()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_grid_mode()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_user_settings()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_injection_settings()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.set_min_injection(50)}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_injection_settings()}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.set_max_injection(50)}")
        sleep(0.1)
        print(f"Solmate {client.serialnum}: {client.get_injection_settings()}")
        sleep(10)


if __name__ == "__main__":
    run_continuously()
