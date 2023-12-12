from components.component import Component
from simulators.uds import run_uds_simulator
import threading
from datetime import datetime


class UDSComponent(Component):
    def _run_simulated(self):
        uds_thread = threading.Thread(target=run_uds_simulator,
                                      args=(self._callback, self.stop_event, self.settings['codename']))
        uds_thread.start()
        return uds_thread

    def _callback(self, code, distance):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "distance": distance})
        uds_payload = {
            "measurement": "Distance",
            "value": distance
        }
        self.add_to_publish_batch([uds_payload], ["Distance"])

    def _run_real(self):
        from sensors.uds import run_uds_loop, UDS
        uds = UDS(self.settings['trig_pin'], self.settings['echo_pin'], self.settings['codename'], self._callback)
        uds_thread = threading.Thread(target=run_uds_loop, args=(uds, self.stop_event))
        uds_thread.start()
        return uds_thread
