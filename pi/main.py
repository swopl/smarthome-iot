import sys
import logging

from curse.curseuibuilder import CurseUIBuilder
from settings import load_settings
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
    init_log()
    logging.debug('Starting app')
    settings = load_settings()[f"PI{running_pi}"]
    check_pin_collision(settings)
    threads = []
    ui_builder = CurseUIBuilder(running_pi)
    for key, component_settings in settings.items():
        device_type = component_settings["type"]
        if device_type == "DHT":
            ui_builder.add_dht(key, component_settings).run(threads)
        elif device_type == "PIR":
            ui_builder.add_pir(key, component_settings).run(threads)
        elif device_type == "BTN":
            ui_builder.add_btn(key, component_settings).run(threads)
        elif device_type == "MBR":
            ui_builder.add_mbr(key, component_settings).run(threads)
        elif device_type == "UDS":
            ui_builder.add_uds(key, component_settings).run(threads)
        elif device_type == "LED":
            ui_builder.add_led(key, component_settings).run(threads)
        elif device_type == "RGB":
            ui_builder.add_rgb(key, component_settings).run(threads)
        elif device_type == "ABZ":
            ui_builder.add_abz(key, component_settings).run(threads)
        logging.info(f"Success loading component: {key}")

    ui, stop_event = ui_builder.build()
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
