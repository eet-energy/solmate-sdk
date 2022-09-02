import solmate_sdk
import paho.mqtt.client as mqtt
from time import sleep
import json

class config:
    mqtt_host = "mqtt.eclipseprojects.io"
    mqtt_port = 1883

client = solmate_sdk.SolMateAPIClient("test1")
client.quickstart()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

mqttClient = mqtt.Client()
mqttClient.on_connect = on_connect
mqttClient.connect(config.mqtt_host, config.mqtt_port, 60)
while True:
    print(".", end="", flush=True)
    try:
        live_values = client.get_live_values()
        online = client.check_online()
        #mqttClient.publish(f"eet/solmate/{client.serialnum}/live_values", json.dumps(live_values), 1)
        #mqttClient.publish(f"eet/solmate/{client.serialnum}/online", online, 1)
        for property_name in live_values.keys():
            if property_name == 'pv_power':
                mqttClient.publish(f"eet/solmate/{client.serialnum}/{property_name}", live_values[property_name], 1)
    except Exception as exc:
        print(exc)
    sleep(10)
