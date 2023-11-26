import time
import random


def run_mbr_simulator(callback, stop_event, code):
    possible_keys = ["1", "2", "3", "A", "4", "5", "6", "B",
                     "7", "8", "9", "C", "*", "0", "#", "D"]
    while True:
        delay = random.randint(7, 14) / 5.0
        time.sleep(delay)
        if random.randint(0, 5) > 3:
            callback(code, random.choice(possible_keys))
        if stop_event.is_set():
            break
