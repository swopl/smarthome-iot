import threading
from queue import LifoQueue, Queue
from exterior_interacting.alarmcommander import AlarmCommander
from components.abz import ABZComponent
from components.btn import BTNComponent
from components.d47seg import D47SEGComponent
from components.dht import DHTComponent
from components.gyro import GyroComponent
from components.ir_receiver import IRReceiverComponent
from components.lcd import LCDComponent
from components.led import LEDComponent
from components.mbr import MBRComponent
from components.pir import PIRComponent
from exterior_interacting.publisher.publisher_dict import PublisherDict
from components.rgb import RGBComponent
from components.uds import UDSComponent
from curse.commander import CurseCommandBuilder
from curse.curseui import CurseUI


class CurseUIBuilder:
    def __init__(self, running_pi):
        self.command_builder = CurseCommandBuilder()
        self.row_templates = {}
        self.display_queues = {}
        self.command_queues = {}
        self.stop_event = threading.Event()
        self.publishers = PublisherDict()
        self.running_pi = running_pi
        self.alarm_commander = AlarmCommander(self.stop_event)

    def build(self):
        return (CurseUI(self.display_queues, self.row_templates, self.command_queues,
                        self.command_builder, self.running_pi),
                self.stop_event)

    def add_dht(self, key, component_settings, command_queues=()):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        # TODO: .4 and .5 hum temp precision, but sometimes send int sometimes float
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Status: {value_code:17} Humidity: "
                                   "{humidity:> 6} and Temperature: {temperature:> 7}")
        return DHTComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.publishers[component_settings["type"]], command_queues)

    def add_pir(self, key, component_settings, led_command_queue=None):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Motion detected")
        door_pir = component_settings["codename"].startswith("D")  # We will assume others are Room pirs
        return PIRComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.publishers[component_settings["type"]],
                            self.alarm_commander.dpir_queue if door_pir else self.alarm_commander.rpir_queue,
                            led_command_queue)

    def add_ir_receiver(self, key, component_settings, rgb_command_queue):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | IR Received {message:>6}")
        return IRReceiverComponent(self.display_queues[key], component_settings, self.stop_event,
                                   self.publishers[component_settings["type"]],
                                   rgb_command_queue)

    def add_btn(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Button pushed in: {on_off}")
        return BTNComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.publishers[component_settings["type"]], self.alarm_commander.btn_queue)

    def add_mbr(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Keys: {keys}")
        alarm_mbr_key = "_ALARM_FROM_MBR"
        self.command_queues[alarm_mbr_key] = self.alarm_commander.mbr_queue
        self.command_builder.add_mbr_alarm(alarm_mbr_key)
        return MBRComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.publishers[component_settings["type"]], self.alarm_commander.mbr_queue)

    def add_uds(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        # TODO: .5 precision, but check if can do it
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Distance: {distance:> 7}")
        return UDSComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.publishers[component_settings["type"]], self.alarm_commander.uds_queue)

    def add_led(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        # FIXME: these that take commands should probably be regular queues, possible error when real world
        # FIXME: why did this use to be LifoQueue??
        self.command_queues[key] = Queue()
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Light is {onoff}")
        self.command_builder.add_led(key)
        return LEDComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.command_queues[key])

    def add_abz(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        self.command_queues[key] = Queue()
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Buzzer {buzz}")
        self.command_builder.add_abz(key)
        bedroom = component_settings["codename"].startswith("B")  # We will assume others are not in bedroom
        self.alarm_commander.attach_abz(self.command_queues[key], bedroom)
        return ABZComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.command_queues[key])

    def add_rgb(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        self.command_queues[key] = Queue()
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | RGB colors: {color}")
        self.command_builder.add_rgb(key)
        return RGBComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.command_queues[key])

    def add_gyro(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        # TODO: check if precision allowed, if real can sometimes not be float
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | Acceleration (g): {acceleration:>24} "
                                   "Rotation (d/s): {rotation:>24}")
        return GyroComponent(self.display_queues[key], component_settings, self.stop_event,
                             self.publishers[component_settings["type"]], self.alarm_commander.gyro_queue)

    def add_d47seg(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        # TODO: check if precision allowed, if real can sometimes not be float
        self.row_templates[key] = (int(component_settings["row"]), "{code:10} at {timestamp} | Time: {time_4d}")
        return D47SEGComponent(self.display_queues[key], component_settings, self.stop_event,
                               self.alarm_commander.d47seg_blinking_queue)

    def add_lcd(self, key, component_settings):
        self.display_queues[key] = LifoQueue()
        component_settings["runs_on"] = f"PI{self.running_pi}"
        self.command_queues[key] = Queue()
        self.row_templates[key] = (int(component_settings["row"]),
                                   "{code:10} at {timestamp} | LCD message: {message}")
        return LCDComponent(self.display_queues[key], component_settings, self.stop_event,
                            self.command_queues[key])
