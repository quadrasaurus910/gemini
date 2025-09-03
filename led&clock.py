import time
import network
import ntptime
import random
from machine import Pin, I2C, PWM
from lcd_i2c import I2cLcd

# --- User-configurable variables ---
# WiFi credentials for time sync. Update these with your network's details.
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# I2C pins for LCD1602
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

# RGB LED pins. Ensure these are correct for your setup.
R_PIN = 16
G_PIN = 17
B_PIN = 18

# --- Hardware Initialization ---
# RGB LED (Common Anode logic: on=0, off=65535)
pwm_r = PWM(Pin(R_PIN))
pwm_g = PWM(Pin(G_PIN))
pwm_b = PWM(Pin(B_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

def set_rgb_color(r, g, b):
    # Convert 0-255 values to 65535-0 PWM duty cycles for common anode
    pwm_r.duty_u16(65535 - int(r * 65535 / 255))
    pwm_g.duty_u16(65535 - int(g * 65535 / 255))
    pwm_b.duty_u16(65535 - int(b * 65535 / 255))

# LCD1602 Display
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400000)
# Most common I2C address for this display is 0x27 or 0x3f
devices = i2c.scan()
if len(devices) == 0:
    raise RuntimeError("No I2C devices found. Check connections.")
lcd_address = devices[0]
lcd = I2cLcd(i2c, lcd_address, 2, 16)

# --- Network and Time Sync ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to network...")
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

max_attempts = 10
for i in range(max_attempts):
    if wlan.isconnected():
        print("Connected to WiFi!")
        try:
            ntptime.settime()  # Sync time with NTP server
            print("Time synced.")
            break
        except OSError:
            print("Failed to sync time.")
    else:
        print(f"Attempt {i+1}/{max_attempts}...")
        time.sleep(1)

if not wlan.isconnected():
    print("Could not connect to WiFi. Using fallback time.")
    
# --- Main Program Loop ---
while True:
    # 1. Update RGB LED with a new random color
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    set_rgb_color(r, g, b)
    
    # 2. Update LCD with current time and date
    current_time = time.localtime()
    hour = current_time[3]
    minute = current_time[4]
    second = current_time[5]
    
    # Format the time (HH:MM:SS)
    time_string = f"{hour:02d}:{minute:02d}:{second:02d}"
    
    # Format the date (YYYY-MM-DD)
    date_string = f"{current_time[0]}-{current_time[1]:02d}-{current_time[2]:02d}"

    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(time_string)
    lcd.move_to(0, 1)
    lcd.putstr(date_string)

    time.sleep(1) # Wait 1 second before the next loop
