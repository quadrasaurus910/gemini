import utime
from machine import Pin, PWM

# --- SETUP: Adjust these pin numbers to match your RGB LED's connections. ---
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
WHITE_DIM = (100, 100, 100)
WHITE_BRIGHT = (255, 255, 255)
AMBER_DIM = (128, 128, 0)
AMBER_BRIGHT = (255, 255, 0)
CYAN_DIM = (0, 128, 128)
CYAN_BRIGHT = (0, 255, 255)

# --- SMART STROBE SHOWCASE ---
def showcase_smart_strobe_patterns():
    
    # Pattern 1: "Breathing" Pulse - AMBER
    print("Effect 1: 'Breathing' Pulse - AMBER")
    for _ in range(3):
        # Fade in from dim to mid-range
        for i in range(100):
            r = int(AMBER_DIM[0] + (AMBER_BRIGHT[0] - AMBER_DIM[0]) * (i / 100.0))
            g = int(AMBER_DIM[1] + (AMBER_BRIGHT[1] - AMBER_DIM[1]) * (i / 100.0))
            set_rgb(r, g, AMBER_DIM[2])
            utime.sleep_ms(10)
        
        # Quick, bright flash at the peak
        set_rgb(*AMBER_BRIGHT)
        utime.sleep_ms(50)
        
        # Fade back out
        for i in range(100, -1, -1):
            r = int(AMBER_DIM[0] + (AMBER_BRIGHT[0] - AMBER_DIM[0]) * (i / 100.0))
            g = int(AMBER_DIM[1] + (AMBER_BRIGHT[1] - AMBER_DIM[1]) * (i / 100.0))
            set_rgb(r, g, AMBER_DIM[2])
            utime.sleep_ms(10)

    utime.sleep(1)

    # Pattern 2: "Anticipation" Grouping - WHITE
    print("Effect 2: 'Anticipation' Grouping - WHITE")
    for _ in range(2):
        set_rgb(*WHITE_DIM)
        utime.sleep(1) # Baseline
        
        # Progression of pulses
        for i in range(1, 4):
            # Mid-range pulse
            r, g, b = (int(WHITE_DIM[0] * (1.0 + 0.2*i)), 
                       int(WHITE_DIM[1] * (1.0 + 0.2*i)), 
                       int(WHITE_DIM[2] * (1.0 + 0.2*i)))
            set_rgb(r, g, b)
            utime.sleep_ms(100)
            set_rgb(*WHITE_DIM)
            utime.sleep_ms(100)
        
        # Final bright pulse
        set_rgb(*WHITE_BRIGHT)
        utime.sleep_ms(150)
        set_rgb(*WHITE_DIM)
        utime.sleep_ms(500)

    utime.sleep(1)

    # Pattern 3: "Scanning" with Alert - CYAN
    print("Effect 3: 'Scanning' with Alert - CYAN")
    for _ in range(5):
        # Smooth transition to a bright flash
        for i in range(100):
            r = int(CYAN_DIM[0] + (CYAN_BRIGHT[0] - CYAN_DIM[0]) * (i / 100.0))
            g = int(CYAN_DIM[1] + (CYAN_BRIGHT[1] - CYAN_DIM[1]) * (i / 100.0))
            b = int(CYAN_DIM[2] + (CYAN_BRIGHT[2] - CYAN_DIM[2]) * (i / 100.0))
            set_rgb(r, g, b)
            utime.sleep_ms(5)
        
        # Quick Alert Flash
        set_rgb(*CYAN_BRIGHT)
        utime.sleep_ms(50)
        
        # Fade back out
        for i in range(100, -1, -1):
            r = int(CYAN_DIM[0] + (CYAN_BRIGHT[0] - CYAN_DIM[0]) * (i / 100.0))
            g = int(CYAN_DIM[1] + (CYAN_BRIGHT[1] - CYAN_DIM[1]) * (i / 100.0))
            b = int(CYAN_DIM[2] + (CYAN_BRIGHT[2] - CYAN_DIM[2]) * (i / 100.0))
            set_rgb(r, g, b)
            utime.sleep_ms(5)

    utime.sleep(1)

    set_rgb(*OFF)
    print("All smart patterns finished.")

# --- MAIN LOOP ---
while True:
    showcase_smart_strobe_patterns()
    utime.sleep(3)
