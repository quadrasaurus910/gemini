import time
import numpy as np
import random
from pi5neo import Pi5Neo, LEDColor, EPixelType

# ==============================================================================
# --- APOLLO GUIDANCE COMPUTER (AGC) SIMULATION ENVIRONMENT ---
# --- Block II, MEMORY MAP & CONSTANTS ---
# --- IN MEMORY OF MARGARET HAMILTON (1936-2026) ---
# ==============================================================================

# LED Strip Configuration
SPI_DEVICE = '/dev/spidev0.0'
NUM_LEDS = 60
SPI_SPEED = 800  # kHz
PIXEL_TYPE = EPixelType.GRB  # Adjust if using RGBW

# ==============================================================================
# --- R00 - THE IDLE LOOP ---
# --- Equivalent to AGC "DUMMY JOB" to occupy unused time ---
# ==============================================================================
def r00_idle(duration=0.1):
    """Simple delay mimicking the idle state of the AGC."""
    time.sleep(duration)

# ==============================================================================
# --- AGC EXECUTIVE & PRIORITY SCHEDULER ---
# --- Modeled after Hamilton's "Higher-Order Software" Concepts ---
# ==============================================================================
class AGC_Executive:
    def __init__(self, neo_strip):
        self.neo = neo_strip
        self.num_leds = neo_strip.num_leds
        
        # --- AGC CORE REGISTERS (Simulated) ---
        # Used for intermediate mathematical calculations
        self.MPAC = 0.0  # Multipurpose Accumulator (X-state)
        self.L = 0.0     # Lower Accumulator (Y-state)
        self.Q = 0.0     # Quarter Accumulator (Z-state)
        
        # --- PHASE SPACE / STATE VARIABLES ---
        self.TIME_STEP = 0.01
        self.state = np.array([1.0, 1.0, 1.0])  # Initial X, Y, Z
        
        # --- LORENZ PARAMETERS (Edward Lorenz, 1963) ---
        # The variables that define the chaos
        self.sigma = 10.0
        self.rho = 28.0
        self.beta = 8.0 / 3.0
        
        # --- MISSION CONTROL & STATUS ---
        self.alarm_active = False
        self.alarm_code = 0
        self.last_update_time = time.time()

        print("--> AGC_EXECUTIVE INITIALIZED. HAMILTON/LORENZ SYSTEM ONLINE.")

    # --------------------------------------------------------------------------
    # --- SERVICER (Main Guidance Job) ---
    # --- Priority Job 20. Must execute periodically. ---
    # --------------------------------------------------------------------------
    def servicer_job(self):
        """Main chaotic calculation routine."""
        if self.alarm_active:
            return # Executive is currently in RESTART mode.

        # 1. Update AGC Internal Registers with current system state
        self.MPAC, self.L, self.Q = self.state

        # 2. Compute Chaotic Derivatives (Lorenz ODEs)
        # s*(y - x)
        d_mpac = self.sigma * (self.L - self.MPAC)
        # r*x - y - x*z
        d_l = (self.MPAC * self.rho) - self.L - (self.MPAC * self.Q)
        # x*y - b*z
        d_q = (self.MPAC * self.L) - (self.beta * self.Q)

        # 3. Step System State using Euler integration
        self.state += np.array([d_mpac, d_l, d_q]) * self.TIME_STEP

        # 4. Check for Executive Overflow / Chaos Instability
        # Hamilton's concept: anticipatory error detection.
        self.check_for_system_overflow()

        # 5. Map State to Visuals
        self.update_display_system()

    # --------------------------------------------------------------------------
    # --- ERROR HANDLING & ALARM SYSTEM ---
    # --- "THE 1202 ALARM" Recovery Routine ---
    # --- Designed to restart critical tasks when overloaded. ---
    # --------------------------------------------------------------------------
    def check_for_system_overflow(self):
        """Detects if the chaos system is approaching unstable boundaries."""
        # If any register exceeds an arbitrary boundary, trigger alarm.
        MAX_SAFE_VALUE = 60.0
        if (abs(self.MPAC) > MAX_SAFE_VALUE or 
            abs(self.L) > MAX_SAFE_VALUE or 
            abs(self.Q) > MAX_SAFE_VALUE):
            
            # TRIGGER EXECUTIVE ALARM: 1202 (Executive Overflow)
            self.trigger_alarm(1202)

    def trigger_alarm(self, code):
        """Activates priority restart and displays alarm on DSKY."""
        self.alarm_active = True
        self.alarm_code = code
        print(f"\n*** [ALARM {code}] EXECUTIVE OVERFLOW DETECTED ***")
        print("--> COMMENCING HAMILTON ROBUST RESTART SEQUENCE...")

        # Visually indicate alarm state: Flash red/white pattern (1202 colors)
        alarm_color = LEDColor(red=255, green=0, blue=0)
        warning_color = LEDColor(red=255, green=255, blue=255)
        for _ in range(3):
            self.neo.fill_strip_object(alarm_color)
            self.neo.update_strip()
            r00_idle(0.2)
            self.neo.fill_strip_object(warning_color)
            self.neo.update_strip()
            r00_idle(0.2)

        # ----------------------------------------------------------------------
        # --- RESTART ROUTINE ---
        # --- Priority Job 01. Restore vital state, flush temp jobs. ---
        # ----------------------------------------------------------------------
        print("--> RESTORING SYSTEM STATE FROM SAFE MEMORY PAD...")
        
        # Hamilton's design allows restarting from a known good state.
        # We restore to a chaotic but bounded region, resetting the trajectory.
        self.state = np.array([
            random.uniform(-10, 10),
            random.uniform(-10, 10),
            random.uniform(20, 30) # Typically stable Z region for r=28
        ])
        
        # Add slight timing jitter to represent timing differences during restart
        r00_idle(random.uniform(0.3, 0.7))

        self.alarm_active = False
        self.alarm_code = 0
        print("--> AGC EXECUTIVE RESTART COMPLETE. SERVICER RESUMING.\n")

    # --------------------------------------------------------------------------
    # --- DISPLAY & DSKY SUB-SYSTEM ---
    # --- Maps chaotic state to LED positions and colors ---
    # --------------------------------------------------------------------------
    def update_display_system(self):
        """Renders the state of the chaos system onto the LED strip."""
        # Clean background
        self.neo.clear_strip()

        # 1. Map MPAC (X) to LED position (bounded [0, NUM_LEDS-1])
        # A simple linear map with boundary constraints.
        mpac_map = (self.MPAC + 20) / 40.0 # Map -20..20 to 0..1
        led_index = int(np.clip(mpac_map * self.num_leds, 0, self.num_leds - 1))

        # 2. Map L (Y) and Q (Z) to Color (bounded [0, 255])
        # Use simple modulo and clipping to derive RGB.
        red_val = int(np.clip((abs(self.L) * 10) % 256, 0, 255))
        blue_val = int(np.clip((abs(self.Q) * 5) % 256, 0, 255))
        # Hamilton's classic Apollo uniform color (Cyan-ish) for contrast
        green_val = int(np.clip((abs(self.MPAC) * 2) % 256, 128, 255)) 

        dynamic_color = LEDColor(red=red_val, green=green_val, blue=blue_val)
        
        # 3. Apply state to the selected LED.
        # Draw a primary chaotic 'pixel'
        self.neo.set_led_color_object(led_index, dynamic_color)

        # 4. Draw a slower, trailing shadow representing the system memory.
        shadow_index = int(np.clip((mpac_map * 0.95) * self.num_leds, 0, self.num_leds -1))
        shadow_color = LEDColor(red=100, green=100, blue=100) # Dim white
        self.neo.set_led_color_object(shadow_index, shadow_color)

        self.neo.update_strip()


