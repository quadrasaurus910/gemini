import network
import uasyncio as asyncio
import machine
import utime
import gc

# --- WiFi Setup ---
SSID = 'YOUR_WIFI_NAME'
PASSWORD = 'YOUR_WIFI_PASSWORD'

# --- Hardware Setup ---
pwm_r = machine.PWM(machine.Pin(16))
pwm_g = machine.PWM(machine.Pin(17))
pwm_b = machine.PWM(machine.Pin(18))

for p in [pwm_r, pwm_g, pwm_b]:
    p.freq(1000)

COMMON_ANODE = True 

def set_rgb(r, g, b):
    r = min(255, max(0, int(r)))
    g = min(255, max(0, int(g)))
    b = min(255, max(0, int(b)))
    if COMMON_ANODE:
        pwm_r.duty_u16(65535 - (r * 257))
        pwm_g.duty_u16(65535 - (g * 257))
        pwm_b.duty_u16(65535 - (b * 257))
    else:
        pwm_r.duty_u16(r * 257)
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)

set_rgb(0, 0, 0) # Start off

# --- Multi-User Lock System ---
active_ip = None
last_action_time = 0
TIMEOUT_MS = 2000 # 2 seconds of silence unlocks the hardware

async def handle_client(reader, writer):
    global active_ip, last_action_time
    
    # Get the IP address of the user who just connected
    addr = writer.get_extra_info('peername')
    client_ip = addr[0]
    
    try:
        request_line = await reader.readline()
        if not request_line:
            writer.close()
            await writer.wait_closed()
            return
        
        req_str = request_line.decode('utf-8')
        
        # Flush the remaining HTTP headers from the buffer
        while True:
            h = await reader.readline()
            if not h or h == b'\r\n':
                break
        
        # ROUTE 1: The user wants the webpage
        if "GET / " in req_str or "GET /index.html" in req_str:
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            try:
                # Read the file from the Pico's storage and send it!
                with open("index.html", "r") as f:
                    while True:
                        chunk = f.read(1024)
                        if not chunk: break
                        writer.write(chunk.encode('utf-8'))
                        await writer.drain()
            except OSError:
                writer.write(b"<html><body><h1>ERROR: index.html not found on Pico!</h1></body></html>")
                
        # ROUTE 2: The user is trying to stream LED data
        elif "GET /?data=RGB:" in req_str:
            current_time = utime.ticks_ms()
            
            # Check if someone else owns the lock right now
            if active_ip is not None and active_ip != client_ip:
                if utime.ticks_diff(current_time, last_action_time) < TIMEOUT_MS:
                    # REJECTED: Send HTTP 423 (Locked) back to the phone
                    writer.write(b"HTTP/1.1 423 Locked\r\n\r\nBUSY")
                    writer.close()
                    await writer.wait_closed()
                    return
            
            # ACCEPTED: Lock the hardware to this user's IP
            active_ip = client_ip
            last_action_time = current_time
            
            # Parse the RGB string and drive the LED
            try:
                data_start = req_str.find("RGB:") + 4
                data_end = req_str.find(" HTTP", data_start)
                r, g, b = req_str[data_start:data_end].split(',')
                set_rgb(int(r), int(g), int(b))
                
                writer.write(b"HTTP/1.1 200 OK\r\n\r\nOK")
            except Exception as e:
                pass # Ignore malformed packets
                
        else:
            writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n404")

    except Exception as e:
        print("Network Error:", e)
    finally:
        writer.close()
        await writer.wait_closed()
        gc.collect()

# --- Main Boot Sequence ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting to WiFi...")
    while not wlan.isconnected():
        utime.sleep(0.5)
        print(".", end="")
    print(f"\nConnected! Go to: http://{wlan.ifconfig()[0]}")

async def main():
    connect_wifi()
    print("Starting Async Web Server...")
    # Start the server on port 80
    asyncio.create_task(asyncio.start_server(handle_client, '0.0.0.0', 80))
    
    # The main loop stays empty for now. Later, we can put your LCD/Menu code here!
    while True:
        await asyncio.sleep(1)

# Run the async loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server stopped.")
