from components.component import Component
from simulators.btn import run_btn_simulator
import threading
import json
from datetime import datetime


class BTNComponent(Component):
    def _run_simulated(self):
        btn_thread = threading.Thread(target=run_btn_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        btn_thread.start()
        return btn_thread

    def _callback(self, code, message):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code})
        btn_payload = {
            "measurement": "Button",
            "simulated": self.settings['simulated'],
            "runs_on": self.settings["runs_on"],
            "codename": self.settings["codename"],
            "value": True
        }
        with self.counter_lock:
            # FIXME: check if ok not to retain, it only keeps 1 anyway
            self.publish_batch.append(('Button', json.dumps(btn_payload), 0, False))
            self.publish_data_counter += 1
        if self.publish_data_counter >= self.publish_data_limit:
            self.publish_event.set()

    def _run_real(self):
        from sensors.btn import run_btn_loop, BTN
        btn = BTN(self.settings['pin'], self.settings['codename'], self._callback)
        btn_thread = threading.Thread(target=run_btn_loop, args=(btn, self.stop_event))
        btn_thread.start()
        return btn_thread
