import time
import numpy as np
from pi5neo import Pi5Neo, LEDColor, EPixelType

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
SPI_DEVICE = '/dev/spidev0.0'
NUM_LEDS = 60          # Adjust to match your physical LED strip length
SPI_SPEED = 800        # kHz
PIXEL_TYPE = EPixelType.GRB

# ==============================================================================
# --- LORENZ ATTRACTOR FLUID ENGINE ---
# ==============================================================================
class SmoothLorenzFlow:
    def __init__(self, num_leds, trail_length=35):
        self.num_leds = num_leds
        self.trail_length = trail_length
        
        # Integration parameters (fine step for ultra-smooth flow)
        self.dt = 0.012
        self.sigma = 10.0
        self.rho = 28.0
        self.beta = 8.0 / 3.0
        
        # Initial phase space coordinates (x, y, z)
        self.pos = np.array([0.1, 1.0, 1.0])
        
        # Initialize trail history queue
        self.history = []
        for _ in range(self.trail_length):
            self._step_math()
            self.history.append(self.pos.copy())

    def _step_math(self):
        """Advances the Lorenz differential equations by one step."""
        x, y, z = self.pos
        dx = self.sigma * (y - x)
        dy = x * (self.rho - z) - y
        dz = x * y - self.beta * z
        self.pos += np.array([dx, dy, dz]) * self.dt

    def update(self):
        """Steps the chaos forward and updates the trailing history."""
        self._step_math()
        self.history.pop(0)
        self.history.append(self.pos.copy())

    def generate_palette(self, t):
        """
        Generates smooth, organic RGB color transitions using cosine palettes 
        driven by the chaotic state evolution.
        """
        # Cosine color gradient formulas (Inigo Quilez method)
        # a: bias, b: amplitude, c: frequency, d: phase
        r = 0.5 + 0.5 * np.cos(6.28318 * (1.0 * t + np.array([0.0, 0.33, 0.67])))
        g = 0.5 + 0.5 * np.cos(6.28318 * (1.0 * t + np.array([0.33, 0.67, 0.0])))
        b = 0.5 + 0.5 * np.cos(6.28318 * (1.0 * t + np.array([0.67, 0.0, 0.33])))
        
        # Return scaled RGB tuple (0-255)
        return (
            int(np.clip(r[0] * 255, 0, 255)),
            int(np.clip(g[0] * 255, 0, 255)),
            int(np.clip(b[0] * 255, 0, 255))
        )

    def render_frame(self, neo_strip):
        """Renders the multi-pixel trail with gradient fading onto the strip."""
        # 1. Create a floating-point canvas (shape: [NUM_LEDS, 3]) for smooth blending
        canvas = np.zeros((self.num_leds, 3))
        
        # Time seed for color evolution based on system movement
        color_time = (self.pos[2] * 0.01) % 1.0

        # 2. Map each point in the trail history to the LED strip
        for i, pt in enumerate(self.history):
            x_val, y_val, z_val = pt
            
            # Map Lorenz X coordinate (-20 to 20 range roughly) to strip index [0, NUM_LEDS-1]
            # Clamped safely to prevent out-of-bounds indexing
            normalized_x = (x_val + 20.0) / 40.0
            led_float_idx = normalized_x * (self.num_leds - 1)
            idx = int(np.clip(led_float_idx, 0, self.num_leds - 1))
            
            # Calculate brightness attenuation along the trail (Tail = dim, Head = bright)
            # Using an exponential curve for a gorgeous natural glow tail
            intensity = (i / float(self.trail_length)) ** 2.0
            
            # Modulate color slightly per point based on Y/Z depth for internal richness
            point_color_time = (color_time + (z_val * 0.005)) % 1.0
            base_r, base_g, base_b = self.generate_palette(point_color_time)
            
            # Apply intensity scaling
            r = base_r * intensity
            g = base_g * intensity
            b = base_b * intensity
            
            # Accumulate onto the canvas buffer (handles overlapping pixels gracefully)
            canvas[idx, 0] = min(255.0, canvas[idx, 0] + r)
            canvas[idx, 1] = min(255.0, canvas[idx, 1] + g)
            canvas[idx, 2] = min(255.0, canvas[idx, 2] + b)

        # 3. Push canvas data out to the physical pi5neo strip
        neo_strip.clear_strip()
        for i in range(self.num_leds]:
            red = int(canvas[i, 0])
            green = int(canvas[i, 1])
            blue = int(canvas[i, 2])
            
            if red > 0 or green > 0 or blue > 0:
                color_obj = LEDColor(red=red, green=green, blue=blue)
                neo_strip.set_led_color_object(i, color_obj)

        neo_strip.update_strip()

# ==============================================================================
# --- MAIN EXECUTION LOOP ---
# ==============================================================================
if __name__ == "__main__":
    print("Initializing Smooth Fluid Lorenz Chaos Animation...")
    
    try:
        # Context manager automatically handles initialization and cleanup
        with Pi5Neo(SPI_DEVICE, NUM_LEDS, SPI_SPEED, pixel_type=PIXEL_TYPE) as neo:
            
            chaos_engine = SmoothLorenzFlow(num_leds=NUM_LEDS, trail_length=40)
            
            print("Animation running. Press Ctrl+C to exit.")
            while True:
                # Update math state and render frame
                chaos_engine.update()
                chaos_engine.render_frame(neo)
                
                # Frame pacing (~40-50 FPS for smooth fluid motion)
                time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nAnimation terminated safely by user.")
