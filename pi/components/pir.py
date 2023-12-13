from components.component import Component
from simulators.pir import run_pir_simulator
import threading
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
            "value": True
        }
        self.publisher.add_to_batch([pir_payload], ["Motion"], self.settings)

    def _run_real(self):
        from sensors.pir import run_pir_loop, PIR
        pir = PIR(self.settings['pin'], self.settings['codename'], self._callback)
        pir_thread = threading.Thread(target=run_pir_loop, args=(pir, self.stop_event))
        pir_thread.start()
        return pir_thread
