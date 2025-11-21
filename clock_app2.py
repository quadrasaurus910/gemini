# clock_app.py
# Handles NTP synchronization and Time Display with DST support.

import usocket
import utime
import ustruct
from machine import RTC
import gc
import config # Import config for timezone settings

# --- Configuration ---
NTP_SERVER = "pool.ntp.org"
NTP_DELTA = 2208988800  # 1900-1970 epoch difference
RESYNC_INTERVAL_SECONDS = 60 * 60 * 6 # Sync with internet every 6 hours

# --- Global variables ---
last_sync_time = 0
rtc = RTC()
last_exit_time = 0
DEBOUNCE_DELAY_MS = 500

def get_ntp_time(wlan):
    """Fetches the current time from an NTP server."""
    if not wlan or not wlan.isconnected():
        return None
    
    try:
        addr = usocket.getaddrinfo(NTP_SERVER, 123)[0][-1]
        s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        s.settimeout(2)
        s.sendto(b'\x1b' + 47 * b'\0', addr)
        msg = s.recv(48)
        s.close()
        val = ustruct.unpack_from("!I", msg, 40)[0]
        return val - NTP_DELTA
    except Exception:
        return None

def set_rtc_from_ntp(lcd, wlan):
    """Syncs the Pico's RTC with time from an NTP server."""
    global last_sync_time
    
    # Only display 'Syncing' on the very first sync to avoid disruption
    if last_sync_time == 0:
        lcd.clear()
        lcd.putstr("Syncing Time...")
        
    ntp_timestamp = get_ntp_time(wlan)
    
    if ntp_timestamp:
        # We store UTC in the RTC
        gmt_tuple = utime.gmtime(ntp_timestamp)
        rtc.datetime((gmt_tuple[0], gmt_tuple[1], gmt_tuple[2], gmt_tuple[6],
                      gmt_tuple[3], gmt_tuple[4], gmt_tuple[5], 0))
        last_sync_time = utime.time()
        
        if last_sync_time == 0: # Feedback only on first load
            lcd.clear()
            lcd.putstr("Time Synced!")
            utime.sleep(1)
    else:
        # If sync fails, we just keep going with internal clock
        pass

def check_exit(joy_x_pin):
    """Checks for a joystick left movement to exit."""
    global last_exit_time
    current_time = utime.ticks_ms()
    x_value = joy_x_pin.read_u16()
    
    if x_value < 20000: # Left threshold
        if utime.ticks_diff(current_time, last_exit_time) > DEBOUNCE_DELAY_MS:
            last_exit_time = current_time
            return True
    return False

def is_dst(year, month, day, hour):
    """
    Determines if the given date/time is within US Daylight Saving Time.
    DST starts: 2nd Sunday in March at 2:00 AM
    DST ends: 1st Sunday in November at 2:00 AM
    """
    if month < 3 or month > 11: return False # Jan, Feb, Dec are standard
    if month > 3 and month < 11: return True # Apr-Oct are DST
    
    previous_sunday = day - (utime.localtime(utime.mktime((year, month, day, 0, 0, 0, 0, 0)))[6] + 1) % 7
    
    if month == 3: # March: DST starts 2nd Sunday
        # If day is after the 14th, it's definitely DST.
        # If day is before the 8th, it's definitely Standard.
        # Between 8 and 14, we check the Sunday logic.
        second_sunday = 0
        # Calculate date of 2nd sunday
        # (This is a simplified approximation sufficient for this project)
        # A full calendar calculation is heavy, but we can check simply:
        # In March, the 2nd Sunday is between the 8th and the 14th.
        if day < 8: return False
        if day > 14: return True
        
        # We are in the transition week. 
        # Get the weekday of the current day (0=Mon, 6=Sun)
        t = (year, month, day, hour, 0, 0, 0, 0)
        weekday = utime.localtime(utime.mktime(t))[6]
        
        # If it is Sunday (6)
        if weekday == 6:
            return hour >= 2
        
        # If we passed Sunday already this week?
        # This is getting complex. Let's try the specific formula method:
        
        # Formula to find the day of 2nd Sunday in March:
        # 14 - (1 + year * 5 // 4) % 7
        dst_start_day = 14 - (1 + int(year * 5 / 4)) % 7
        if day > dst_start_day: return True
        if day < dst_start_day: return False
        if day == dst_start_day: return hour >= 2

    if month == 11: # Nov: DST ends 1st Sunday
        # 1st Sunday is between 1st and 7th
        # Formula for 1st Sunday in Nov:
        # 7 - (1 + year * 5 // 4) % 7
        dst_end_day = 7 - (1 + int(year * 5 / 4)) % 7
        if day > dst_end_day: return False
        if day < dst_end_day: return True
        if day == dst_end_day: return hour < 2
        
    return False

def display_time_and_date(lcd):
    """Displays the current local time and date."""
    # 1. Get UTC timestamp
    current_utc = utime.time()
    
    # 2. Get Basic Local (Standard Time) Tuple
    # We use the config offset (e.g., -5 for EST)
    standard_timestamp = current_utc + (config.TIMEZONE_OFFSET_HOURS * 3600)
    t = utime.localtime(standard_timestamp)
    
    # 3. Check DST
    # t = (year, month, day, hour, min, sec, weekday, yearday)
    dst_active = is_dst(t[0], t[1], t[2], t[3])
    
    # 4. Apply DST adjustment if needed
    if dst_active:
        # Add 1 hour (3600 seconds)
        t = utime.localtime(standard_timestamp + 3600)

    year, month, day, hour, minute, second = t[0], t[1], t[2], t[3], t[4], t[5]

    # Format AM/PM
    am_pm = "AM"
    if hour >= 12:
        am_pm = "PM"
    if hour > 12:
        hour -= 12
    if hour == 0:
        hour = 12

    time_str = "{:02d}:{:02d}:{:02d} {}".format(hour, minute, second, am_pm)
    date_str = "{:02d}/{:02d}/{:04d}".format(month, day, year)

    lcd.move_to(0, 0)
    lcd.putstr(time_str)
    lcd.move_to(0, 1)
    lcd.putstr(date_str)

def run_clock_app(lcd, joy_x_pin, wlan):
    """The main entry point for the clock app."""
    global last_sync_time

    lcd.clear()
    
    # Initial sync
    set_rtc_from_ntp(lcd, wlan)
    
    # Force a clear before starting the loop
    lcd.clear()
    
    last_second_display = -1

    while True:
        current_timestamp = utime.time()
        
        # 1. Re-sync with NTP if interval passed
        if current_timestamp - last_sync_time >= RESYNC_INTERVAL_SECONDS:
            set_rtc_from_ntp(lcd, wlan)
            lcd.clear() # Clear after sync message
            last_second_display = -1 # Force refresh

        # 2. Update Display (Non-blocking, only when second changes)
        # We check the current second from the RTC
        # Note: We grab the raw second from UTC to detect change
        current_second = utime.localtime()[5] 
        
        if current_second != last_second_display:
            display_time_and_date(lcd)
            last_second_display = current_second

        # 3. Check Exit
        if check_exit(joy_x_pin):
            lcd.clear()
            lcd.putstr("Back to Menu...")
            utime.sleep(1)
            return

        # 4. Short Sleep
        # Checking every 50ms ensures we never miss a second, 
        # but don't hog the CPU.
        utime.sleep_ms(50) 
