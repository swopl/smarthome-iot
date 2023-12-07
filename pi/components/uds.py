from components.component import Component
from simulators.uds import run_uds_simulator
import threading
import json
from datetime import datetime


class UDSComponent(Component):
    def _run_simulated(self):
        uds_thread = threading.Thread(target=run_uds_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        uds_thread.start()
        return uds_thread

    def _callback(self, code, distance):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "distance": distance})
        uds_payload = {
            "measurement": "Distance",
            "simulated": self.settings['simulated'],
            "runs_on": self.settings["runs_on"],
            "codename": self.settings["codename"],
            "value": distance
        }
        with self.counter_lock:
            # FIXME: check if ok not to retain, it only keeps 1 anyway
            self.publish_batch.append(('Distance', json.dumps(uds_payload), 0, False))
            self.publish_data_counter += 1
        if self.publish_data_counter >= self.publish_data_limit:
            self.publish_event.set()

    def _run_real(self):
        from sensors.uds import run_uds_loop, UDS
        uds = UDS(self.settings['trig_pin'], self.settings['echo_pin'], self.settings['codename'], self._callback)
        uds_thread = threading.Thread(target=run_uds_loop, args=(uds, self.stop_event))
        uds_thread.start()
        return uds_thread
