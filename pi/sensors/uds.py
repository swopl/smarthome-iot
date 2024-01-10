import logging
import threading

import RPi.GPIO as GPIO
import time


class UDS(object):
    def __init__(self, trig_pin, echo_pin, code, callback):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.code = code
        self.callback = callback

    def do_reading(self):
        distance = self._get_distance()
        logging.debug(f"UDS.do_reading: {distance}; Trig: {self.trig_pin}, Echo: {self.echo_pin}")
        # distance is None when measurement times out
        if distance is not None:
            self.callback(self.code, distance)

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def _get_distance(self):
        GPIO.output(self.trig_pin, False)
        time.sleep(0.2)
        GPIO.output(self.trig_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trig_pin, False)
        pulse_start_time = time.time()
        pulse_end_time = time.time()

        max_iter = 1000

        iter = 0
        while GPIO.input(self.echo_pin) == 0:
            if iter > max_iter:
                return None
            pulse_start_time = time.time()
            iter += 1

        iter = 0
        while GPIO.input(self.echo_pin) == 1:
            if iter > max_iter:
                return None
            pulse_end_time = time.time()
            iter += 1

        pulse_duration = pulse_end_time - pulse_start_time
        distance = (pulse_duration * 34300) / 2
        return distance

    def stop(self):
        pass


def run_uds_loop(uds: UDS, stop_event):
    uds.setup()
    logging.debug(f"Thread {threading.get_ident()} running {uds.code}")
    while True:
        uds.do_reading()
        if stop_event.is_set():
            uds.stop()
            break
        time.sleep(0.6)
