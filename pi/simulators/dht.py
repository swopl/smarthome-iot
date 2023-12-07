import time
import random


def generate_values(initial_temp=25.0, initial_humidity=20.0):
    temperature = initial_temp
    humidity = initial_humidity
    while True:
        temperature = temperature + 1.0 * random.randint(-1, 1)
        humidity = humidity + 1.0 * random.randint(-1, 1)
        if humidity < 0.0:
            humidity = 0.0
        if humidity > 100.0:
            humidity = 100.0
        yield humidity, temperature


def run_dht_simulator(delay, callback, stop_event, code):
    for h, t in generate_values():
        time.sleep(delay)  # Delay between readings (adjust as needed)
        callback(h, t, code)
        if stop_event.is_set():
            break
