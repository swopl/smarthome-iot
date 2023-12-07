from queue import Empty
import time


class ABZSimulated:
    def __init__(self, code, stop_event, command_queue, callback):
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
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
            pitch, duration = command["pitch"], command["duration"]
            self.callback({"pitch": pitch, "duration": duration}, self.code)
            time.sleep(duration)
            self.callback(False, self.code)
