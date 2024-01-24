import json
import logging
import threading
from queue import Queue, Empty

import paho.mqtt.client as mqtt


class RGBColorizer:
    def __init__(self, stop_event, on_color=(1, 1, 1)):
        self.colorization_queue = Queue()
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect("localhost", 1883, 60)  # TODO: extract host to file
        self.mqtt_client.loop_start()
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._process_message
        self.on_color = on_color
        self.stop_event = stop_event
        self.rgb_command_queue = None

    def attach_rgb_command_queue(self, rgb_command_queue):
        self.rgb_command_queue = rgb_command_queue

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        self.mqtt_client.subscribe("RGBColor")

    def _process_message(self, client, userdata, message):
        payload = json.loads(message.payload.decode("utf-8"))
        logging.debug(f"RGBColorizer received color: {payload}")
        self.colorization_queue.put(int(payload))

    def activate(self) -> threading.Thread:
        colorizer_thread = threading.Thread(target=self._loop, args=())
        colorizer_thread.start()
        return colorizer_thread

    def decode_color(self, color_num: int):
        self.on_color = (color_num >> 2) % 2, (color_num >> 1) % 2, color_num % 2
        return self.on_color

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                break
            try:
                color_number = self.colorization_queue.get(timeout=0.5)
            except Empty:
                return
            colors = self.decode_color(color_number)
            if self.rgb_command_queue:
                self.rgb_command_queue.put(colors)
