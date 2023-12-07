from components.component import Component
from simulators.dht import run_dht_simulator
import threading
import time


class DHTComponent(Component):
    def _run_simulated(self):
        dht_thread = threading.Thread(target=run_dht_simulator,
                                      args=(2, self._callback, self.stop_event, self.settings['codename']))
        dht_thread.start()
        return dht_thread

    def _callback(self, humidity, temperature, code):
        t = time.localtime()
        self.display_queue.put({"timestamp": t, "code": code, "temperature": temperature, "humidity": humidity})

    def _run_real(self):
        from sensors.dht import run_dht_loop, DHT
        dht = DHT(self.settings['pin'])
        dht_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht_callback, self.stop_event))
        dht_thread.start()
        return dht_thread
