from simulators.mbr import run_mbr_simulator
import threading
import time
import logging


def mbr_callback(code, message):
    t = time.localtime()
    print("= " * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Keys: {message}")


def run_mbr(settings, threads, stop_event):
    if settings['simulated']:
        logging.debug(f"Starting {settings['codename']} simulator")
        mbr_thread = threading.Thread(target=run_mbr_simulator,
                                      args=(mbr_callback, stop_event, settings['codename']))
        mbr_thread.start()
        threads.append(mbr_thread)
        logging.debug(f"{settings['codename']} simulator started")
    else:
        from sensors.mbr import run_mbr_loop, MBR
        logging.debug(f"Starting {settings['codename']} loop")
        # TODO: check if this is passed correctly
        mbr = MBR(settings['R'], settings['C'], settings['codename'], mbr_callback)
        mbr_thread = threading.Thread(target=run_mbr_loop, args=(mbr, stop_event))
        mbr_thread.start()
        threads.append(mbr_thread)
        logging.debug(f"{settings['codename']} loop started")
