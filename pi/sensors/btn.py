import logging
import threading

import RPi.GPIO as GPIO
import time


# warning: expects pull up
class BTN(object):
    def __init__(self, pin, code, callback):
        self.pin = pin
        self.code = code
        self.callback = callback

    def btn_press(self, channel):
        if GPIO.input(channel):
            # FIXME: i had to invert these, i thought it was different?
            self.callback(self.code, False)
        else:
            self.callback(self.code, True)

    def start(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.btn_press, bouncetime=100)

    def stop(self):
        pass


def run_btn_loop(btn: BTN, stop_event):
    btn.start()
    logging.debug(f"Thread {threading.get_ident()} running {btn.code}")
    while True:
        if stop_event.is_set():
            btn.stop()
            break
        time.sleep(1)
