from components.component import Component
from simulators.pir import run_pir_simulator
import threading
import json
from datetime import datetime


class PIRComponent(Component):
    def _run_simulated(self):
        pir_thread = threading.Thread(target=run_pir_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        pir_thread.start()
        return pir_thread

    def _callback(self, code, message):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code})
        pir_payload = {
            "measurement": "Motion",
            "simulated": self.settings['simulated'],
            "runs_on": self.settings["runs_on"],
            "codename": self.settings["codename"],
            "value": True
        }
        with self.counter_lock:
            # FIXME: check if ok not to retain, it only keeps 1 anyway
            self.publish_batch.append(('Motion', json.dumps(pir_payload), 0, False))
            self.publish_data_counter += 1
        if self.publish_data_counter >= self.publish_data_limit:
            self.publish_event.set()

    def _run_real(self):
        from sensors.pir import run_pir_loop, PIR
        pir = PIR(self.settings['pin'], self.settings['codename'], self._callback)
        pir_thread = threading.Thread(target=run_pir_loop, args=(pir, self.stop_event))
        pir_thread.start()
        return pir_thread
