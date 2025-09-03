from machine import Pin, PWM
import time

pwm_red = PWM(Pin(16))
pwm_green = PWM(Pin(17))
pwm_blue = PWM(Pin(18))

pwm_red.freq(1000)
pwm_green.freq(1000)
pwm_blue.freq(1000)

def set_color(r, g, b):
    # We need to map the 0-255 values to the 16-bit PWM duty cycle range (0-65535)
    # The higher the value, the brighter the color.
    pwm_red.duty_u16(int((r / 255) * 65535))
    pwm_green.duty_u16(int((g / 255) * 65535))
    pwm_blue.duty_u16(int((b / 255) * 65535))

print("Starting time-based color sequence...")

while True:
    # Get the current time as a tuple
    current_time = time.localtime()

    # Get the current hour (0-23)
    current_hour = current_time[3]
    print(f"Current hour: {current_hour}")

    # Set the color based on the time of day
    if 6 <= current_hour < 9:
        # Morning / Sunrise (orange-red)
        # R: 255, G: 140, B: 0
        set_color(255, 140, 0)
        print("Sunrise colors...")
    elif 9 <= current_hour < 18:
        # Daytime (cool blue-white)
        # R: 200, G: 220, B: 255
        set_color(200, 220, 255)
        print("Daylight colors...")
    elif 18 <= current_hour < 21:
        # Evening / Sunset (purple-pink)
        # R: 255, G: 105, B: 180
        set_color(255, 105, 180)
        print("Sunset colors...")
    else:
        # Night (deep blue)
        # R: 0, G: 0, B: 128
        set_color(0, 0, 128)
        print("Night colors...")

    # Wait for one minute before checking the time and updating the color again
    time.sleep(60)
