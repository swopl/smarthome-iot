import sys
import threading
import logging

from components.abz import ABZComponent
from components.btn import BTNComponent
from components.component import Component
from components.dht import DHTComponent
from components.led import LEDComponent
from components.mbr import MBRComponent
from components.publisher.publisher_dict import PublisherDict
from components.rgb import RGBComponent
from components.uds import UDSComponent
from settings import load_settings
from components.pir import PIRComponent
from curseui import CurseUI
from queue import LifoQueue, Queue
from datetime import datetime

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
except:
    pass


def check_pin_collision(settings: dict):
    used_pins = []
    for component_setting in settings.values():
        if not component_setting["simulated"] and component_setting["type"] == "MBR":
            used_pins.extend(component_setting['r'])
            used_pins.extend(component_setting['c'])
        elif not component_setting["simulated"] and component_setting["type"] == "UDS":
            used_pins.append(component_setting['trig_pin'])
            used_pins.append(component_setting['echo_pin'])
        elif not component_setting["simulated"]:
            used_pins.append(component_setting['pin'])

    if len(used_pins) != len(set(used_pins)):
        raise Exception("There is a collision within the pins!")


def init_log():
    t = datetime.now()
    timestamp = t.strftime("%Y-%m-%d-%H%M%S")
    logging.basicConfig(filename=f"iot-{timestamp}.log", level=logging.DEBUG)


def main():
    running_pi = 2
    if len(sys.argv) > 1 and sys.argv[1] in {"1", "2", "3"}:
        running_pi = sys.argv[1]
    device_values_to_display = {}
    command_queues = {}
    row_templates = {}
    init_log()
    logging.debug('Starting app')
    settings = load_settings()[f"PI{running_pi}"]
    check_pin_collision(settings)
    threads = []
    stop_event = threading.Event()
    publishers = PublisherDict()
    for key in settings:
        device_values_to_display[key] = LifoQueue()
        settings[key]["runs_on"] = "PI1"
        device_type = settings[key]["type"]
        publisher = publishers[device_type]
        if device_type == "DHT":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Humidity: "
                                  "{humidity:> 6.4} and Temperature: {temperature:> 7.5}")
            dht = DHTComponent(device_values_to_display[key], settings[key], stop_event, publisher)
            dht.run(threads)
        elif device_type == "PIR":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Motion detected")
            pir = PIRComponent(device_values_to_display[key], settings[key], stop_event, publisher)
            pir.run(threads)
        elif device_type == "BTN":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Button pressed")
            btn = BTNComponent(device_values_to_display[key], settings[key], stop_event, publisher)
            btn.run(threads)
        elif device_type == "MBR":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Keys: {keys}")
            mbr = MBRComponent(device_values_to_display[key], settings[key], stop_event, publisher)
            mbr.run(threads)
        elif device_type == "UDS":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Distance: {distance:> 7.5}")
            uds = UDSComponent(device_values_to_display[key], settings[key], stop_event, publisher)
            uds.run(threads)
        elif device_type == "LED":
            # FIXME: these that take commands should probably be regular queues, possible error when real world
            command_queues[key] = LifoQueue()
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Light is {onoff}")
            abz = LEDComponent(device_values_to_display[key], settings[key],
                               stop_event, command_queues[key])
            abz.run(threads)
        elif device_type == "RGB":
            command_queues[key] = Queue()
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | RGB colors: {color}")
            rgb = RGBComponent(device_values_to_display[key], settings[key],
                               stop_event, command_queues[key])
            rgb.run(threads)
        elif device_type == "ABZ":
            # FIXME: these that take commands should probably be regular queues, possible error when real world
            command_queues[key] = LifoQueue()
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Buzzer {buzz}")
            abz = ABZComponent(device_values_to_display[key], settings[key],
                               stop_event, command_queues[key])
            abz.run(threads)
        logging.info(f"Success loading component: {key}")

    logging.debug(f"RowT: {row_templates}")
    ui = CurseUI(device_values_to_display, row_templates, command_queues)
    try:
        ui.draw_loop()
    except KeyboardInterrupt:
        print("Stopping app")
        logging.debug('Stopping app')
        for t in threads:
            stop_event.set()
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
    # curses.wrapper(main2)
