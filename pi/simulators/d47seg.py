import queue
import time


class D47SEGSimulated:
    def __init__(self, code, stop_event, callback, blinking_queue: queue.Queue):
        self.code = code
        self.stop_event = stop_event
        self.callback = callback
        self.blinking_queue = blinking_queue
        self.blinking = False

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
            try:
                self.blinking = self.blinking_queue.get(block=False)
            except queue.Empty:
                pass
            if not self.blinking:
                self.callback(self.code, s)
                time.sleep(1)
                continue
            self.callback(self.code, "    ")
            time.sleep(0.5)
            self.callback(self.code, s)
            time.sleep(0.5)

