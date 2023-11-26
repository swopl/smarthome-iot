import time
import random


def run_pir_simulator(callback, stop_event, code):
    while True:
        delay = random.randint(7, 14) / 5.0
        time.sleep(delay)
        callback(code, f"{code} detected motion")
        if stop_event.is_set():
            break
