import machine
import time
import random

Assign RGB LED pins (adjust these to match your wiring)
red = machine.Pin(15, machine.Pin.OUT)
green = machine.Pin(14, machine.Pin.OUT)
blue = machine.Pin(13, machine.Pin.OUT)

def random_rgb(interval=10):
    """
    Randomly sets RGB LED values every interval seconds.
    Default is 10 seconds.
    """
    while True:
        r = random.randint(0, 1)
        g = random.randint(0, 1)
        b = random.randint(0, 1)

        red.value(r)
        green.value(g)
        blue.value(b)

        print(f"New color -> R:{r}, G:{g}, B:{b}")
        time.sleep(interval)


def polarity_test():
    for ca in (False, True):
        print("Testing COMMON_ANODE =", ca)
        global COMMON_ANODE
        COMMON_ANODE = ca
        set_rgb(255, 0, 0); time.sleep(1)
        set_rgb(0, 255, 0); time.sleep(1)
        set_rgb(0, 0, 255); time.sleep(1)
        set_rgb(0, 0, 0);   time.sleep(0.5)
