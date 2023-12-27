import logging
import threading

import RPi.GPIO as GPIO
from queue import Empty
import time


class ABZ:
    def __init__(self, pin, code, stop_event, command_queue, callback):
        self.pin = pin
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
        self.callback = callback

    def _setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def _buzz(self, pitch, duration):
        period = 1.0 / pitch
        delay = period / 2
        cycles = int(duration * pitch)
        for i in range(cycles):
            GPIO.output(self.pin, True)
            time.sleep(delay)
            GPIO.output(self.pin, False)
            time.sleep(delay)

    def run(self):
        logging.debug(f"Thread {threading.get_ident()} running {self.code}")
        self._setup()
        self._loop()

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                break
            try:
                command = self.command_queue.get(timeout=1)
            except Empty:
                continue
            pitch = command["pitch"]
            duration = command["duration"]
            self.callback({"pitch": pitch, "duration": duration}, self.code)
            self._buzz(pitch, duration)
            self.callback(False, self.code)
