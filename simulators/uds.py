import time
import random


def run_uds_simulator(callback, stop_event, code):
    while True:
        delay = random.randint(7, 14) / 5.0
        time.sleep(delay)
        callback(code, random.randint(10, 1000) / 100)
        if stop_event.is_set():
            break
