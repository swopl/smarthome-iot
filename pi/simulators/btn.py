import time
import random


def run_btn_simulator(callback, stop_event, code):
    pushed_in = False
    while True:
        # TODO: instead of doing this, allow push from CurseUI
        delay = random.randint(12, 13) / 5.0
        time.sleep(delay)
        pushed_in = not pushed_in
        callback(code, pushed_in)
        if stop_event.is_set():
            break
