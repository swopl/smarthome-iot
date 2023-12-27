# -----------------------------------------#
# Name - IR-Finalized.py
# Description - The finalized code to read data from an IR sensor and then reference it with stored values
# Author - Lime Parallelogram
# License - Completely Free
# Date - 12/09/2019
# ------------------------------------------------------------#
# Imports modules
import logging
import threading

import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import time
from components.ir_receiver_glob import Buttons, ButtonsNames



# Gets binary value
def getBinary(pin, timeout=timedelta(seconds=1)):
    # Internal vars
    num1s = 0  # Number of consecutive 1s read
    binary = 1  # The binary value
    command = []  # The list to store pulse times in
    previousValue = 0  # The last value
    value = GPIO.input(pin)  # The current value

    # Waits for the sensor to pull pin low

    wait_start = datetime.now()
    while value:
        time.sleep(0.0001)  # This sleep decreases CPU utilization immensely
        value = GPIO.input(pin)
        if datetime.now() - wait_start > timeout:
            return

    # Records start time
    startTime = datetime.now()

    while True:
        # If change detected in value
        if previousValue != value:
            now = datetime.now()
            pulseTime = now - startTime  # Calculate the time of pulse
            startTime = now  # Reset start time
            command.append((previousValue, pulseTime.microseconds))  # Store recorded data

        # Updates consecutive 1s variable
        if value:
            num1s += 1
        else:
            num1s = 0

        # Breaks program when the amount of 1s surpasses 10000
        if num1s > 10000:
            break

        # Re-reads pin
        previousValue = value
        value = GPIO.input(pin)

    # Converts times to binary
    for (typ, tme) in command:
        if typ == 1:  # If looking at rest period
            if tme > 1000:  # If pulse greater than 1000us
                binary = binary * 10 + 1  # Must be 1
            else:
                binary *= 10  # Must be 0

    if len(str(binary)) > 34:  # Sometimes, there is some stray characters
        binary = int(str(binary)[:34])

    return binary


# Convert value to hex
def convert_hex(binary_value):
    tmp_b2 = int(str(binary_value), 2)  # Temporarely propper base 2
    return hex(tmp_b2)


class IRReceiver(object):
    def __init__(self, pin, code, callback):
        self.pin = pin
        self.code = code
        self.callback = callback

    def signal_detect(self, signal):
        self.callback(self.code, signal)

    def start(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

    def stop(self):
        pass


def run_ir_receiver_loop(ir: IRReceiver, stop_event):
    ir.start()
    logging.debug(f"Thread {threading.get_ident()} running {ir.code}")
    while True:
        if stop_event.is_set():
            ir.stop()
            break
        binary = getBinary(ir.pin)
        if not binary:
            continue
        in_data = convert_hex(binary)  # Runs subs to get incoming hex value
        for button in range(len(Buttons)):  # Runs through every value in list
            if hex(Buttons[button]) == in_data:  # Checks this against incoming
                ir.signal_detect(ButtonsNames[button])
