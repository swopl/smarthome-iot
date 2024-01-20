import time
import random
import csv


def run_gyro_simulator(callback, stop_event, code):
    simulated_values = []
    with open("./pre_simulated/gyro_alarming.csv", "r") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        for row in csv_reader:
            simulated_values.append([float(value) for value in row])
    i = 0
    while True:
        delay = random.randint(7, 14) / 3.0
        time.sleep(delay)
        # FIXME: can this be negative in real world?
        # accel = (random.random() * 2.0 - 1.0, random.random() * 2.0 - 1.0, random.random() * 2.0 - 1.0)
        # gyro = (random.random() * 40 - 20, random.random() * 40 - 20, random.random() * 40 - 20)
        accel = tuple(simulated_values[i][:3])
        gyro = tuple(simulated_values[i][3:])
        callback(code, accel, gyro)
        i = (i + 1) % len(simulated_values)
        if stop_event.is_set():
            break
