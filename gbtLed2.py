import machine, time, random

--- Pin setup (adjust to your wiring) ---
PIN_R = 15
PIN_G = 14
PIN_B = 13

Setup PWM for each channel
R = machine.PWM(machine.Pin(PIN_R))
G = machine.PWM(machine.Pin(PIN_G))
B = machine.PWM(machine.Pin(PIN_B))

for ch in (R, G, B):
    ch.freq(1000)

def set_rgb(r, g, b):
    """
    Set RGB values (0–255 each) for a common-anode LED.
    0 = off, 255 = full brightness.
    """
    # Invert because it's common-anode
    R.duty_u16(65535 - (r * 257))
    G.duty_u16(65535 - (g * 257))
    B.duty_u16(65535 - (b * 257))

def random_rgb(interval=10):
    """
    Show a new random color every interval seconds.
    """
    while True:
        r = random.getrandbits(8)
        g = random.getrandbits(8)
        b = random.getrandbits(8)
        set_rgb(r, g, b)
        print(f"New color -> R:{r} G:{g} B:{b}")
        time.sleep(interval)
