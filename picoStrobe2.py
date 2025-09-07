import machine
import time

# Pin definitions for common anode RGB LED
# Remember: For common anode, we set the pin to low to turn it on
# The 1k resistors should be connected in series with the LED pins
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

# Create PWM objects for each color
pwm_red = machine.PWM(machine.Pin(RED_PIN))
pwm_green = machine.PWM(machine.Pin(GREEN_PIN))
pwm_blue = machine.PWM(machine.Pin(BLUE_PIN))

# Set the PWM frequency
frequency = 1000 # Hz
pwm_red.freq(frequency)
pwm_green.freq(frequency)
pwm_blue.freq(frequency)

def set_color(r, g, b):
    """
    Sets the duty cycle for each color to control brightness.
    For common anode, 0 is max brightness, 65535 is off.
    """
    # Invert the values because 0 is on and 65535 is off
    pwm_red.duty_u16(65535 - r)
    pwm_green.duty_u16(65535 - g)
    pwm_blue.duty_u16(65535 - b)

def strobe_effect():
    """
    Creates a strobe effect with different colors and timing.
    """
    print("Starting strobe effect...")
    
    # Define color patterns with duty cycles and timings
    # Duty cycle values are from 0 (off) to 65535 (full brightness)
    patterns = [
        # Red strobe
        {'color': (65535, 0, 0), 'duration_on': 0.1, 'duration_off': 0.1},
        # Green strobe
        {'color': (0, 65535, 0), 'duration_on': 0.1, 'duration_off': 0.1},
        # Blue strobe
        {'color': (0, 0, 65535), 'duration_on': 0.1, 'duration_off': 0.1},
        # Yellow (Red + Green) strobe with overlap
        {'color': (65535, 65535, 0), 'duration_on': 0.2, 'duration_off': 0.1},
        # Magenta (Red + Blue) strobe
        {'color': (65535, 0, 65535), 'duration_on': 0.15, 'duration_off': 0.15},
        # Cyan (Green + Blue) strobe
        {'color': (0, 65535, 65535), 'duration_on': 0.1, 'duration_off': 0.2},
    ]

    try:
        while True:
            for pattern in patterns:
                # Turn on the specific color combination
                set_color(pattern['color'][0], pattern['color'][1], pattern['color'][2])
                time.sleep(pattern['duration_on'])
                
                # Turn off the LED
                set_color(0, 0, 0)
                time.sleep(pattern['duration_off'])

    except KeyboardInterrupt:
        print("Strobe effect stopped.")
    finally:
        # Clean up by turning off all LEDs
        set_color(0, 0, 0)
        pwm_red.deinit()
        pwm_green.deinit()
        pwm_blue.deinit()

if __name__ == "__main__":
    strobe_effect()
