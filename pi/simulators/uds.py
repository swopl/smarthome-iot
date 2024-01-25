import csv
import time
import random


def run_uds_simulator(callback, stop_event, code):
    simulated_values = []
    with open("./pre_simulated/uds_entering.csv", "r") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        for row in csv_reader:
            simulated_values.extend([float(value) for value in row])
    i = 0
    while True:
        delay = random.randint(7, 14) / 5.0
        time.sleep(delay)
        callback(code, simulated_values[i])
        if (i + 1) < len(simulated_values):
            i = i + 1
        if stop_event.is_set():
            break
