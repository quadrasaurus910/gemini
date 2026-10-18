import time
import numpy as np
import random
from pi5neo import Pi5Neo, LEDColor, EPixelType

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
SPI_DEVICE = '/dev/spidev0.0'
NUM_LEDS = 60          # Adjust to your physical strip length
SPI_SPEED = 800        # kHz
PIXEL_TYPE = EPixelType.GRB

# ==============================================================================
# --- SOLAR CORONA & PLASMA ENGINE ---
# ==============================================================================
class SolarCoronaSimulation:
    def __init__(self, num_leds):
        self.num_leds = num_leds
        
        # Floating-point canvas for smooth additive light blending [NUM_LEDS, 3]
        self.canvas = np.zeros((self.num_leds, 3))
        
        # Active flare / coronal mass ejection wavefronts
        # Each flare: [position, velocity, intensity, width]
        self.flares = []
        
        # Core fusion pulse timer
        self.fusion_phase = 0.0
        
        # Solar wind particle drift offset
        self.wind_offset = 0.0

    def update(self):
        """Advances plasma dynamics, fusion pulses, solar wind, and flare events."""
        # 1. Thermal Decay (Cooling of plasma trails)
        # Multiplicative decay fades out older light smoothly
        self.canvas *= 0.85

        # 2. Solar Wind (Constant baseline stream moving outward)
        self.wind_offset = (self.wind_offset + 0.3) % self.num_leds
        
        # 3. Hydrogen/Helium Fusion Core (Pulsing energy generation near the start)
        self.fusion_phase += 0.15
        fusion_intensity = (np.sin(self.fusion_phase) * 0.5 + 0.5) ** 3.0  # Sharp core pulses
        
        # Inject fusion energy at the base (LEDs 0 to 3)
        core_color = np.array([255.0, 120.0, 10.0]) # Deep solar orange/gold
        for i in range(min(4, self.num_leds)):
            self.canvas[i] += core_color * (fusion_intensity * 0.4)

        # 4. Magnetic Reconnection & Flare Generation
        # Random chance each frame to trigger a magnetic snap / flare event
        if random.random() < 0.08 and len(self.flares) < 3:
            # Spawn flare near the lower-middle active region
            spawn_pos = random.uniform(5.0, float(self.num_leds * 0.4))
            velocity = random.uniform(0.8, 2.2)      # Outward surge speed
            intensity = random.uniform(180.0, 255.0) # Blinding coronal brightness
            width = random.uniform(3.0, 8.0)         # Flare spread width
            self.flares.append([spawn_pos, velocity, intensity, width])

        # 5. Update and Render Active Flares (CMEs)
        active_flares = []
        for flare in self.flares:
            pos, vel, intensity, width = flare
            pos += vel  # Move outward
            intensity *= 0.94  # Energy dissipation as it travels

            if intensity > 5.0 and pos < self.num_leds:
                active_flares.append([pos, vel, intensity, width])
                
                # Render flare profile across nearby LEDs using a Gaussian distribution
                for i in range(self.num_leds):
                    dist = abs(i - pos)
                    if dist < width * 2.5:
                        # Coronal flare color: intense white-yellow core fading to solar red edges
                        flare_profile = np.exp(-(dist**2) / (2.0 * (width**2))) * intensity
                        
                        # High-energy core gets super-heated white/cyan tint, outer edges get hot red/orange
                        if flare_profile > 150:
                            r, g, b = 255.0, 255.0, 200.0 # Blinding reconnection flash
                        elif flare_profile > 80:
                            r, g, b = 255.0, 180.0, 50.0  # Active corona yellow
                        else:
                            r, g, b = 220.0, 40.0, 10.0   # Chromosphere red
                            
                        self.canvas[i, 0] = min(255.0, self.canvas[i, 0] + (r * (flare_profile / 255.0)))
                        self.canvas[i, 1] = min(255.0, self.canvas[i, 1] + (g * (flare_profile / 255.0)))
                        self.canvas[i, 2] = min(255.0, self.canvas[i, 2] + (b * (flare_profile / 255.0)))

        self.flares = active_flares

        # 6. Add ambient Solar Wind particle wisps
        for i in range(self.num_leds):
            # Traveling wave pattern simulating charged particles in magnetic field lines
            wind_wave = np.sin((i + self.wind_offset) * 0.3) * 0.5 + 0.5
            wind_color = np.array([40.0, 20.0, 5.0]) # Dim ambient solar glow
            self.canvas[i] += wind_color * (wind_wave * 0.15)

    def render_frame(self, neo_strip):
        """Pushes the floating-point plasma canvas onto the physical LED strip."""
        neo_strip.clear_strip()
        
        for i in range(self.num_leds):
            r = int(np.clip(self.canvas[i, 0], 0, 255))
            g = int(np.clip(self.canvas[i, 1], 0, 255))
            b = int(np.clip(self.canvas[i, 2], 0, 255))
            
            if r > 0 or g > 0 or b > 0:
                color_obj = LEDColor(red=r, green=g, blue=b)
                neo_strip.set_led_color_object(i, color_obj)
                
        neo_strip.update_strip()

# ==============================================================================
# --- MAIN EXECUTION LOOP ---
# ==============================================================================
if __name__ == "__main__":
    print("Initializing Solar Chromosphere & Corona Simulation...")
    
    try:
        with Pi5Neo(SPI_DEVICE, NUM_LEDS, SPI_SPEED, pixel_type=PIXEL_TYPE) as neo:
            solar_sim = SolarCoronaSimulation(num_leds=NUM_LEDS)
            
            print("Solar simulation running. Press Ctrl+C to exit.")
            while True:
                solar_sim.update()
                solar_sim.render_frame(neo)
                
                # Frame pacing (~40 FPS for smooth plasma wave propagation)
                time.sleep(0.025)

    except KeyboardInterrupt:
        print("\nSolar simulation terminated safely.")
