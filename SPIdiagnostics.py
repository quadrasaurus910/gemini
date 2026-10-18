import time
import numpy as np
from pi5neo import Pi5Neo, LEDColor, EPixelType

# ==============================================================================
# --- DIAGNOSTIC CONFIGURATION ---
# ==============================================================================
SPI_DEVICE = '/dev/spidev0.0'
NUM_LEDS = 60          # Match your physical strip length
SPI_SPEED = 800        # kHz
PIXEL_TYPE = EPixelType.GRB

class SPIHardwareDiagnostics:
    def __init__(self, num_leds):
        self.num_leds = num_leds

    def print_telemetry(self, test_name, params):
        """Outputs formatted real-time telemetry to the terminal."""
        param_str = " | ".join([f"{k}: {v}" for k, v in params.items()])
        print(f"[DIAGNOSTIC TEST: {test_name}] -> {param_str}")

    def run_spectrum_and_brightness_test(self, neo):
        """
        Test 1: Full Spectrum Hue Rotation & Dynamic Brightness Scaling
        Tests the strip's color reproduction across all primary channels 
        while sweeping global brightness from 10% to 100%.
        """
        print("\n--- STARTING TEST 1: Spectrum & Brightness Gradient Sweep ---")
        
        brightness_levels = [0.1, 0.4, 0.7, 1.0]
        
        for b_idx, brightness in enumerate(brightness_levels):
            # Sweep through full 360-degree hue space
            for hue_angle in range(0, 360, 15):
                # Convert HSV-like hue angle to RGB via cosine approximation
                rad = np.radians(hue_angle)
                r = int((np.cos(rad) * 0.5 + 0.5) * 255 * brightness)
                g = int((np.cos(rad - 2.094) * 0.5 + 0.5) * 255 * brightness)
                b = int((np.cos(rad - 4.188) * 0.5 + 0.5) * 255 * brightness)
                
                color = LEDColor(red=r, green=g, blue=b)
                neo.fill_strip_object(color)
                neo.update_strip()
                
                self.print_telemetry("Color/Brightness Sweep", {
                    "Brightness": f"{int(brightness * 100)}%",
                    "Hue Angle": f"{hue_angle}°",
                    "RGB Output": f"({r}, {g}, {b})"
                })
                time.sleep(0.03)

    def run_trail_memory_test(self, neo):
        """
        Test 2: Trail Buffer & Memory Allocation Stress Test
        Tests variable memory/trail lengths (short points to full strip saturation)
        moving dynamically across the hardware buffer.
        """
        print("\n--- STARTING TEST 2: Trail Memory Allocation Sweep ---")
        
        trail_lengths = [5, 15, 30, 50, NUM_LEDS]
        
        for trail_len in trail_lengths:
            for step in range(NUM_LEDS + trail_len):
                neo.clear_strip()
                
                # Draw trailing ribbon
                for i in range(trail_len):
                    pos = step - i
                    if 0 <= pos < self.num_leds:
                        intensity = 1.0 - (i / float(trail_len))
                        r = int(255 * intensity)
                        g = int(100 * intensity)
                        b = int(255 * intensity)
                        neo.set_led_color_object(pos, LEDColor(red=r, green=g, blue=b))
                
                neo.update_strip()
                
                self.print_telemetry("Memory/Trail Sweep", {
                    "Trail Buffer Size": trail_len,
                    "Current Head Pos": step % NUM_LEDS
                })
                time.sleep(0.02)

    def run_hertz_and_speed_stress_test(self, neo):
        """
        Test 3: SPI Hertz & Frame Pacing Stress Test
        Steps through various frame delay intervals (simulating Hz variations) 
        to verify SPI bus stability under high-frequency updates.
        """
        print("\n--- STARTING TEST 3: SPI Frequency & Frame Rate Stress Test ---")
        
        # Test varying speeds from rapid hyper-bursts to smooth sweeps
        frequencies_hz = [20, 50, 100, 200, 60] # Hertz (FPS equivalent)
        
        for target_hz in frequencies_hz:
            delay = 1.0 / target_hz
            print(f"--> Pacing SPI Bus at ~{target_hz} Hz (Delay: {delay:.4f}s)")
            
            for _ in range(30): # Run for 30 frames per frequency
                # Random noise / static burst test to stress SPI bit transmission
                for i in range(self.num_leds):
                    if np.random.random() > 0.5:
                        neo.set_led_color_object(i, LEDColor(red=np.random.randint(0, 255),
                                                           green=np.random.randint(0, 255),
                                                           blue=np.random.randint(0, 255)))
                    else:
                        neo.set_led_color_object(i, LEDColor(red=0, green=0, blue=0))
                
                neo.update_strip()
                
                self.print_telemetry("Hertz Stress Test", {
                    "Target Frequency": f"{target_hz} Hz",
                    "Frame Interval": f"{delay * 1000:.1f} ms"
                })
                time.sleep(delay)

# ==============================================================================
# --- MAIN EXECUTION LOOP ---
# ==============================================================================
if __name__ == "__main__":
    print("==========================================================")
    print("     PI5NEO SPI HARDWARE & LED STRIP DIAGNOSTIC SUITE     ")
    print("==========================================================")

    try:
        # Initialize SPI context manager
        with Pi5Neo(SPI_DEVICE, NUM_LEDS, SPI_SPEED, pixel_type=PIXEL_TYPE) as neo:
            diagnostic = SPIHardwareDiagnostics(num_leds=NUM_LEDS)
            
            # Continuous diagnostic loop
            loop_count = 1
            while True:
                print(f"\n========== DIAGNOSTIC CYCLE #{loop_count} BEGINS ==========")
                
                # Execute Test Suite Modules in Sequence
                diagnostic.run_spectrum_and_brightness_test(neo)
                diagnostic.run_trail_memory_test(neo)
                diagnostic.run_hertz_and_speed_stress_test(neo)
                
                print(f"========== CYCLE #{loop_count} COMPLETE. RESTARTING... ==========\n")
                loop_count += 1
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[DIAGNOSTIC TERMINATED] User interrupted test suite. SPI connection closed safely.")
