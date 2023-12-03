from simulators.dht import run_dht_simulator
import threading
import time
import logging


def dht_callback(humidity, temperature, code):
    t = time.localtime()
    print("= " * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Humidity: {humidity}%")
    print(f"Temperature: {temperature}°C")


def run_dht(settings, threads, stop_event):
    if settings['simulated']:
        logging.debug(f"Starting {settings['codename']} simulator")
        dht_thread = threading.Thread(target=run_dht_simulator,
                                      args=(2, dht_callback, stop_event, settings['codename']))
        dht_thread.start()
        threads.append(dht_thread)
        logging.debug(f"{settings['codename']} simulator started")
    else:
        from sensors.dht import run_dht_loop, DHT
        logging.debug(f"Starting {settings['codename']} loop")
        dht = DHT(settings['pin'])
        dht_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht_callback, stop_event))
        dht_thread.start()
        threads.append(dht_thread)
        logging.debug(f"{settings['codename']} loop started")
