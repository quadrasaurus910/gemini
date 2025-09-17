import utime
from machine import Pin, PWM

# --- SETUP: Adjust these pin numbers to match your RGB LED's connections. ---
# Assuming a common anode RGB LED
PIN_R = 16
PIN_G = 17
PIN_B = 18

led_r = PWM(Pin(PIN_R))
led_g = PWM(Pin(PIN_G))
led_b = PWM(Pin(PIN_B))

PWM_FREQ = 1000
led_r.freq(PWM_FREQ)
led_g.freq(PWM_FREQ)
led_b.freq(PWM_FREQ)

# --- HELPER FUNCTION FOR COMMON ANODE LEDS ---
def set_rgb(r, g, b):
    """
    Sets the color of a common anode RGB LED by inverting the values.
    """
    r_inverted = 255 - max(0, min(255, int(r)))
    g_inverted = 255 - max(0, min(255, int(g)))
    b_inverted = 255 - max(0, min(255, int(b)))
    
    led_r.duty_u16(int(r_inverted / 255 * 65535))
    led_g.duty_u16(int(g_inverted / 255 * 65535))
    led_b.duty_u16(int(b_inverted / 255 * 65535))

# --- COLOR CONSTANTS ---
OFF = (0, 0, 0)
WHITE = (255, 255, 255)
AMBER_DIM = (128, 128, 0)
AMBER_BRIGHT = (255, 255, 0)
RED_DIM = (128, 0, 0)
RED_BRIGHT = (255, 0, 0)
CYAN_DIM = (0, 128, 128)
CYAN_BRIGHT = (0, 255, 255)

