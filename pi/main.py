import os.path
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


def init_log():
    t = datetime.now()
    timestamp = t.strftime("%Y-%m-%d-%H%M%S")
    if not os.path.exists("./log"):
        os.makedirs("./log")
    logging.basicConfig(filename=f"./log/iot-{timestamp}.log", level=logging.DEBUG)


def main():
    running_pi = 2
    if len(sys.argv) > 1 and sys.argv[1] in {"1", "2", "3"}:
        running_pi = sys.argv[1]
    init_log()
    logging.debug('Starting app')
    settings = load_settings()[f"PI{running_pi}"]
    threads = []
    ui_builder = CurseUIBuilder(running_pi)
    rgb = None
    lcd = None
    for key, component_settings in settings.items():
        device_type = component_settings["type"]
        if device_type == "DHT":
            if component_settings["codename"] == "GDHT":
                # FIXME: make not dependent on order
                ui_builder.add_dht(key, component_settings,
                                   (lcd.command_queue, )).run(threads)
            else:
                ui_builder.add_dht(key, component_settings).run(threads)
        elif device_type == "PIR":
            ui_builder.add_pir(key, component_settings).run(threads)
        elif device_type == "IR_RECEIVER":
            ui_builder.add_ir_receiver(key, component_settings, rgb.command_queue).run(threads)
        elif device_type == "BTN":
            ui_builder.add_btn(key, component_settings).run(threads)
        elif device_type == "MBR":
            ui_builder.add_mbr(key, component_settings).run(threads)
        elif device_type == "UDS":
            ui_builder.add_uds(key, component_settings).run(threads)
        elif device_type == "LED":
            ui_builder.add_led(key, component_settings).run(threads)
        elif device_type == "RGB":
            rgb = ui_builder.add_rgb(key, component_settings)
            rgb.run(threads)
        elif device_type == "ABZ":
            ui_builder.add_abz(key, component_settings).run(threads)
        elif device_type == "GYRO":
            ui_builder.add_gyro(key, component_settings).run(threads)
        elif device_type == "D47SEG":
            ui_builder.add_d47seg(key, component_settings).run(threads)
        elif device_type == "LCD":
            lcd = ui_builder.add_lcd(key, component_settings)
            lcd.run(threads)
        logging.info(f"Success loading component: {key}")

    threads.append(ui_builder.alarm_commander.activate())
    ui, stop_event = ui_builder.build()
    try:
        ui.draw_loop()
    except KeyboardInterrupt:
        print("Stopping app")
        logging.debug('Stopping app')
        for t in threads:
            stop_event.set()
        for t in threads:
            logging.debug(f"Stopping thread: {t} {t.ident} {t.name}")
            t.join()
            if t.is_alive():
                logging.warning(f"Thread lived: {t} {t.ident} {t.name}")
    finally:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
