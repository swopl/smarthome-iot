import threading
import json
from components.component import Component
from simulators.dht import run_dht_simulator
from datetime import datetime


class DHTComponent(Component):
    def _run_simulated(self):
        dht_thread = threading.Thread(target=run_dht_simulator,
                                      args=(2, self._callback, self.stop_event, self.settings['codename']))
        dht_thread.start()
        return dht_thread

    def _callback(self, humidity, temperature, code):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "temperature": temperature, "humidity": humidity})
        temp_payload = {
            "measurement": "Temperature",
            "simulated": self.settings['simulated'],
            "runs_on": self.settings["runs_on"],
            "name": self.settings["codename"],
            "value": temperature
        }

        humidity_payload = {
            "measurement": "Humidity",
            "simulated": self.settings['simulated'],
            "runs_on": self.settings["runs_on"],
            "name": self.settings["codename"],
            "value": humidity
        }

        with self.counter_lock:
            self.publish_batch.append(('Temperature', json.dumps(temp_payload), 0, True))
            self.publish_batch.append(('Humidity', json.dumps(humidity_payload), 0, True))
            self.publish_data_counter += 1

        if self.publish_data_counter >= self.publish_data_limit:
            self.publish_event.set()

    def _run_real(self):
        from sensors.dht import run_dht_loop, DHT
        dht = DHT(self.settings['pin'])
        dht_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht_callback, self.stop_event))
        dht_thread.start()
        return dht_thread
