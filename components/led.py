from components.component import Component
from simulators.led import LEDSimulated
import threading
import time


class LEDComponent(Component):
    def __init__(self, display_queue, settings, stop_event, command_queue):
        super().__init__(display_queue, settings, stop_event)
        self.command_queue = command_queue

    def _callback(self, onoff, code):
        t = time.localtime()
        self.display_queue.put({"timestamp": t, "code": code, "onoff": "on" if onoff else "off"})

    def _run_simulated(self):
        led = LEDSimulated(self.settings['codename'], self.stop_event,
                           self.command_queue, self.display_queue, self._callback)
        led_thread = threading.Thread(target=led.run, args=())
        led_thread.start()
        return led_thread

    def _run_real(self):
        from actuators.led import LED
        led = LED(self.settings['pin'], self.settings['codename'],
                  self.stop_event, self.command_queue, self.display_queue, self._callback)
        led_thread = threading.Thread(target=led.run, args=())
        led_thread.start()
        return led_thread
