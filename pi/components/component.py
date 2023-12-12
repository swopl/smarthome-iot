import logging
import threading
import json
import paho.mqtt.publish as publish
from abc import abstractmethod
from broker_settings import HOSTNAME, PORT
from datetime import datetime


class Component:
    def __init__(self, display_queue, settings, stop_event, publish_data_limit=8):
        self.display_queue = display_queue
        self.settings = settings
        self.stop_event = stop_event
        self.publish_data_limit = publish_data_limit
        self.publish_data_counter = 0
        self.publish_batch = []
        self.counter_lock = threading.Lock()
        self.publish_event = threading.Event()

    # FIXME: check if ok not to retain, it only keeps 1 anyway
    def add_to_publish_batch(self, payloads: list[dict], topics: list[str], qos=0, retain=False):
        for payload in payloads:
            payload.update({
                "time": datetime.utcnow().isoformat() + "Z",
                "simulated": self.settings["simulated"],
                "runs_on": self.settings["runs_on"],
                "codename": self.settings["codename"],
            })
        mqtt_loads = [(topics[i], json.dumps(payloads[i]), qos, retain) for i in range(len(payloads))]
        with self.counter_lock:
            self.publish_batch.extend(mqtt_loads)
            self.publish_data_counter += 1
        if self.publish_data_counter >= self.publish_data_limit:
            self.publish_event.set()

    def _publisher_task(self):
        while True:
            self.publish_event.wait()
            with self.counter_lock:
                local_batch = self.publish_batch.copy()
                publishing = self.publish_data_counter
                self.publish_data_counter = 0
                self.publish_batch.clear()
            publish.multiple(local_batch, hostname=HOSTNAME, port=PORT)
            logging.info(f"{self.settings['codename']} published {publishing} dht values")
            self.publish_event.clear()

    @abstractmethod
    def _run_simulated(self) -> threading.Thread:
        pass

    def run(self, threads):
        if self.settings['simulated']:
            logging.debug(f"Starting {self.settings['codename']} simulator")
            thread = self._run_simulated()
            logging.debug(f"{self.settings['codename']} simulator started")
        else:
            logging.debug(f"Starting {self.settings['codename']} loop")
            thread = self._run_real()
            logging.debug(f"{self.settings['codename']} loop started")
        threads.append(thread)
        publisher_thread = threading.Thread(target=self._publisher_task, args=())
        publisher_thread.daemon = True
        publisher_thread.start()

    @abstractmethod
    def _run_real(self) -> threading.Thread:
        pass
