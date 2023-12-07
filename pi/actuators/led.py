import RPi.GPIO as GPIO
from queue import Empty


class LED:
    def __init__(self, pin, code, stop_event, command_queue, callback):
        self.pin = pin
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
        self.callback = callback

    def _setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self.callback(False, self.code)

    def run(self):
        self._setup()
        self._loop()

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                self._stop()
                break
            try:
                command = self.command_queue.get(timeout=1)
            except Empty:
                continue
            if command:
                GPIO.output(self.pin, GPIO.HIGH)
                onoff = True
            else:
                GPIO.output(self.pin, GPIO.LOW)
                onoff = False
            self.callback(onoff, self.code)

    def _stop(self):
        GPIO.output(self.pin, GPIO.LOW)
