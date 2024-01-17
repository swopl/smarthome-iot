from components.component import Component
from simulators.btn import run_btn_simulator
import threading
from datetime import datetime


class BTNComponent(Component):
    def __init__(self, display_queue, settings, stop_event, publisher, alarm_queue):
        super().__init__(display_queue, settings, stop_event, publisher)
        self.alarm_queue = alarm_queue

    def _run_simulated(self):
        btn_thread = threading.Thread(target=run_btn_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        btn_thread.start()
        return btn_thread

    def _callback(self, code, on_off):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "on_off": on_off})
        btn_payload = {
            "measurement": "Button",
            "value": on_off
        }
        self.alarm_queue.put(on_off)
        self.publisher.add_to_batch([btn_payload], ["Button"], self.settings)

    def _run_real(self):
        from sensors.btn import run_btn_loop, BTN
        btn = BTN(self.settings['pin'], self.settings['codename'], self._callback)
        btn_thread = threading.Thread(target=run_btn_loop, args=(btn, self.stop_event))
        btn_thread.start()
        return btn_thread
