from components.component import Component
from simulators.ir_receiver import run_ir_receiver_simulator
import threading
from datetime import datetime


class IRReceiverComponent(Component):
    def __init__(self, display_queue, settings, stop_event, publisher, colorizer_queue):
        super().__init__(display_queue, settings, stop_event, publisher)
        self.colorizer_queue = colorizer_queue

    def _run_simulated(self):
        ir_thread = threading.Thread(target=run_ir_receiver_simulator,
                                     args=(self._callback, self.stop_event, self.settings['codename']))
        ir_thread.start()
        return ir_thread

    def _callback(self, code, message):
        t = datetime.now()
        self.display_queue.put({"timestamp": t, "code": code, "message": message})
        ir_payload = {
            "measurement": "IRReceiver",
            "value": message
        }
        self.publisher.add_to_batch([ir_payload], ["IRReceiver"], self.settings)
        if message.isdigit() and 0 <= int(message) <= 8 and self.colorizer_queue:
            self.colorizer_queue.put(int(message))

    def _run_real(self):
        from sensors.ir_receiver import run_ir_receiver_loop, IRReceiver
        ir = IRReceiver(self.settings['pin'], self.settings['codename'], self._callback)
        ir_thread = threading.Thread(target=run_ir_receiver_loop, args=(ir, self.stop_event))
        ir_thread.start()
        return ir_thread
