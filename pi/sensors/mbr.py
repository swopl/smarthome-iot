import logging
import threading

import RPi.GPIO as GPIO
import time


class MBR(object):
    # [r1, r2, r3, r4]
    def __init__(self, r: list, c: list, code, callback):
        self.r = r.copy()
        self.c = c.copy()
        self.code = code
        self.callback = callback
        self.working = True

    def start_looping(self, stop_event):
        GPIO.setmode(GPIO.BCM)

        # FIXME: this might be necessary
        # GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.r[0], GPIO.OUT)
        GPIO.setup(self.r[1], GPIO.OUT)
        GPIO.setup(self.r[2], GPIO.OUT)
        GPIO.setup(self.r[3], GPIO.OUT)

        # Make sure to configure the input pins to use the internal pull-down resistors
        GPIO.setup(self.c[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.c[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.c[2], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.c[3], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        logging.debug(f"Thread {threading.get_ident()} running {self.code}")
        self._loop(stop_event)

    def read_line(self, line, characters):
        ret = []
        GPIO.output(line, GPIO.HIGH)
        if GPIO.input(self.c[0]) == 1:
            ret.append(characters[0])
        if GPIO.input(self.c[1]) == 1:
            ret.append(characters[1])
        if GPIO.input(self.c[2]) == 1:
            ret.append(characters[2])
        if GPIO.input(self.c[3]) == 1:
            ret.append(characters[3])
        GPIO.output(line, GPIO.LOW)
        return ret

    def _loop(self, stop_event):
        while self.working:
            # call the read_line function for each row of the keypad
            chars = []
            chars.extend(self.read_line(self.r[0], ["1", "2", "3", "A"]))
            chars.extend(self.read_line(self.r[1], ["4", "5", "6", "B"]))
            chars.extend(self.read_line(self.r[2], ["7", "8", "9", "C"]))
            chars.extend(self.read_line(self.r[3], ["*", "0", "#", "D"]))
            if chars:
                self.callback(self.code, chars)
            time.sleep(0.2)
            if stop_event.is_set():
                self.stop()

    def stop(self):
        self.working = False


def run_mbr_loop(mbr: MBR, stop_event):
    mbr.start_looping(stop_event)