# ==============================================================================
# --- MAIN MISSION EXECUTION ---
# --- Context Manager handles setup and cleanup automatically ---
# ==============================================================================
if __name__ == "__main__":
    print("\n==================================================================")
    print("      *** DEDICATION TO MARGARET ELIZABETH HAMILTON ***")
    print("          PIONEERING SOFTWARE ENGINEER (1936-2026)")
    print("==================================================================\n")

    try:
        # 1. Activate hardware interface
        with Pi5Neo(SPI_DEVICE, NUM_LEDS, SPI_SPEED, pixel_type=PIXEL_TYPE) as neo:
            
            # 2. Initialize the AGC Executive
            agc = AGC_Executive(neo)
            
            # 3. Start Mission Time / Main Executive Loop
            print("--> GNC MASTER MISSION TIMER STARTED. CYCLE COMMENCING.")
            while True:
                # Execute the Servicer Job (Priority 20)
                agc.servicer_job()

                # Add a variable Idle delay to represent process timing variability
                # R00 (Idle Loop) occupies remainder of cycle time.
                r00_idle(random.uniform(0.005, 0.015))

    except KeyboardInterrupt:
        # Hamilton software always allows user/astronaut intervention.
        print("\n--> MANUAL INTERRUPT RECEIVED. GNC SYSTEM TERMINATING SAFELY.")
        # Context manager automatically clears strip and closes SPI.
        print("--> SPI INTERFACE CLOSED. STRIP CLEARED.")
        print("Ad Astra, Margaret.\n")
