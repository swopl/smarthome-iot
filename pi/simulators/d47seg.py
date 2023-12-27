import time


class D47SEGSimulated:
    def __init__(self, code, stop_event, callback):
        self.code = code
        self.stop_event = stop_event
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
            n = time.ctime()[11:13] + time.ctime()[14:16]
            s = str(n).rjust(4)
            self.callback(self.code, s)
            time.sleep(1)
