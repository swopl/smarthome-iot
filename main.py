import threading
import time
import logging

from components.btn import run_btn
from components.mbr import run_mbr
from components.uds import run_uds
from settings import load_settings
from components.dht import run_dht
from components.pir import run_pir
from curseui import CurseUI

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


def main2():
    device_values = {
        "DHT": [],
        "MBR": [],
        "PIR": [],
        "UDS": [],
        "BTN": []
    }
    CurseUI().draw_loop()
    return
    init_log()
    logging.debug('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    try:
        check_pin_collision(settings)
        rdht1_settings = settings['RDHT1']
        run_dht(rdht1_settings, threads, stop_event)
        rdht2_settings = settings['RDHT2']
        run_dht(rdht2_settings, threads, stop_event)

        rpir1_settings = settings['RPIR1']
        run_pir(rpir1_settings, threads, stop_event)
        rpir2_settings = settings['RPIR2']
        run_pir(rpir2_settings, threads, stop_event)
        dpir1_settings = settings['DPIR1']
        run_pir(dpir1_settings, threads, stop_event)

        ds1_settings = settings['DS1']
        run_btn(ds1_settings, threads, stop_event, stdscr)

        dms_settings = settings['DMS']
        run_mbr(dms_settings, threads, stop_event)

        dus1_settings = settings['DUS1']
        run_uds(dus1_settings, threads, stop_event)

        while True:
            key = stdscr.getkey()
            print("YOU PRESSED:", key)
            time.sleep(1)

    except KeyboardInterrupt:
        logging.debug('Stopping app')
        for t in threads:
            stop_event.set()
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass


if __name__ == "__main__":
    main2()
    # curses.wrapper(main2)
