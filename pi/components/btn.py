from components.component import Component
from simulators.btn import run_btn_simulator
import threading
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

    def _run_real(self):
        from sensors.btn import run_btn_loop, BTN
        btn = BTN(self.settings['pin'], self.settings['codename'], self._callback)
        btn_thread = threading.Thread(target=run_btn_loop, args=(btn, self.stop_event))
        btn_thread.start()
        return btn_thread
