import time
import random


def run_btn_simulator(callback, stop_event, code):
    while True:
        delay = random.randint(10, 20) / 5.0
        time.sleep(delay)
        callback(code, f"{code} button pressed")
        if stop_event.is_set():
            break
