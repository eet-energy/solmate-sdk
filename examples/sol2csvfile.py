from time import sleep
import solmate_sdk
import csv

client = solmate_sdk.SolMateAPIClient("test1")
client.quickstart()
vals = client.get_live_values()
keys = vals.keys()
with open(f'{client.serialnum}.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = keys)
    writer.writeheader()
    writer.writerow(vals)
while True:
    with open(f'{client.serialnum}.csv', 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = keys)
        writer.writerow(client.get_live_values())
    sleep(1)
