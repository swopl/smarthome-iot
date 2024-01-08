from components.component import Component
import threading
from datetime import datetime

from simulators.rgb import RGBSimulated


class RGBComponent(Component):
    def __init__(self, display_queue, settings, stop_event, command_queue):
        super().__init__(display_queue, settings, stop_event)
        self.command_queue = command_queue

    def _callback(self, color, code):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "color": str(color)})

    def _run_simulated(self):
        rgb = RGBSimulated(self.settings['codename'], self.stop_event,
                           self.command_queue, self._callback)
        rgb_thread = threading.Thread(target=rgb.run, args=())
        rgb_thread.start()
        return rgb_thread

    def _run_real(self):
        from actuators.rgb import RGB
        rgb = RGB(self.settings['pin_r'],self.settings['pin_g'], self.settings['pin_b'],
                  self.settings['codename'], self.stop_event, self.command_queue, self._callback)
        rgb_thread = threading.Thread(target=rgb.run, args=())
        rgb_thread.start()
        return rgb_thread
