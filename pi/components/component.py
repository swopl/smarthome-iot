import logging
import threading
from abc import abstractmethod


class Component:
    def __init__(self, display_queue, settings, stop_event):
        self.display_queue = display_queue
        self.settings = settings
        self.stop_event = stop_event

    @abstractmethod
    def _run_simulated(self) -> threading.Thread:
        pass

    def run(self, threads):
        if self.settings['simulated']:
            logging.debug(f"Starting {self.settings['codename']} simulator")
            thread = self._run_simulated()
            logging.debug(f"{self.settings['codename']} simulator started")
        else:
            logging.debug(f"Starting {self.settings['codename']} loop")
            thread = self._run_real()
            logging.debug(f"{self.settings['codename']} loop started")
        threads.append(thread)

    @abstractmethod
    def _run_real(self) -> threading.Thread:
        pass
