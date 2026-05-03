import utime
import math
import machine
import gc

# Hardware Setup (Common Anode: 0 is full brightness, 65535 is off)
red = machine.PWM(machine.Pin(18)) # Replace with your actual pins
green = machine.PWM(machine.Pin(19))
blue = machine.PWM(machine.Pin(20))
for p in [red, green, blue]: p.freq(1000)

def set_led(r, g, b):
    # Invert values for Common Anode
    red.duty_u16(65535 - int(r))
    green.duty_u16(65535 - int(g))
    blue.duty_u16(65535 - int(b))

def cosmic_scan(joy_x_pin):
    """Simulates mirror polishing and infrared-to-visible discovery."""
    t = 0
    while True:
        # Check for joystick left (exit logic)[span_1](start_span)[span_1](end_span)[span_2](start_span)[span_2](end_span)
        if joy_x_pin.read_u16() < 20000:
            set_led(0, 0, 0)
            return

        # Breathing effect for 'polishing' clarity
        brightness = (math.sin(t) + 1) / 2 
        
        # Shift from Infrared (Deep Red) to Stellar White
        # At low 't', it's mostly red; as polishing 'clears', white emerges
        r_val = 30000 + (35535 * brightness)
        g_val = 20000 * brightness
        b_val = 40000 * brightness
        
        # Add a 'twinkle' effect (Fresnel focus)
        if t % 10 > 9.5:
            set_led(65535, 65535, 65535) # Focused flash
            utime.sleep_ms(20)

        set_led(r_val, g_val, b_val)
        
        t += 0.05
        utime.sleep_ms(30)
        gc.collect()
