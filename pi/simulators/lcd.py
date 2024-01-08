from queue import Empty


class LCDSimulated:
    def __init__(self, code, stop_event, command_queue, callback):
        self.code = code
        self.stop_event = stop_event
        self.command_queue = command_queue
        self.callback = callback

    def _setup(self):
        pass

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
            self.callback(self.code, command)
