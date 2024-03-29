import logging
import queue
import threading
import RPi.GPIO as GPIO
import time


class D47SEG:
    # TODO: FIXME: dont use pin 4!!!! It makes problems because it is GP CLK.
    # CHANGE IT IN settings.json to sth else
    num = {' ': (0, 0, 0, 0, 0, 0, 0),
           '0': (1, 1, 1, 1, 1, 1, 0),
           '1': (0, 1, 1, 0, 0, 0, 0),
           '2': (1, 1, 0, 1, 1, 0, 1),
           '3': (1, 1, 1, 1, 0, 0, 1),
           '4': (0, 1, 1, 0, 0, 1, 1),
           '5': (1, 0, 1, 1, 0, 1, 1),
           '6': (1, 0, 1, 1, 1, 1, 1),
           '7': (1, 1, 1, 0, 0, 0, 0),
           '8': (1, 1, 1, 1, 1, 1, 1),
           '9': (1, 1, 1, 1, 0, 1, 1)}

    def __init__(self, pins_segments, pins_digits, code, stop_event, callback, blinking_queue):
        self.segments = pins_segments
        self.digits = pins_digits
        self.code = code
        self.stop_event = stop_event
        self.callback = callback
        self.blinking_queue = blinking_queue
        self.blinking = False

    def _setup(self):
        GPIO.setmode(GPIO.BCM)
        for segment in self.segments:
            GPIO.setup(segment, GPIO.OUT)
            GPIO.output(segment, 0)
        for digit in self.digits:
            GPIO.setup(digit, GPIO.OUT)
            GPIO.output(digit, 1)

    def run(self):
        logging.debug(f"Thread {threading.get_ident()} running {self.code}")
        self._setup()
        self._loop()

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                self._stop()
                break
            n = time.ctime()[11:13] + time.ctime()[14:16]
            s = str(n).rjust(4)
            self._draw(s)
            self.callback(self.code, s)
            # TODO: check if sleep is ok here, GPIO.output should keep outputting
            if self.blinking:
                time.sleep(0.5)
                s = "    "
                self._draw(s)
                self.callback(self.code, s)
                time.sleep(0.5)

    def _draw(self, s):
        for digit in range(4):
            for loop in range(0, 7):
                GPIO.output(self.segments[loop], self.num[s[digit]][loop])
                if (int(time.ctime()[18:19]) % 2 == 0) and (digit == 1):
                    GPIO.output(25, 1)
                else:
                    GPIO.output(25, 0)
            GPIO.output(self.digits[digit], 0)
            time.sleep(0.001)
            GPIO.output(self.digits[digit], 1)

    def _stop(self):
        pass
