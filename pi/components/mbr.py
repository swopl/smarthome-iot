from components.component import Component
from simulators.mbr import run_mbr_simulator
import threading
import json
from datetime import datetime


class MBRComponent(Component):
    def _run_simulated(self):
        mbr_thread = threading.Thread(target=run_mbr_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        mbr_thread.start()
        return mbr_thread

    def _callback(self, code, message):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "keys": message})
        mbr_payload = {
            "measurement": "Keypad",
            "simulated": self.settings['simulated'],
            "runs_on": self.settings["runs_on"],
            "codename": self.settings["codename"],
            "value": message
        }
        with self.counter_lock:
            # FIXME: check if ok not to retain, it only keeps 1 anyway
            self.publish_batch.append(('Keypad', json.dumps(mbr_payload), 0, False))
            self.publish_data_counter += 1
        if self.publish_data_counter >= self.publish_data_limit:
            self.publish_event.set()

    def _run_real(self):
        from sensors.mbr import run_mbr_loop, MBR
        # TODO: check if this is passed correctly
        mbr = MBR(self.settings['R'], self.settings['C'], self.settings['codename'], self._callback)
        mbr_thread = threading.Thread(target=run_mbr_loop, args=(mbr, self.stop_event))
        mbr_thread.start()
        return mbr_thread
