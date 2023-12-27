import threading
from components.component import Component
from datetime import datetime
from simulators.gyro import run_gyro_simulator


class GyroComponent(Component):
    def _run_simulated(self):
        gyro_thread = threading.Thread(target=run_gyro_simulator,
                                       args=(self._callback, self.stop_event, self.settings['codename']))
        gyro_thread.start()
        return gyro_thread

    def _callback(self, code, acceleration, rotation):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code,
                                "acceleration": str(tuple(round(num, 3) for num in acceleration)),
                                "rotation": str(tuple(round(num, 2) for num in rotation))})
        acceleration_payload = {
            "measurement": "Acceleration",
            "value": list(acceleration)
        }
        rotation_payload = {
            "measurement": "Rotation",
            "value": list(rotation)
        }
        self.publisher.add_to_batch([acceleration_payload, rotation_payload],
                                    ["Acceleration", "Rotation"], self.settings)

    def _run_real(self):
        from sensors.gyro.gyro import run_gyro_loop, Gyro
        gyro = Gyro(self.settings['codename'], self._callback)
        gyro_thread = threading.Thread(target=run_gyro_loop, args=(gyro, self.stop_event))
        gyro_thread.start()
        return gyro_thread
