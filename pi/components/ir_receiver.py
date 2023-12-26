from components.component import Component
from simulators.ir_receiver import run_ir_receiver_simulator
import threading
from datetime import datetime


class IRReceiverComponent(Component):
    def __init__(self, display_queue, settings, stop_event, publisher, rgb_command_queue, on_color=(1, 1, 1)):
        super().__init__(display_queue, settings, stop_event, publisher)
        self.rgb_command_queue = rgb_command_queue
        self.on_color = on_color

    def decode_color(self, message: str):
        if message == "0":
            return 0, 0, 0
        if message == "8":
            return self.on_color
        if message.isdigit():
            num = int(message)
            self.on_color = (num >> 2) % 2, (num >> 1) % 2, num % 2
            return self.on_color

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
        color = self.decode_color(message)
        # TODO: allow web server to do same thing
        if color:
            self.rgb_command_queue.put(color)

    def _run_real(self):
        from sensors.ir_receiver import run_ir_receiver_loop, IRReceiver
        ir = IRReceiver(self.settings['pin'], self.settings['codename'], self._callback)
        ir_thread = threading.Thread(target=run_ir_receiver_loop, args=(ir, self.stop_event))
        ir_thread.start()
        return ir_thread
