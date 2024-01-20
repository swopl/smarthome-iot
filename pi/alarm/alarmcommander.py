import datetime
import json
import logging
import threading
import time
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from queue import Queue, Empty


class AlarmCommander:
    def __init__(self, stop_event):
        self.stop_event = stop_event
        self.abz_queues = []
        self.btn_queue = Queue()
        self.mbr_queue = Queue()
        self.btn_state = False
        self.when_btn_pressed = datetime.now()
        self.alarm_active = False
        self.door_security_active = False
        self.security_system_password = "1234"  # TODO: actually extract to secret
        self.alarm_password = "5678"
        self.person_count = -1
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect("localhost", 1883, 60)  # TODO: extract host to file
        self.mqtt_client.loop_start()
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._process_message

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        self.mqtt_client.subscribe("AlarmInfo")  # TODO: think about qos and others
        self.mqtt_client.subscribe("PeopleCount")  # TODO: think about qos and others

    def _process_message(self, client, userdata, message):
        payload = json.loads(message.payload.decode("utf-8"))
        if message.topic == "AlarmInfo":
            if payload["state"] == "enabled":
                logging.info("Alarm: ENABLED")
                self.alarm_active = True
            elif payload["state"] == "disabled":
                logging.info("Alarm: DISABLED")
                self.alarm_active = False
            else:
                logging.fatal(f"Unknown alarm state received: {payload['state']}")
        elif message.topic == "PeopleCount":
            logging.info(f"Received PeopleCount payload: {payload}")
            self.person_count = payload  # TODO: test
        else:
            logging.warning(f"Unknown topic: {message.topic}")

    def activate(self) -> threading.Thread:
        alarm_thread = threading.Thread(target=self._loop, args=())
        alarm_thread.start()
        return alarm_thread

    def _loop(self):
        while True:
            if self.stop_event.is_set():
                break
            time.sleep(1.1)
            self._check_mbr()
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
            logging.info("Alarm activating due to DS...")
            self.mqtt_client.publish("AlarmInfo", json.dumps({
                "time": datetime.utcnow().isoformat() + "Z",
                "runs_on": "TODO",  # TODO: add runs_on
                "reason": "DS",
                "extra": "Door sensor pushed in for longer than 5 seconds",
                "state": "enabled"
            }), 2, True)
        if not state:
            self.btn_state = state

    def _check_mbr(self):
        try:
            keys = self.mbr_queue.get(timeout=0.03)
        except Empty:
            return
        if not keys:
            # TODO: will it ever actually get in here?
            return
        password = keys[:-1]
        if password == self.security_system_password:
            logging.info("MBR security system toggled")
            # TODO: send to server so other pi knows
            self.door_security_active = not self.door_security_active
        elif password == self.alarm_password and self.alarm_active:
            logging.info("Disabling alarm...")
            self.mqtt_client.publish("AlarmInfo", json.dumps({
                "time": datetime.utcnow().isoformat() + "Z",
                "runs_on": "TODO",  # TODO: add runs_on
                "reason": "MBR",
                "extra": "Deactivated by password",
                "state": "disabled"
            }), 2, True)
        else:
            logging.info("Wrong password attempted!")

    def attach_abz(self, abz_queue):
        self.abz_queues.append(abz_queue)

    def _buzz_all(self):
        buzz = {"pitch": 440, "duration": 1.0}
        for abz_queue in self.abz_queues:
            abz_queue.put(buzz)
