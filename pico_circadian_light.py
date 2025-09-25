import machine
import time

# Pin assignments for a common anode RGB LED
# Common anode means 0V is on, 255V is off. We invert the values.
PIN_R = 16
PIN_G = 17
PIN_B = 18

# Initialize PWM on the specified pins
pwm_r = machine.PWM(machine.Pin(PIN_R))
pwm_g = machine.PWM(machine.Pin(PIN_G))
pwm_b = machine.PWM(machine.Pin(PIN_B))

# Set PWM frequency (e.g., 1000 Hz)
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

def set_rgb_color(r, g, b):
    # Invert the 0-255 value for common anode
    # MicroPython PWM duty is 0-65535, so we scale the 0-255 range
    duty_r = int((255 - r) / 255 * 65535)
    duty_g = int((255 - g) / 255 * 65535)
    duty_b = int((255 - b) / 255 * 65535)

    pwm_r.duty_u16(duty_r)
    pwm_g.duty_u16(duty_g)
    pwm_b.duty_u16(duty_b)

# Define the end colors for each hour (0-23)
# These tuples represent (R, G, B) values from 0-255
hourly_colors = [
    (100, 0, 150),   # 00:00 - 01:00 (Deep violet)
    (50, 50, 150),   # 01:00 - 02:00 (Blue with a hint of green)
    (150, 0, 50),    # 02:00 - 03:00 (Dark maroon)
    (50, 0, 100),    # 03:00 - 04:00 (Deep violet)
    (20, 20, 100),   # 04:00 - 05:00 (Deep blue)
    (50, 50, 150),   # 05:00 - 06:00 (Lighter blue)
    (100, 100, 200),  # 06:00 - 07:00 (Morning blue)
    (150, 150, 255),  # 07:00 - 08:00 (Light blue, approaching sunrise)
    (255, 150, 0),    # 08:00 - 09:00 (Vibrant orange)
    (255, 200, 50),   # 09:00 - 10:00 (Vibrant yellow-orange)
    (255, 255, 200),  # 10:00 - 11:00 (Washed pale yellow)
    (255, 255, 220),  # 11:00 - 12:00 (Washed pale yellow)
    (255, 255, 250),  # 12:00 - 13:00 (Near white, high sun)
    (255, 255, 230),  # 13:00 - 14:00 (Washed pale yellow)
    (255, 200, 50),   # 14:00 - 15:00 (Vibrant yellow-orange)
    (255, 150, 0),    # 15:00 - 16:00 (Vibrant orange)
    (200, 200, 50),   # 16:00 - 17:00 (Yellow-green)
    (255, 100, 0),    # 17:00 - 18:00 (Orange-pink, sunset)
    (255, 50, 150),   # 18:00 - 19:00 (Pink-purple, sunset)
    (100, 150, 255),  # 19:00 - 20:00 (Lighter cool blue)
    (50, 100, 255),   # 20:00 - 21:00 (Cool blue)
    (0, 50, 150),     # 21:00 - 22:00 (Dark blue)
    (20, 0, 100),     # 22:00 - 23:00 (Violet)
    (5, 0, 50)        # 23:00 - 24:00 (Very dark violet)
]

def main():
    while True:
        # Get the current time from the Pico W's internal clock
        # NOTE: For persistent accuracy, you should set the time using ntp.
        current_time = time.localtime()
        current_hour = current_time[3]
        current_minute = current_time[4]
        current_second = current_time[5]

        # Determine the start and end colors for the current hour's transition
        # The transition from hour 23 to 0 loops back to the beginning of the list
        start_color = hourly_colors[current_hour - 1] if current_hour > 0 else hourly_colors[23]
        end_color = hourly_colors[current_hour]

        # Calculate the interpolation factor based on the time elapsed in the current hour
        # A full hour is 3600 seconds
        total_seconds_in_hour = 3600
        current_seconds_in_hour = (current_minute * 60) + current_second
        interpolation_factor = current_seconds_in_hour / total_seconds_in_hour

        # Linearly interpolate the RGB values for a smooth transition
        current_r = int(start_color[0] + (end_color[0] - start_color[0]) * interpolation_factor)
        current_g = int(start_color[1] + (end_color[1] - start_color[1]) * interpolation_factor)
        current_b = int(start_color[2] + (end_color[2] - start_color[2]) * interpolation_factor)

        # Set the LED color
        set_rgb_color(current_r, current_g, current_b)

        # Wait for the next second to update the color
        time.sleep(1)

# Start the main loop
if __name__ == '__main__':
    main()
