import time
import random
from components.ir_receiver_glob import ButtonsNames


def run_ir_receiver_simulator(callback, stop_event, code):
    while True:
        delay = random.randint(7, 14) / 2.0
        time.sleep(delay)
        callback(code, random.choice(ButtonsNames))
        if stop_event.is_set():
            break
