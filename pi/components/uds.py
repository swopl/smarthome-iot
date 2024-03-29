from components.component import Component
from simulators.uds import run_uds_simulator
import threading
from datetime import datetime


class UDSComponent(Component):
    def __init__(self, display_queue, settings, stop_event, publisher, alarm_queue):
        super().__init__(display_queue, settings, stop_event, publisher)
        self.alarm_queue = alarm_queue

    def _run_simulated(self):
        uds_thread = threading.Thread(target=run_uds_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        uds_thread.start()
        return uds_thread

    def _callback(self, code, distance):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "distance": distance})
        self.alarm_queue.put(distance)
        uds_payload = {
            "measurement": "Distance",
            "value": distance
        }
        self.publisher.add_to_batch([uds_payload], ["Distance"], self.settings)

    def _run_real(self):
        from sensors.uds import run_uds_loop, UDS
        uds = UDS(self.settings['trig_pin'], self.settings['echo_pin'], self.settings['codename'], self._callback)
        uds_thread = threading.Thread(target=run_uds_loop, args=(uds, self.stop_event))
        uds_thread.start()
        return uds_thread
