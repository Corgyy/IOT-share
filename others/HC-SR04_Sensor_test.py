from machine import Pin, time_pulse_us
import utime

TRIG = Pin(3, Pin.OUT)
ECHO = Pin(2, Pin.IN)

def do_measure():
    TRIG.low()
    utime.sleep_us(2)
    TRIG.high()
    utime.sleep_us(10)
    TRIG.low()

    duration = time_pulse_us(ECHO, 1, 30000)  # Timeout 30ms
    distance = duration * 0.0343 / 2  # Tốc độ âm thanh ~343m/s

    return distance

while True:
    d = do_measure()
    print("Khoảng cách: {:.2f} cm".format(d))
    utime.sleep(1)
