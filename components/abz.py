from components.component import Component
from simulators.abz import ABZSimulated
import threading
import time


class ABZComponent(Component):
    def __init__(self, display_queue, settings, stop_event, command_queue):
        super().__init__(display_queue, settings, stop_event)
        self.command_queue = command_queue

    def _callback(self, buzz, code):
        t = time.localtime()
        if not buzz:
            self.display_queue.put({"timestamp": t, "code": code, "buzz": "not buzzing"})
        else:
            self.display_queue.put({"timestamp": t, "code": code,
                                    "buzz": f"buzzing at {buzz['pitch']:> 5}Hz"})

    def _run_simulated(self):
        abz = ABZSimulated(self.settings['codename'], self.stop_event,
                           self.command_queue, self._callback)
        abz_thread = threading.Thread(target=abz.run, args=())
        abz_thread.start()
        return abz_thread

    def _run_real(self):
        from actuators.abz import ABZ
        abz = ABZ(self.settings['pin'], self.settings['codename'],
                  self.stop_event, self.command_queue, self._callback)
        abz_thread = threading.Thread(target=abz.run, args=())
        abz_thread.start()
        return abz_thread
