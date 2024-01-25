import datetime
import json
import logging
import math
import threading
import time
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from queue import Queue, Empty


def calculate_intensity(acceleration):
    return math.sqrt(acceleration[0] ** 2 + acceleration[1] ** 2 + acceleration[2] ** 2)


class AlarmCommander:
    def __init__(self, stop_event, runs_on: str):
        self.stop_event = stop_event
        self.abz_queues = []
        self.bedroom_abz_queue = Queue()
        self.btn_queue = Queue()
        self.mbr_queue = Queue()
        self.gyro_queue = Queue()
        self.uds_queue = Queue()
        self.dpir_queue = Queue()
        self.rpir_queue = Queue()
        self.d47seg_blinking_queue = Queue()
        self.btn_pushed_in = False  # TODO: !! check if holding btn when starting glitches it
        self.when_btn_released = datetime.now()
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
        self.gyro_intensities = []
        self.uds_distances = []
        self.wakeup_alert_active = False
        self.door_security_timer = None
        self.alarm_activated_by_btn = False
        self.last_people_publish = datetime.now()
        self.runs_on = runs_on

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        self.mqtt_client.subscribe("AlarmInfo")  # TODO: think about qos and others
        self.mqtt_client.subscribe("PeopleCount")  # TODO: think about qos and others
        self.mqtt_client.subscribe("WakeupAlert")
        self.mqtt_client.subscribe("DoorSecuritySystem")

    # TODO: make prettier
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
            self.person_count = int(payload)  # TODO: test
        elif message.topic == "WakeupAlert":
            if payload["state"] == "enabled":
                logging.info("WakeupAlert: ENABLED")
                self.wakeup_alert_active = True
                self.d47seg_blinking_queue.put(True)
            elif payload["state"] == "disabled":
                logging.info("WakeupAlert: DISABLED")
                self.wakeup_alert_active = False
                self.d47seg_blinking_queue.put(False)
            else:
                logging.fatal(f"Unknown wakeup alert state received: {payload['state']}")
        elif message.topic == "DoorSecuritySystem":
            if payload["state"] == "enabled":
                logging.info("DoorSecuritySystem: ENABLED")
                self.door_security_active = True
            elif payload["state"] == "disabled":
                logging.info("DoorSecuritySystem: DISABLED")
                self.door_security_active = False
            else:
                logging.fatal(f"Unknown door security state received: {payload['state']}")
        else:
            logging.warning(f"Unknown topic: {message.topic}")

    def _publish_alarm(self, reason, extra, state="enabled"):
        self.mqtt_client.publish("AlarmInfo", json.dumps({
            "time": datetime.utcnow().isoformat() + "Z",
            "runs_on": "TODO",  # TODO: add runs_on
            "reason": reason,
            "extra": extra,
            "state": state
        }), 2, True)

    def _publish_door_security(self, state="enabled"):
        self.mqtt_client.publish("DoorSecuritySystem", json.dumps({
            "time": datetime.utcnow().isoformat() + "Z",
            "runs_on": "TODO",  # TODO: add runs_on
            "state": state
        }), 2, True)

    def _publish_people_change(self, incrementing):
        if datetime.now() - self.last_people_publish < timedelta(seconds=15):
            return
        self.last_people_publish = datetime.now()
        self.mqtt_client.publish("PeopleDetection", json.dumps({
            "time": datetime.utcnow().isoformat() + "Z",
            "runs_on": "TODO",  # TODO: add runs_on
            "incrementing": incrementing,
        }), 2, True)

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
            self._check_gyro()
            self._check_uds()
            self._check_dpir()
            self._check_rpir()
            if not self.alarm_active and self.door_security_active:
                self._check_button_high_alert()
            if self.alarm_active:
                # TODO: also display on curse ui
                self._buzz_all()
            if not self.alarm_active and self.wakeup_alert_active:
                # TODO: also display on curse ui
                # blinking is activated/deactivated in processing message, since it is state
                self._buzz_bedroom()

    def _check_dpir(self):
        try:
            self.dpir_queue.get(timeout=0.03)
        except Empty:
            return
        # if too little values, wait a bit longer
        if len(self.uds_distances) <= 5:
            return
        movement = self.uds_distances[-1] - self.uds_distances[0]
        # TODO: experiment with movement numbers
        if movement < -10:
            logging.info("Sending person entering...")
            self._publish_people_change(True)
        elif movement > 10:
            logging.info("Sending person exiting...")
            self._publish_people_change(False)
        else:
            logging.warning("There was quite a bit of movement, but somehow not entering or exiting")

    def _check_rpir(self):
        try:
            code = self.rpir_queue.get(timeout=0.03)
        except Empty:
            return
        if not self.alarm_active and self.person_count == 0:
            logging.info(f"Alarm activating due to RPIR: {code}...")
            self._publish_alarm("RPIR", f"No people present, but RPIR: {code} detected someone")

    def _check_uds(self):
        # FIXME: this expects only one uds per pi, should work for our examples
        try:
            distance = self.uds_queue.get(timeout=0.03)
        except Empty:
            return
        self.uds_distances.append(distance)  # TODO: do i need datetime for better calcs?
        self.uds_distances = self.uds_distances[-32:]

    def _calculate_gyro_movement(self):
        # assuming every gyro comes in similar deltas
        delta_seconds = ((self.gyro_intensities[-1][0] - self.gyro_intensities[0][0]).total_seconds() /
                         len(self.gyro_intensities))
        return sum(delta_seconds * delta_seconds * intensity for _, intensity in self.gyro_intensities)

    def _check_gyro(self):
        # FIXME: this expects only one gyro per pi, should work for our examples
        try:
            # expects gyro xyz values
            values = self.gyro_queue.get(timeout=0.03)
        except Empty:
            return
        intensity = calculate_intensity(values)
        self.gyro_intensities.append((datetime.utcnow(), intensity))
        self.gyro_intensities = self.gyro_intensities[-16:]
        # if too little values, wait a bit longer
        if len(self.gyro_intensities) <= 4:
            return
        movement = self._calculate_gyro_movement()
        # TODO: experiment with movement numbers
        if not self.alarm_active and movement > 20:
            logging.info("Alarm activating due to GYRO...")
            self._publish_alarm("GYRO", "Gyro safe moved too much")

    def _check_button(self):
        # FIXME: this expects only one button per pi, should work for our examples
        try:
            newly_pushed_in = self.btn_queue.get(timeout=0.03)
            if self.btn_pushed_in and not newly_pushed_in:
                self.btn_pushed_in = False
                self.when_btn_released = datetime.now()
        except Empty:
            newly_pushed_in = None
        if (not self.alarm_active and
                not self.btn_pushed_in and datetime.now() - self.when_btn_released >= timedelta(seconds=5)):
            logging.info("Alarm activating due to DS...")
            self.alarm_activated_by_btn = True
            self._publish_alarm("DS", "Door sensor released for longer than 5 seconds")
        if newly_pushed_in is not None:
            self.btn_pushed_in = newly_pushed_in
        if self.alarm_activated_by_btn and self.alarm_active and self.btn_pushed_in:
            self.alarm_activated_by_btn = False
            self._publish_alarm("AfterDS", "Door sensor pushed in after alarm caused by DS",
                                "disabled")

    def _check_button_high_alert(self):
        # FIXME: this expects only one button per pi, should work for our examples
        if not self.btn_pushed_in:
            logging.info("Alarm activating due to DS while Security system active...")
            self._publish_alarm("SecDS", "Door sensor not pushed in while security system active")

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
            if not self.door_security_active:
                logging.info("MBR security system toggling in 10 seconds: ON")
                self.door_security_timer = threading.Timer(10, lambda: self._publish_door_security("enabled"))
                self.door_security_timer.start()
            else:
                logging.info("MBR security system toggled: OFF")
                # TODO: potential weird behavior if somehow user enters password right when published enabled?
                if self.door_security_timer:
                    self.door_security_timer.cancel()  # should be safe to cancel even when finished
                    self.door_security_timer = None
                self._publish_door_security("disabled")
        elif password == self.alarm_password and self.alarm_active:
            logging.info("Disabling alarm...")
            self._publish_alarm("MBR", "Deactivated by password", "disabled")
        else:
            logging.info("Wrong password attempted!")

    def attach_abz(self, abz_queue, bedroom=False):
        if bedroom:
            self.bedroom_abz_queue = abz_queue
        self.abz_queues.append(abz_queue)

    def _buzz_all(self):
        buzz = {"pitch": 440, "duration": 1.0}
        for abz_queue in self.abz_queues:
            abz_queue.put(buzz)

    def _buzz_bedroom(self):
        if not self.bedroom_abz_queue:
            return
        buzz = {"pitch": 440, "duration": 1.0}
        self.bedroom_abz_queue.put(buzz)
