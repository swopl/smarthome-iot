from flask import Flask
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# InfluxDB Configuration
token = "CHANGE_ME"
org = "FTN"
url = "http://localhost:8086"
bucket = "example_db"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)

# MQTT Configuration
mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()


def on_connect(client, userdata, flags, rc):
    client.subscribe("Temperature")
    client.subscribe("Humidity")
    client.subscribe("Motion")
    client.subscribe("Keypad")
    client.subscribe("Distance")
    client.subscribe("Button")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = lambda client, userdata, msg: save_to_db(json.loads(msg.payload.decode('utf-8')))


def save_to_db(data):
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    point = (
        Point(data["measurement"])
        .tag("simulated", data["simulated"])
        .tag("runs_on", data["runs_on"])
        .tag("codename", data["codename"])
        .field("measurement", data["value"])
    )
    write_api.write(bucket=bucket, org=org, record=point)


if __name__ == '__main__':
    app.run(debug=True)
