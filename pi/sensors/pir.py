import logging
import threading

import RPi.GPIO as GPIO
import time


class PIR(object):
    def __init__(self, pin, code, callback):
        self.pin = pin
        self.code = code
        self.callback = callback

    def rising_motion_detect(self, channel):
        self.callback(self.code, f"PIR on {self.pin} detected motion")

    def start(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.rising_motion_detect)

    def stop(self):
        pass


def run_pir_loop(pir: PIR, stop_event):
    pir.start()
    logging.debug(f"Thread {threading.get_ident()} running {pir.code}")
    while True:
        if stop_event.is_set():
            pir.stop()
            break
        time.sleep(1)
