import threading
import time
import curses

from components.btn import run_btn
from components.mbr import run_mbr
from components.uds import run_uds
from settings import load_settings
from components.dht import run_dht
from components.pir import run_pir

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


def main(stdscr):
    stdscr.clear()
    # This raises ZeroDivisionError when i == 10.
    for i in range(0, 9):
        v = i-10
        stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))
    stdscr.refresh()
    key = stdscr.getkey()


def main2():
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    try:
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
        run_btn(ds1_settings, threads, stop_event)

        dms_settings = settings['DMS']
        run_mbr(dms_settings, threads, stop_event)

        dus1_settings = settings['DUS1']
        run_uds(dus1_settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass


if __name__ == "__main__":
    main2()
    # curses.wrapper(main)
