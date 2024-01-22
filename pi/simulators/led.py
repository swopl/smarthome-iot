import time
from datetime import datetime, timedelta
from queue import Empty


class LEDSimulated:
    def __init__(self, code, stop_event, command_queue, callback):
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
        self.callback = callback
        self.someone_outside = False
        self.when_to_stop = None

    def _setup(self):
        self.callback(False, self.code)

    def run(self):
        self._setup()
        self._loop()

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                break
            # this will stop taking in commands while 'someone is outside'
            # TODO: is it good to buffer commands then like I'm doing here?
            if self.someone_outside:
                time.sleep(0.2)
                if datetime.now() > self.when_to_stop:
                    self.someone_outside = False
                    self.callback(False, self.code)
                continue
            try:
                command = self.command_queue.get(timeout=1)
            except Empty:
                continue
            if command["on"]:
                if "time" in command:
                    self.someone_outside = True
                    self.when_to_stop = datetime.now() + timedelta(seconds=float(command["time"]))
                onoff = True
            else:
                onoff = False
            self.callback(onoff, self.code)
