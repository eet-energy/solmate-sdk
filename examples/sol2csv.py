from time import sleep
import solmate_sdk

SEPERATOR=';'

client = solmate_sdk.SolMateAPIClient("test1")
client.quickstart()

vals = client.get_live_values()
keys = vals.keys()
print("serial_number", end=SEPERATOR)
for k in vals.keys():
    print(k, end=SEPERATOR)
print()
while True:
    vals = client.get_live_values()
    print(client.serialnum, end=SEPERATOR)
    for k in keys:
        if k in vals:
            print(vals[k], end=SEPERATOR)
        else:
            print(" ", end=SEPERATOR)
    print()
    sleep(5)