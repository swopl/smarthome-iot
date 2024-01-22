from components.component import Component
import threading
from datetime import datetime
from simulators.d47seg import D47SEGSimulated


# TODO: allow commanding to show stuff instead of hardcoded ctime
class D47SEGComponent(Component):
    def __init__(self, display_queue, settings, stop_event, blinking_queue):
        super().__init__(display_queue, settings, stop_event)
        self.blinking_queue = blinking_queue

    def _callback(self, code, time_4d):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "time_4d": time_4d})

    def _run_simulated(self):
        d47seg = D47SEGSimulated(self.settings['codename'], self.stop_event, self._callback, self.blinking_queue)
        d47seg_thread = threading.Thread(target=d47seg.run, args=())
        d47seg_thread.start()
        return d47seg_thread

    def _run_real(self):
        from actuators.d47seg import D47SEG
        d47seg = D47SEG(self.settings['pins_segments'], self.settings['pins_digits'],
                        self.settings['codename'], self.stop_event, self._callback, self.blinking_queue)
        d47seg_thread = threading.Thread(target=d47seg.run, args=())
        d47seg_thread.start()
        return d47seg_thread
