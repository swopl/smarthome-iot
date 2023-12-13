from components.component import Component
from simulators.mbr import run_mbr_simulator
import threading
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
            "value": message
        }
        self.publisher.add_to_batch([mbr_payload], ["Keypad"])

    def _run_real(self):
        from sensors.mbr import run_mbr_loop, MBR
        # TODO: check if this is passed correctly
        mbr = MBR(self.settings['R'], self.settings['C'], self.settings['codename'], self._callback)
        mbr_thread = threading.Thread(target=run_mbr_loop, args=(mbr, self.stop_event))
        mbr_thread.start()
        return mbr_thread
