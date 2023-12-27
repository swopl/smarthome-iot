import threading
from components.component import Component
from simulators.dht import run_dht_simulator
from datetime import datetime


class DHTComponent(Component):
    def _run_simulated(self):
        dht_thread = threading.Thread(target=run_dht_simulator,
                                      args=(2, self._callback, self.stop_event, self.settings['codename']))
        dht_thread.start()
        return dht_thread

    def _callback(self, humidity, temperature, code, value_code):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "temperature": temperature, "humidity": humidity,
                                "value_code": value_code})
        temp_payload = {
            "measurement": "Temperature",
            "value": temperature
        }
        humidity_payload = {
            "measurement": "Humidity",
            "value": humidity
        }
        self.publisher.add_to_batch([temp_payload, humidity_payload],
                                    ["Temperature", "Humidity"], self.settings)

    def _run_real(self):
        from sensors.dht import run_dht_loop, DHT
        dht = DHT(self.settings['pin'], self.settings['codename'])
        dht_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, self._callback, self.stop_event))
        dht_thread.start()
        return dht_thread
