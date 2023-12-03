from simulators.uds import run_uds_simulator
import threading
import time
import logging


def uds_callback(code, distance):
    t = time.localtime()
    print("= " * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Distance: {distance}")


def run_uds(settings, threads, stop_event):
    if settings['simulated']:
        logging.debug(f"Starting {settings['codename']} simulator")
        uds_thread = threading.Thread(target=run_uds_simulator,
                                      args=(uds_callback, stop_event, settings['codename']))
        uds_thread.start()
        threads.append(uds_thread)
        logging.debug(f"{settings['codename']} simulator started")
    else:
        from sensors.uds import run_uds_loop, UDS
        logging.debug(f"Starting {settings['codename']} loop")
        uds = UDS(settings['trig_pin'], settings['echo_pin'], settings['codename'], uds_callback)
        uds_thread = threading.Thread(target=run_uds_loop, args=(uds, stop_event))
        uds_thread.start()
        threads.append(uds_thread)
        logging.debug(f"{settings['codename']} loop started")
