#!/usr/bin/env python3
import gi
import cairo
import random
import subprocess
import os
import time
import math

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# --- Configuration ---
SCREENSHOT_PATH = "/tmp/screensaver_bg.png"
SAFE_DELAY = 1.0
WIDTH = 3840  # Your TV Width
HEIGHT = 2160 # Your TV Height

class Block:
    """Represents a single block's data"""
    def __init__(self, x, y, size, gray, alpha):
        self.x = x
        self.y = y
        self.size = size
        self.gray = gray
        self.alpha = alpha

class BlockSeries:
    """
    An independent agent that grows over time.
    It has its own speed, spacing, and color rules.
    """
    def __init__(self, screen_w, screen_h):
        # --- 1. RANDOM VARIABLES per Series ---
        self.total_blocks = random.randint(3, 25)
        self.spacing = random.randint(30, 80)      # Variable Spacing
        self.size = random.randint(40, 120)
        self.alpha = random.uniform(0.4, 0.9)      # Variable Transparency
        
        # TIMING: How fast does this specific snake grow?
        # A lower number is faster. Range: 0.05s to 0.4s per block
        self.spawn_rate = random.uniform(0.05, 0.4) 
        self.last_spawn_time = 0
        
        # DIRECTION
        angle = random.uniform(0, 2 * math.pi)
        self.dx = math.cos(angle) * self.spacing
        self.dy = math.sin(angle) * self.spacing
        
        # START POSITION
        self.current_x = random.randint(0, screen_w)
        self.current_y = random.randint(0, screen_h)
        
        # --- 2. COLOR LOGIC ---
        self.current_gray = random.random() # Start shade (0.0 to 1.0)
        
        # Determine step (how much color changes per block)
        raw_step = random.uniform(0.02, 0.20)
        
        # CONSTRAINT: If series is short (< 5), force high contrast
        if self.total_blocks < 5:
            raw_step = max(0.15, raw_step)

        # Decide direction of fade (lighten or darken)
        if self.current_gray > 0.5:
            self.gray_step = -raw_step 
        else:
            self.gray_step = raw_step

        # STATE
        self.blocks = [] # The blocks that actually exist so far
        self.finished = False

    def update(self):
        """Called every frame. Decides if it's time to add a new block."""
        if len(self.blocks) >= self.total_blocks:
            self.finished = True
            return

        now = time.time()
        # Check if enough time has passed based on THIS series' speed
        if now - self.last_spawn_time > self.spawn_rate:
            self.add_next_block()
            self.last_spawn_time = now

    def add_next_block(self):
        # Clamp gray to valid range
        render_gray = max(0.0, min(1.0, self.current_gray))
        
        # Create block data
        b = Block(self.current_x, self.current_y, self.size, render_gray, self.alpha)
        self.blocks.append(b)
        
        # Advance math for next time
        self.current_x += self.dx
        self.current_y += self.dy
        self.current_gray += self.gray_step

    def draw(self, cr):
        # Draw all blocks that exist so far
        for b in self.blocks:
            cr.set_source_rgba(b.gray, b.gray, b.gray, b.alpha)
            cr.rectangle(b.x, b.y, b.size, b.size)
            cr.fill()

class ScreensaverWindow(Gtk.Window):
    def __init__(self):
        self.start_time = time.time()
        self.take_screenshot()
        
        super().__init__()
        self.resize(WIDTH, HEIGHT) # Force TV Resolution

        # Load background
        try:
            self.bg_surface = cairo.ImageSurface.create_from_png(SCREENSHOT_PATH)
        except Exception as e:
            print(f"Bg Error: {e}")
            self.bg_surface = None

        self.active_series = [] # List of currently animating series
        
        self.setup_window()
        
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)
        self.connect("realize", self.on_realize)
        
        # Inputs
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | 
                        Gdk.EventMask.BUTTON_PRESS_MASK | 
                        Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("motion-notify-event", self.quit_app)
        self.connect("button-press-event", self.quit_app)
        self.connect("key-press-event", self.quit_app)

        # ANIMATION LOOP: Runs 30 times per second (33ms)
        GLib.timeout_add(33, self.game_loop)

    def take_screenshot(self):
        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
        try:
            if "GNOME" in desktop or "UBUNTU" in desktop:
                subprocess.run(["gnome-screenshot", "-f", SCREENSHOT_PATH], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif "WAYLAND_DISPLAY" in os.environ:
                subprocess.run(["grim", SCREENSHOT_PATH], check=True)
            else:
                subprocess.run(["scrot", "--overwrite", SCREENSHOT_PATH], check=True)
        except:
            pass

    def setup_window(self):
        self.fullscreen()
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_app_paintable(True)

    def on_realize(self, widget):
        cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.BLANK_CURSOR)
        if self.get_window():
            self.get_window().set_cursor(cursor)

    def on_draw(self, widget, cr):
        # 1. ALWAYS DRAW BACKGROUND FIRST (Fixes Black Screen)
        if self.bg_surface:
            img_w = self.bg_surface.get_width()
            img_h = self.bg_surface.get_height()
            scale_x = WIDTH / img_w
            scale_y = HEIGHT / img_h
            
            cr.save()
            cr.scale(scale_x, scale_y)
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.paint()
            cr.restore()
        else:
            cr.set_source_rgb(0, 0, 0)
            cr.paint()

        # 2. Draw all active series on top
        for series in self.active_series:
            series.draw(cr)

    def game_loop(self):
        """The heart of the animation"""
        
        # A. Randomly add a new series (1 in 10 chance per frame)
        if len(self.active_series) < 15 and random.random() < 0.1:
            self.active_series.append(BlockSeries(WIDTH, HEIGHT))

        # B. Update existing series
        for series in self.active_series:
            series.update()

        # C. Remove old/finished series
        # We keep them for a bit after they finish, or remove them immediately?
        # Let's remove them if they are 'finished' and have been sitting for 2 seconds
        # For now, let's just keep growing the list until a clear limits
        if len(self.active_series) > 20:
            # Remove the oldest one to keep memory clean
            self.active_series.pop(0)

        # D. Trigger a Redraw
        self.queue_draw()
        return True

    def quit_app(self, widget, event):
        if time.time() - self.start_time > SAFE_DELAY:
            Gtk.main_quit()
            return True
        return False

if __name__ == "__main__":
    win = ScreensaverWindow()
    win.show_all()
    Gtk.main()
