from simulators.pir import run_pir_simulator
import threading
import time
import logging


def pir_callback(code, message):
    t = time.localtime()
    print("= " * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Message: {message}")


def run_pir(settings, threads, stop_event):
    if settings['simulated']:
        logging.debug(f"Starting {settings['codename']} simulator")
        pir_thread = threading.Thread(target=run_pir_simulator,
                                      args=(pir_callback, stop_event, settings['codename']))
        pir_thread.start()
        threads.append(pir_thread)
        logging.debug(f"{settings['codename']} simulator started")
    else:
        from sensors.pir import run_pir_loop, PIR
        logging.debug(f"Starting {settings['codename']} loop")
        pir = PIR(settings['pin'], settings['codename'], pir_callback)
        pir_thread = threading.Thread(target=run_pir_loop, args=(pir, stop_event))
        pir_thread.start()
        threads.append(pir_thread)
        logging.debug(f"{settings['codename']} loop started")
