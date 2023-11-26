import threading
from settings import load_settings
from components.dht import run_dht
import time
import curses

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
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()


if __name__ == "__main__":
    main2()
    # curses.wrapper(main)
