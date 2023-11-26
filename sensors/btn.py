import RPi.GPIO as GPIO
import time


# warning: expects pull up
class BTN(object):
    def __init__(self, pin, code, callback):
        self.pin = pin
        self.code = code
        self.callback = callback

    def btn_press(self):
        self.callback(self.code, f"BTN on {self.pin} pressed")

    def start(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.btn_press, bouncetime=100)

    def stop(self):
        pass


def run_btn_loop(btn: BTN, stop_event):
    btn.start()
    while True:
        if stop_event.is_set():
            btn.stop()
        time.sleep(1)