# --- PATTERN SHOWCASE FUNCTION ---
def showcase_strobe_patterns():
    """
    Cycles through various strobe patterns and transitions.
    """
    # Pattern 1: Simple slow pulse - AMBER
    print("Pattern 1: Simple slow amber pulse")
    for _ in range(5):
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(250)
        set_rgb(*OFF)
        utime.sleep_ms(250)

    utime.sleep(1)
    
    # Pattern 2: Quick burst - AMBER
    print("Pattern 2: Quick amber burst")
    for _ in range(5):
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(50)
        set_rgb(*OFF)
        utime.sleep_ms(50)
    utime.sleep(1)

    # Pattern 3: Double flash burst - AMBER
    print("Pattern 3: Double flash amber burst")
    for _ in range(3):
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(75)
        set_rgb(*OFF)
        utime.sleep_ms(75)
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(75)
        set_rgb(*OFF)
        utime.sleep_ms(400)
    utime.sleep(1)

    # Pattern 4: Triple flash burst - AMBER
    print("Pattern 4: Triple flash amber burst")
    for _ in range(3):
        for __ in range(3):
            set_rgb(*AMBER_BRIGHT)
            utime.sleep_ms(50)
            set_rgb(*OFF)
            utime.sleep_ms(50)
        utime.sleep_ms(500)
    utime.sleep(1)

    # Pattern 5: Mid-range to bright pulse - AMBER
    print("Pattern 5: Mid-range to bright pulse - AMBER")
    for _ in range(10):
        set_rgb(*AMBER_DIM)
        utime.sleep_ms(100)
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(50)
        set_rgb(*AMBER_DIM)
        utime.sleep_ms(100)
        set_rgb(*OFF)
        utime.sleep_ms(150)
    utime.sleep(1)

    # Pattern 6: Mid-range to bright burst - RED
    print("Pattern 6: Mid-range to bright burst - RED")
    for _ in range(5):
        set_rgb(*RED_DIM)
        utime.sleep_ms(100)
        for __ in range(2):
            set_rgb(*RED_BRIGHT)
            utime.sleep_ms(75)
            set_rgb(*RED_DIM)
            utime.sleep_ms(75)
        set_rgb(*OFF)
        utime.sleep_ms(400)
    utime.sleep(1)

    # Pattern 7: Fast continuous strobe - WHITE
    print("Pattern 7: Fast continuous strobe - WHITE")
    for _ in range(20):
        set_rgb(*WHITE)
        utime.sleep_ms(30)
        set_rgb(*OFF)
        utime.sleep_ms(30)
    utime.sleep(1)

    # Pattern 8: Alternating color strobe - RED & AMBER
    print("Pattern 8: Alternating Red & Amber strobe")
    for _ in range(10):
        set_rgb(*RED_BRIGHT)
        utime.sleep_ms(100)
        set_rgb(*OFF)
        utime.sleep_ms(100)
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(100)
        set_rgb(*OFF)
        utime.sleep_ms(100)
    utime.sleep(1)

    # Pattern 9: Triple flash burst with alternating colors - CYAN & AMBER
    print("Pattern 9: Triple flash alternating burst - CYAN & AMBER")
    for _ in range(3):
        for __ in range(3):
            set_rgb(*CYAN_BRIGHT)
            utime.sleep_ms(50)
            set_rgb(*OFF)
            utime.sleep_ms(50)
        utime.sleep_ms(150)
        for __ in range(3):
            set_rgb(*AMBER_BRIGHT)
            utime.sleep_ms(50)
            set_rgb(*OFF)
            utime.sleep_ms(50)
        utime.sleep_ms(500)
    utime.sleep(1)
    
    # Pattern 10: Fading pulse with color transition - RED to AMBER
    print("Pattern 10: Fading pulse with transition - RED to AMBER")
    for i in range(10):
        # Red pulse
        set_rgb(*RED_BRIGHT)
        utime.sleep_ms(100)
        set_rgb(*OFF)
        utime.sleep_ms(100)
        # Transitioning color
        transition_color = (255, int(i / 10 * 255), 0)
        set_rgb(*transition_color)
        utime.sleep_ms(50)
    utime.sleep(1)
    
    # Pattern 11: Mid-range to brighter pulse with longer off time - CYAN
    print("Pattern 11: Mid-range to brighter pulse - CYAN")
    for _ in range(8):
        set_rgb(*CYAN_DIM)
        utime.sleep_ms(150)
        set_rgb(*CYAN_BRIGHT)
        utime.sleep_ms(75)
        set_rgb(*OFF)
        utime.sleep_ms(500)
    utime.sleep(1)
    
    # Pattern 12: Short pulse, long pause - AMBER
    print("Pattern 12: Short pulse, long pause - AMBER")
    for _ in range(5):
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(50)
        set_rgb(*OFF)
        utime.sleep_ms(1000)
    utime.sleep(1)

    # Pattern 13: Grouped burst with varying speed - WHITE
    print("Pattern 13: Grouped burst with varying speed - WHITE")
    for _ in range(3):
        set_rgb(*WHITE)
        utime.sleep_ms(75)
        set_rgb(*OFF)
        utime.sleep_ms(75)
        set_rgb(*WHITE)
        utime.sleep_ms(50)
        set_rgb(*OFF)
        utime.sleep_ms(50)
        set_rgb(*WHITE)
        utime.sleep_ms(30)
        set_rgb(*OFF)
        utime.sleep_ms(700)
    utime.sleep(1)

    # Pattern 14: Short pulse, long pause - RED
    print("Pattern 14: Short pulse, long pause - RED")
    for _ in range(5):
        set_rgb(*RED_BRIGHT)
        utime.sleep_ms(50)
        set_rgb(*OFF)
        utime.sleep_ms(1000)
    utime.sleep(1)

    # Pattern 15: Triple flash burst - RED
    print("Pattern 15: Triple flash burst - RED")
    for _ in range(3):
        for __ in range(3):
            set_rgb(*RED_BRIGHT)
            utime.sleep_ms(50)
            set_rgb(*OFF)
            utime.sleep_ms(50)
        utime.sleep_ms(500)
    utime.sleep(1)

    set_rgb(*OFF)
    print("All patterns finished.")

# --- MAIN LOOP ---
while True:
    showcase_strobe_patterns()
    utime.sleep(5)
