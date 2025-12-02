import ssl
import json
import request
import time
import os
from paho.mqtt import client as mqtt



IOT_ENDPOINT = "apc4udnp426oi-ats.iot.eu-central-1.amazonaws.com"  
PORT = 8883
TOPIC = "decoded/#"
CLIENT_ID = "raspberrypi-subscriber"

CERT_ROOT = os.path.expanduser("~/iot/certs/AmazonRootCA1.pem")
CERT_FILE = os.path.expanduser("~/iot/certs/f397c6ef30d1506986fcfb78b23d519599e830bf5e15f66132f5f5cb678cd99c-certificate.pem.crt")
KEY_FILE  = os.path.expanduser("~/iot/certs/f397c6ef30d1506986fcfb78b23d519599e830bf5e15f66132f5f5cb678cd99c-private.pem.key")

def on_connect(client, userdata, flags, rc):
    print("Połączono, rc=", rc)
    client.subscribe(TOPIC)
    print("Zasubskrybowano:", TOPIC)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    requests.post(
        "http://your-django-server/api/data/",
        json={
            "temperature": payload["temperature"],
            "humidity": payload["humidity"],
            "pressure": payload["pressure"],
            "gas_resistance": payload["gas_resistance_ohm"]
        }
    )

def main():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.tls_set(ca_certs=CERT_ROOT,
                   certfile=CERT_FILE,
              	   keyfile=KEY_FILE,
                   tls_version=ssl.PROTOCOL_TLSv1_2)
    client.on_connect = on_connect
    client.on_message = on_message

    print("Łączenie do:", IOT_ENDPOINT)
    client.connect(IOT_ENDPOINT, PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()

