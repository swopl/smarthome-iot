import threading
import time
import logging

from components.btn import BTNComponent
from components.dht import DHTComponent
from components.led import LEDComponent
from components.mbr import MBRComponent
from components.uds import UDSComponent
from settings import load_settings
from components.pir import PIRComponent
from curseui import CurseUI
from queue import LifoQueue

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
except:
    pass


def check_pin_collision(settings):
    used_pins = []
    if not settings['RDHT1']['simulated']:
        used_pins.append(settings['RDHT1']['pin'])
    if not settings['RDHT2']['simulated']:
        used_pins.append(settings['RDHT2']['pin'])

    if not settings['RPIR1']['simulated']:
        used_pins.append(settings['RPIR1']['pin'])
    if not settings['RPIR2']['simulated']:
        used_pins.append(settings['RPIR2']['pin'])
    if not settings['DPIR1']['simulated']:
        used_pins.append(settings['DPIR1']['pin'])

    if not settings['DS1']['simulated']:
        used_pins.append(settings['DS1']['pin'])

    if not settings['DMS']['simulated']:
        used_pins.extend(settings['DMS']['r'])
        used_pins.extend(settings['DMS']['c'])

    if not settings['DUS1']['simulated']:
        used_pins.append(settings['DUS1']['trig_pin'])
        used_pins.append(settings['DUS1']['echo_pin'])
    if len(used_pins) != len(set(used_pins)):
        raise Exception("There is a collision within the pins!")


def init_log():
    t = time.localtime()
    timestamp = time.strftime("%Y-%m-%d-%H%M%S", t)
    logging.basicConfig(filename=f"iot-{timestamp}.log", level=logging.DEBUG)


def main():
    device_values_to_display = {}
    command_queues = {}
    row_templates = {}
    init_log()
    logging.debug('Starting app')
    settings = load_settings()
    check_pin_collision(settings)
    threads = []
    stop_event = threading.Event()
    for key in settings:
        device_values_to_display[key] = LifoQueue()
        if settings[key]["type"] == "DHT":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Humidity: "
                                  "{humidity:> 6.4} and Temperature: {temperature:> 7.5}")
            dht = DHTComponent(device_values_to_display[key], settings[key], stop_event)
            dht.run(threads)
        elif settings[key]["type"] == "PIR":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Motion detected")
            pir = PIRComponent(device_values_to_display[key], settings[key], stop_event)
            pir.run(threads)
        elif settings[key]["type"] == "BTN":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Button pressed")
            btn = BTNComponent(device_values_to_display[key], settings[key], stop_event)
            btn.run(threads)
        elif settings[key]["type"] == "MBR":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Keys: {keys}")
            mbr = MBRComponent(device_values_to_display[key], settings[key], stop_event)
            mbr.run(threads)
        elif settings[key]["type"] == "UDS":
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Distance: {distance:> 7.5}")
            uds = UDSComponent(device_values_to_display[key], settings[key], stop_event)
            uds.run(threads)
        elif settings[key]["type"] == "LED":
            command_queues[key] = LifoQueue()
            row_templates[key] = (int(settings[key]["row"]),
                                  "{code:10} at {timestamp} | Light is {onoff} ")
            led = LEDComponent(device_values_to_display[key], settings[key],
                               stop_event, command_queues[key])
            led.run(threads)
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
