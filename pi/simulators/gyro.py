import time
import random


def run_gyro_simulator(callback, stop_event, code):
    while True:
        delay = random.randint(7, 14) / 3.0
        time.sleep(delay)
        # FIXME: can this be negative in real world?
        accel = (random.random() * 2.0 - 1.0, random.random() * 2.0 - 1.0, random.random() * 2.0 - 1.0)
        gyro = (random.random() * 40 - 20, random.random() * 40 - 20, random.random() * 40 - 20)
        callback(code, accel, gyro)
        if stop_event.is_set():
            break
