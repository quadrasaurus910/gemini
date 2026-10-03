import time
import math
import random
import board
import neopixel

# =============================================================================
# STRIP CONFIGURATION (External Power)
# =============================================================================
NUM_PIXELS = 60
pixels = neopixel.NeoPixel(board.D18, NUM_PIXELS, brightness=0.85, auto_write=False)

GAMMA = 2.2

# =============================================================================
# COLOR SPACE UTILITIES
# =============================================================================
def linear_to_srgb(c):
    """Gamma correction for final hardware output."""
    c = max(0.0, min(1.0, float(c)))
    if c <= 0.0031308:
        s = c * 12.92
    else:
        s = 1.055 * math.pow(c, 1.0 / GAMMA) - 0.055
    return int(max(0, min(255, s * 255)))

def oklab_to_linear_rgb(L, a, b):
    """Converts OKLab to Linear RGB for physically accurate additive light blending."""
    L = max(0.0, min(1.0, L))
    
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3

    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_rgb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    return max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b_rgb))

# =============================================================================
# PARTICLE PHYSICS ENGINE
# =============================================================================
class Particle:
    def __init__(self, pos, vel, lab_color, size, life, is_vibrating=False):
        self.pos = pos
        self.vel = vel
        self.color = lab_color # (L, a, b)
        self.size = size
        self.life = life
        self.max_life = life
        self.is_vibrating = is_vibrating
        self.active = True

    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        if self.life <= 0 or self.pos < -10 or self.pos > NUM_PIXELS + 10:
            self.active = False

def spawn_event(particles):
    """Randomly selects and spawns one of the 5 physics interactions."""
    event_type = random.choices(
        ['MICROWAVE', 'INFRARED', 'PHOTOELECTRIC', 'COMPTON', 'PAIR_PROD'], 
        weights=[20, 20, 20, 15, 10], k=1
    )[0]
    
    start_pos = -2.0 if random.random() > 0.5 else NUM_PIXELS + 2.0
    direction = 1 if start_pos < 0 else -1

    if event_type == 'MICROWAVE':
        # Rotational spin: Slow, wide, amber heat
        vel = direction * random.uniform(8.0, 15.0)
        life = random.uniform(6.0, 10.0)
        particles.append(Particle(start_pos, vel, (0.45, 0.12, 0.18), size=6.0, life=life))

    elif event_type == 'INFRARED':
        # Vibrational: Strikes a random molecule, causing rapid stationary pulsing
        impact_pos = random.uniform(5, NUM_PIXELS - 5)
        life = random.uniform(2.0, 4.0)
        particles.append(Particle(impact_pos, 0.0, (0.50, 0.22, 0.05), size=1.5, life=life, is_vibrating=True))

    elif event_type == 'PHOTOELECTRIC':
        # UV/X-Ray: Fast projectile hits, ejects electron
        impact_time = random.uniform(1.0, 2.0)
        vel = direction * random.uniform(25.0, 35.0)
        
        class PhotoelectricProjectile(Particle):
            def update(self, dt):
                super().update(dt)
                if self.life <= 0 and self.active:
                    self.active = False
                    # Eject electron (Blue, very fast, small)
                    particles.append(Particle(self.pos, self.vel * 1.5, (0.7, -0.1, -0.2), size=1.0, life=2.0))

        particles.append(PhotoelectricProjectile(start_pos, vel, (0.6, 0.15, -0.2), size=2.0, life=impact_time))

    elif event_type == 'COMPTON':
        # High X-Ray: Projectile hits, scatters lower energy photon + electron
        impact_time = random.uniform(1.0, 2.0)
        vel = direction * random.uniform(35.0, 45.0)
        
        class ComptonProjectile(Particle):
            def update(self, dt):
                super().update(dt)
                if self.life <= 0 and self.active:
                    self.active = False
                    # Lower energy scattered photon (Green/Yellow)
                    particles.append(Particle(self.pos, self.vel * 0.8, (0.6, -0.15, 0.15), size=2.0, life=3.0))
                    # Ejected electron (Blue, deflected slightly slower)
                    particles.append(Particle(self.pos, self.vel * 0.5, (0.6, -0.1, -0.2), size=1.0, life=1.5))

        particles.append(ComptonProjectile(start_pos, vel, (0.9, 0.0, 0.0), size=2.0, life=impact_time))

    elif event_type == 'PAIR_PROD':
        # Gamma: Blinding hit, splits into Matter (Electron) and Antimatter (Positron)
        impact_time = random.uniform(1.0, 1.5)
        vel = direction * random.uniform(45.0, 60.0)
        
        class PairProdProjectile(Particle):
            def update(self, dt):
                super().update(dt)
                if self.life <= 0 and self.active:
                    self.active = False
                    # Annihilation flash
                    particles.append(Particle(self.pos, 0.0, (0.95, 0.0, 0.0), size=3.0, life=0.2))
                    # Electron (Blue)
                    particles.append(Particle(self.pos, 25.0, (0.7, -0.1, -0.2), size=1.5, life=2.0))
                    # Positron (Magenta)
                    particles.append(Particle(self.pos, -25.0, (0.7, 0.2, -0.1), size=1.5, life=2.0))

        particles.append(PairProdProjectile(start_pos, vel, (1.0, 0.0, 0.0), size=2.5, life=impact_time))


def main():
    print("Initiating Water Absorption Physics Engine (60 Pixels)...")
    
    particles = []
    last_time = time.time()
    start_time = last_time
    next_event_time = 0.5

    try:
        while True:
            now = time.time()
            dt = now - last_time
            last_time = now
            elapsed = now - start_time

            # 1. Random Event Spawner
            if elapsed > next_event_time:
                spawn_event(particles)
                next_event_time = elapsed + random.uniform(0.8, 3.5)

            # 2. Update Particles
            for p in particles:
                p.update(dt)
            particles = [p for p in particles if p.active]

            # 3. Render Loop (Additive Blending in Linear RGB space)
            # Start with the "Transparent Water" baseline (Visible Spectrum passing through)
            water_shift = math.sin(elapsed * 0.5) * 0.02
            water_lab = (0.12 + water_shift, -0.06, -0.12)
            water_r, water_g, water_b = oklab_to_linear_rgb(*water_lab)

            for i in range(NUM_PIXELS):
                pixel_r, pixel_g, pixel_b = water_r, water_g, water_b

                # Additive particle light
                for p in particles:
                    dist = abs(i - p.pos)
                    if dist < p.size * 2.0:
                        # Gaussian falloff for smooth anti-aliased particles
                        intensity = math.exp(-(dist ** 2) / (p.size ** 2))
                        
                        # Fade out at end of life
                        fade = min(1.0, p.life / 0.5)
                        intensity *= fade

                        # High-frequency vibration for Infrared events
                        if p.is_vibrating:
                            intensity *= 0.2 + 0.8 * abs(math.sin(p.life * 40.0))

                        pr, pg, pb = oklab_to_linear_rgb(*p.color)
                        
                        # Additive light physics
                        pixel_r += pr * intensity
                        pixel_g += pg * intensity
                        pixel_b += pb * intensity

                # Hardware output with gamma correction
                pixels[i] = (
                    linear_to_srgb(pixel_r), 
                    linear_to_srgb(pixel_g), 
                    linear_to_srgb(pixel_b)
                )

            pixels.show()
            time.sleep(0.02) # ~50 FPS

    except KeyboardInterrupt:
        pixels.fill((0, 0, 0))
        pixels.show()
        print("\nPhysics Engine halted.")

if __name__ == "__main__":
    main()
