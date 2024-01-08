from components.component import Component
import threading
from datetime import datetime
from simulators.lcd import LCDSimulated


class LCDComponent(Component):
    def __init__(self, display_queue, settings, stop_event, command_queue):
        super().__init__(display_queue, settings, stop_event)
        self.command_queue = command_queue

    def _callback(self, code, message: str):
        t = datetime.now()
        message = str(message).replace("\n", "\\n")
        self.display_queue.put({"timestamp": t, "code": code, "message": message})

    def _run_simulated(self):
        lcd = LCDSimulated(self.settings['codename'], self.stop_event,
                           self.command_queue, self._callback)
        lcd_thread = threading.Thread(target=lcd.run, args=())
        lcd_thread.start()
        return lcd_thread

    def _run_real(self):
        from actuators.lcd.LCD1602 import LCD
        lcd = LCD(self.settings['codename'], self.stop_event, self.command_queue, self._callback)
        lcd_thread = threading.Thread(target=lcd.run, args=())
        lcd_thread.start()
        return lcd_thread
