import time
import random
import math
from gpiozero import RGBLED

# --- CONFIGURATION ---
# Using Raspberry Pi 5 Hardware PWM pins for maximum stability
# Red: GPIO 18, Green: GPIO 13, Blue: GPIO 12
led = RGBLED(red=18, green=13, blue=12, frequency=1000)

GAMMA = 2.2  # Standard Gamma for human eye perception

# --- TEST FUNCTIONS ---

def gamma_correction_test(duration=5):
    """
    Compares Linear vs Gamma-corrected fades.
    Demonstrates the difference between mathematical '0-1' and human perception.
    """
    print(f"--- Running Gamma Correction Test ({duration}s) ---")
    print("Fading Red (Linear) vs Green (Gamma Corrected)...")
    
    steps = 100
    for _ in range(2):
        for i in range(steps + 1):
            # Linear conversion (what you were using)
            linear_val = i / steps
            # Gamma conversion (stretches the low-end for smoothness)
            gamma_val = pow(i / steps, GAMMA)
            
            led.color = (linear_val, gamma_val, 0)
            time.sleep(duration / (steps * 2))
            
def quantization_bit_depth_test(bits=3):
    """
    Simulates lower bit-depths (resolution).
    Demonstrates how data sampling/quantization affects 'smooth' analog output.
    """
    levels = pow(2, bits)
    print(f"--- Running Quantization Test: {bits}-bit Depth ({levels} levels) ---")
    
    for _ in range(3):
        for i in range(levels):
            # Quantizing the 0-1 range into specific 'steps'
            val = i / (levels - 1)
            led.color = (0, val, val) # Cyan tones
            time.sleep(0.2)

def frequency_flicker_sweep():
    """
    Sweeps the PWM frequency to find the threshold of perception (Reconstruction).
    Lower frequencies will show visible 'reconstruction jitter' (flicker).
    """
    frequencies = [50, 100, 500, 2000]
    print("--- Running Frequency Sweep ---")
    
    for f in frequencies:
        print(f"Testing Frequency: {f}Hz")
        # Re-initialize frequency on the fly
        led.blue.frequency = f
        led.blue.value = 0.1 # Low brightness shows flicker better
        time.sleep(2)
    led.blue.frequency = 1000 # Reset to default

def analog_wave_reconstruction(samples=64):
    """
    Uses a sine wave to represent an analog signal.
    Tests how sampling interval affects the 'smoothness' of the reconstruction.
    """
    print(f"--- Running Analog Wave Reconstruction ({samples} samples) ---")
    for i in range(samples):
        # Generate a sine wave scaled to 0-1
        # Represents taking an analog signal and outputting it digitally
        val = (math.sin(2 * math.pi * i / samples) + 1) / 2
        led.color = (val, 0, val) # Magenta pulse
        time.sleep(0.05)

def binary_memory_burst(num_bits=24):
    """
    Represents raw binary data in memory. 
    Interprets a 24-bit integer as 3x8-bit color channels.
    """
    # Create a random 24-bit number (0 to 16,777,215)
    raw_data = random.getrandbits(num_bits)
    print(f"--- Binary Data Test: {bin(raw_data)} ---")
    
    # Extract 8-bit channels (Bit Masking / Shifts)
    r = (raw_data >> 16) & 0xFF
    g = (raw_data >> 8) & 0xFF
    b = raw_data & 0xFF
    
    # Convert 0-255 to 0.0-1.0
    led.color = (r/255, g/255, b/255)
    time.sleep(1)

# --- MAIN LOOP ---

def main():
    print("Starting RGB LED Technical Lab...")
    tests = [
        gamma_correction_test,
        quantization_bit_depth_test,
        frequency_flicker_sweep,
        analog_wave_reconstruction,
        binary_memory_burst
    ]
    
    try:
        while True:
            # Shuffle tests for a random experience, or keep order for logging
            test_func = random.choice(tests)
            
            # Pass random parameters where applicable
            if test_func == quantization_bit_depth_test:
                test_func(bits=random.randint(1, 5))
            elif test_func == binary_memory_burst:
                test_func(num_bits=random.choice([8, 16, 24]))
            else:
                test_func()
                
            time.sleep(1)
            led.off()
            
    except KeyboardInterrupt:
        print("\nLab session ended. Cleaning up GPIO.")
        led.close()

if __name__ == "__main__":
    main()
