from simulators.btn import run_btn_simulator
import threading
import time
import logging


def btn_callback(code, message):
    t = time.localtime()
    print("= " * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Message: {message}")


def run_btn(settings, threads, stop_event):
    if settings['simulated']:
        logging.debug(f"Starting {settings['codename']} simulator")
        pir_thread = threading.Thread(target=run_btn_simulator,
                                      args=(btn_callback, stop_event, settings['codename']))
        pir_thread.start()
        threads.append(pir_thread)
        logging.debug(f"{settings['codename']} simulator started")
    else:
        from sensors.btn import run_btn_loop, BTN
        logging.debug(f"Starting {settings['codename']} loop")
        btn = BTN(settings['pin'], settings['codename'], btn_callback)
        btn_thread = threading.Thread(target=run_btn_loop, args=(btn, stop_event))
        btn_thread.start()
        threads.append(btn_thread)
        logging.debug(f"{settings['codename']} loop started")
