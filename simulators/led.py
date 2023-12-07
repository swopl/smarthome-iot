import time
from queue import Empty


class LEDSimulated:
    def __init__(self, code, stop_event, command_queue, display_queue, callback):
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
        self.display_queue = display_queue
        self.state = False
        self.callback = callback

    def _setup(self):
        self.callback(False, self.code)

    def run(self):
        self._setup()
        self._loop()

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                break
            try:
                command = self.command_queue.get(timeout=1)
            except Empty:
                continue
            if command:
                onoff = True
            else:
                onoff = False
            self.callback(onoff, self.code)
