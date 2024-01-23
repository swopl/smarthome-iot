import logging
import threading
from abc import abstractmethod

from exterior_interacting.publisher.publisher import Publisher


class Component:
    # WARNING! Watch out to send publisher on some
    def __init__(self, display_queue, settings, stop_event, publisher: Publisher = None):
        self.display_queue = display_queue
        self.settings = settings
        self.stop_event = stop_event
        self.publisher = publisher

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
        if self.publisher:
            self.publisher.start_thread()

    @abstractmethod
    def _run_real(self) -> threading.Thread:
        pass
