import json
import logging
import threading
import paho.mqtt.publish as publish
from broker_settings import HOSTNAME, PORT
from datetime import datetime


class Publisher:
    def __init__(self, type_name: str, publish_data_limit=8888888):
        self.publish_data_limit = publish_data_limit
        self.publish_data_counter = 0
        self.publish_batch = []
        self.counter_lock = threading.Lock()
        self.publish_event = threading.Event()
        self.type_name = type_name

    # FIXME: check if ok not to retain, it only keeps 1 anyway
    def add_to_batch(self, payloads: list[dict], topics: list[str], settings, qos=0, retain=False):
        for payload in payloads:
            payload.update({
                "time": datetime.utcnow().isoformat() + "Z",
                "simulated": settings["simulated"],
                "runs_on": settings["runs_on"],
                "publisher": self.type_name,
                "codename": settings["codename"],
            })
        mqtt_loads = [(topics[i], json.dumps(payloads[i]), qos, retain) for i in range(len(payloads))]
        with self.counter_lock:
            self.publish_batch.extend(mqtt_loads)
            self.publish_data_counter += 1
        if self.publish_data_counter >= self.publish_data_limit:
            self.publish_event.set()

    def start_thread(self):
        publisher_thread = threading.Thread(target=self._publisher_task, args=())
        publisher_thread.daemon = True
        publisher_thread.start()

    def _publisher_task(self):
        while True:
            self.publish_event.wait()
            with self.counter_lock:
                local_batch = self.publish_batch.copy()
                publishing = self.publish_data_counter
                self.publish_data_counter = 0
                self.publish_batch.clear()
            publish.multiple(local_batch, hostname=HOSTNAME, port=PORT)
            logging.info(f"{self.type_name} published {publishing} values")
            self.publish_event.clear()
