import time
from datetime import datetime, timedelta
import logging
import threading

import RPi.GPIO as GPIO
from queue import Empty


class LED:
    def __init__(self, pin, code, stop_event, command_queue, callback):
        self.pin = pin
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
        self.callback = callback
        self.someone_outside = False
        self.when_to_stop = None

    def _setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self.callback(False, self.code)

    def run(self):
        logging.debug(f"Thread {threading.get_ident()} running {self.code}")
        self._setup()
        self._loop()

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                self._stop()
                break
            # this will stop taking in commands while 'someone is outside'
            # TODO: is it good to buffer commands then like I'm doing here?
            if self.someone_outside:
                time.sleep(0.2)
                if datetime.now() > self.when_to_stop:
                    GPIO.output(self.pin, GPIO.LOW)
                    self.someone_outside = False
                    self.callback(False, self.code)
                continue
            try:
                command = self.command_queue.get(timeout=0.2)
            except Empty:
                continue
            if command["on"]:
                if "time" in command:
                    self.someone_outside = True
                    self.when_to_stop = datetime.now() + timedelta(seconds=float(command["time"]))
                GPIO.output(self.pin, GPIO.HIGH)
                onoff = True
            else:
                GPIO.output(self.pin, GPIO.LOW)
                onoff = False
            self.callback(onoff, self.code)

    def _stop(self):
        pass
