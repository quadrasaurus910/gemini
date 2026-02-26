import time
import math
import tracemalloc
from gpiozero import RGBLED

# Initialize the RGB LED with your specific GPIO pins
led = RGBLED(red=17, green=18, blue=27)

# Start tracing Python memory allocation
tracemalloc.start()

# Print the header for our cleanly formatted readout
print(f"{'Time (s)':<10} | {'Blue Intensity':<15} | {'Current Mem (B)':<18} | {'Peak Mem (B)':<15}")
print("-" * 65)

start_time = time.time()

try:
    while True:
        # 1. Calculate elapsed time
        t = time.time() - start_time
        
        # 2. Famous Formula: Adjusted Sine Wave for smooth gradient
        blue_intensity = (math.sin(t) + 1) / 2
        
        # 3. Apply to LED (Red and Green remain 0, Blue gets the gradient)
        led.value = (0, 0, blue_intensity)
        
        # 4. Fetch memory allocation data
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        
        # 5. Formatted readout: 
        # <10.2f means left-aligned, 10 spaces wide, 2 decimal places.
        # <18,d means left-aligned, 18 spaces wide, comma-separated integers.
        print(f"{t:<10.2f} | {blue_intensity:<15.4f} | {current_mem:<18,d} | {peak_mem:<15,d}")
        
        # Small delay to keep the terminal readable and prevent CPU pegging
        time.sleep(0.05)

except KeyboardInterrupt:
    # Clean up nicely when you press Ctrl+C
    print("\nGradient stopped. Cleaning up GPIO and Memory Tracer...")
    led.close()
    tracemalloc.stop()
