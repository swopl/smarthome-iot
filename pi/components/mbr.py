from components.component import Component
from simulators.mbr import run_mbr_simulator
import threading
from datetime import datetime


class MBRComponent(Component):
    def __init__(self, display_queue, settings, stop_event, publisher, alarm_queue):
        super().__init__(display_queue, settings, stop_event, publisher)
        self.alarm_queue = alarm_queue
        self.accumulated_keys = ""

    def _run_simulated(self):
        mbr_thread = threading.Thread(target=run_mbr_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        mbr_thread.start()
        return mbr_thread

    def _callback(self, code, message):
        t = datetime.now()
        self.accumulated_keys += message
        if message and self.accumulated_keys.endswith("*"):
            # this is so password is not shown forever
            self.display_queue.put({"timestamp": t, "code": code, "keys": ""})
            mbr_payload = {
                "measurement": "Keypad",
                "value": self.accumulated_keys
            }
            self.alarm_queue.put(self.accumulated_keys)
            self.publisher.add_to_batch([mbr_payload], ["Keypad"], self.settings)
            self.accumulated_keys = ""
        else:
            self.display_queue.put({"timestamp": t, "code": code, "keys": self.accumulated_keys})

    def _run_real(self):
        from sensors.mbr import run_mbr_loop, MBR
        # TODO: check if this is passed correctly
        mbr = MBR(self.settings['R'], self.settings['C'], self.settings['codename'], self._callback)
        mbr_thread = threading.Thread(target=run_mbr_loop, args=(mbr, self.stop_event))
        mbr_thread.start()
        return mbr_thread
