import threading
import sensors.gyro.MPU6050 as MPU6050
import time


class Gyro:
    # assuming I2C pins here
    def __init__(self, code, callback):
        self.code = code
        self.callback = callback
        self.mpu = None

    def setup(self):
        self.mpu = MPU6050.MPU6050()  # instantiate a MPU6050 class object
        self.mpu.dmp_initialize()  # initialize MPU6050

    def loop(self, stop_event):
        while True:
            if stop_event.is_set():
                self.stop()
                break
            accel, gyro = self.do_reading()
            self.callback(self.code, accel, gyro)
            time.sleep(0.1)

    def do_reading(self):
        accel = self.mpu.get_acceleration()  # get accelerometer data
        gyro = self.mpu.get_rotation()  # get gyroscope data
        # units should be g for accel and degree/second for gyro
        return ((accel[0] / 16384.0, accel[1] / 16384.0, accel[2] / 16384.0),
                (gyro[0] / 131.0, gyro[1] / 131.0, gyro[2] / 131.0))

    def stop(self):
        pass


def run_gyro_loop(gyro: Gyro, stop_event: threading.Event):
    gyro.setup()
    gyro.loop(stop_event)
