from time import sleep
import solmate_sdk

client = solmate_sdk.SolMateAPIClient("test1")
client.quickstart()
while True:
    print(f"Solmate {client.serialnum}: {client.get_live_values()}")
    sleep(5)