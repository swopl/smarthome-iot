import logging
import threading
from queue import Empty
from actuators.lcd.PCF8574 import PCF8574_GPIO
from actuators.lcd.Adafruit_LCD1602 import Adafruit_CharLCD

PCF8574_ADDRESS = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_ADDRESS = 0x3F  # I2C address of the PCF8574A chip.


class LCD:
    def __init__(self, code, stop_event, command_queue, callback):
        self.code = code
        self.stop_event = stop_event
        self.callback = callback
        self.command_queue = command_queue
        self.lcd = None  # type:Adafruit_CharLCD | None
        self.mcp = None  # type:PCF8574_GPIO | None

    def _setup(self):
        # Create PCF8574 GPIO adapter.
        try:
            self.mcp = PCF8574_GPIO(PCF8574_ADDRESS)
        except:
            try:
                self.mcp = PCF8574_GPIO(PCF8574A_ADDRESS)
            except:
                print('I2C Address Error !')
                raise KeyboardInterrupt  # FIXME: would this error exit safely actually?
                # FIXME: ^ answer is ALMOST DEFINITELY NOT!!!
        # Create LCD, passing in MCP GPIO adapter.
        self.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], GPIO=self.mcp)

    def run(self):
        logging.debug(f"Thread {threading.get_ident()} running {self.code}")
        self._setup()
        self._loop()

    # assumes 2 lines and 16 (?) characters per line
    def _loop(self):
        self.mcp.output(3, 1)  # turn on LCD backlight
        self.lcd.begin(16, 2)  # set number of LCD lines and columns
        while True:
            if self.stop_event.is_set():
                self._stop()
                break
            try:
                # format: "{max16}\n{max16}"
                command = self.command_queue.get(timeout=1)
            except Empty:
                continue
            # self.lcd.clear()  # TODO: do i need to clear? test on real
            self.lcd.setCursor(0, 0)  # set cursor position
            self.lcd.message(command)
            self.callback(self.code, command)

    def _stop(self):
        self.lcd.clear()
