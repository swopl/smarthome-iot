import datetime
import logging
import threading
import time
from datetime import datetime, timedelta
from queue import Queue, Empty


class AlarmCommander:
    def __init__(self, stop_event):
        self.stop_event = stop_event
        self.abz_queues = []
        self.btn_queue = Queue()
        self.btn_state = False
        self.when_btn_pressed = datetime.now()
        self.alarm_active = False

    def activate(self) -> threading.Thread:
        alarm_thread = threading.Thread(target=self._loop, args=())
        alarm_thread.start()
        return alarm_thread

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                break
            time.sleep(1.1)
            self._check_button()
            if self.alarm_active:
                # TODO: also display on curse ui
                self._buzz_all()

    def _check_button(self):
        # FIXME: this expects only one button per pi, should work for our examples
        try:
            state = self.btn_queue.get(timeout=0.03)
        except Empty:
            return
        if not self.btn_state and state:
            self.btn_state = state
            self.when_btn_pressed = datetime.now()
        if self.btn_state and datetime.now() - self.when_btn_pressed >= timedelta(seconds=5):
            logging.info("Alarm activated due to DS")
            # TODO: send mqtt
            self.alarm_active = True
        if not state:
            self.btn_state = state

    def attach_abz(self, abz_queue):
        self.abz_queues.append(abz_queue)

    def _buzz_all(self):
        buzz = {"pitch": 440, "duration": 1.0}
        for abz_queue in self.abz_queues:
            abz_queue.put(buzz)
