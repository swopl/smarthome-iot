import threading

import RPi.GPIO as GPIO
from queue import Empty


class RGB:
    def __init__(self, pin_r, pin_g, pin_b, code, stop_event, command_queue, callback):
        self.pin_r = pin_r
        self.pin_g = pin_g
        self.pin_b = pin_b
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
        self.callback = callback

    def _setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_r, GPIO.OUT)
        GPIO.setup(self.pin_g, GPIO.OUT)
        GPIO.setup(self.pin_b, GPIO.OUT)
        GPIO.output(self.pin_r, GPIO.LOW)
        GPIO.output(self.pin_g, GPIO.LOW)
        GPIO.output(self.pin_b, GPIO.LOW)
        self.callback((0, 0, 0), self.code)

    def run(self):
        print(threading.get_ident(), self.code)
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
            GPIO.output(self.pin_r, GPIO.HIGH if command[0] else GPIO.LOW)
            GPIO.output(self.pin_g, GPIO.HIGH if command[1] else GPIO.LOW)
            GPIO.output(self.pin_b, GPIO.HIGH if command[2] else GPIO.LOW)
            self.callback(command, self.code)

    def _stop(self):
        pass
