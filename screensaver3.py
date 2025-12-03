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

# YOUR TV RESOLUTION
WIDTH = 3840
HEIGHT = 2160

# ANIMATION SETTINGS
MAX_SERIES_ON_SCREEN = 50  # How many "snakes" before we clear
SPACING = 40               # Distance between blocks in a series
BLOCK_SIZE_MIN = 30
BLOCK_SIZE_MAX = 100

class BlockSeries:
    """
    Manages a group of blocks that stagger in a specific direction
    """
    def __init__(self, screen_w, screen_h):
        # 1. Properties of the SERIES (The Snake)
        self.num_blocks = random.randint(5, 20) # 5-20 boxes per grouping
        
        # Random Start Point
        self.start_x = random.randint(0, screen_w)
        self.start_y = random.randint(0, screen_h)
        
        # Random Direction (Vector)
        # We pick a random angle (0 to 2pi) and convert to x/y
        angle = random.uniform(0, 2 * math.pi)
        self.dx = math.cos(angle) * SPACING
        self.dy = math.sin(angle) * SPACING
        
        # Block Size for this series
        self.size = random.randint(BLOCK_SIZE_MIN, BLOCK_SIZE_MAX)
        
        # 2. Color Logic (Grayscale Fade)
        # Start at a random gray (0.0=black, 1.0=white)
        self.start_gray = random.random()
        # Decide if we get lighter or darker
        if self.start_gray > 0.5:
            self.gray_step = -0.05 # Get darker
        else:
            self.gray_step = 0.05  # Get lighter

    def draw(self, cr):
        current_x = self.start_x
        current_y = self.start_y
        current_gray = self.start_gray

        for i in range(self.num_blocks):
            # Clamp gray value between 0 and 1
            render_gray = max(0.0, min(1.0, current_gray))
            
            # Set Color (R, G, B, Alpha)
            # Alpha varies slightly so they look like glass
            cr.set_source_rgba(render_gray, render_gray, render_gray, 0.6)
            
            # Draw the box
            cr.rectangle(current_x, current_y, self.size, self.size)
            cr.fill()
            
            # --- CALCULATE NEXT ITERATION ---
            # Move position
            current_x += self.dx
            current_y += self.dy
            
            # Shift shade
            current_gray += self.gray_step

class ScreensaverWindow(Gtk.Window):
    def __init__(self):
        self.start_time = time.time()
        self.take_screenshot()
        
        super().__init__()
        
        # Use your Hardcoded Dimensions
        self.width = WIDTH
        self.height = HEIGHT

        try:
            self.bg_surface = cairo.ImageSurface.create_from_png(SCREENSHOT_PATH)
        except Exception as e:
            print(f"Background load failed: {e}")
            self.bg_surface = None

        self.series_list = [] # List to hold our BlockSeries objects

        self.setup_window()
        
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)
        self.connect("realize", self.on_realize)
        
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | 
                        Gdk.EventMask.BUTTON_PRESS_MASK | 
                        Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("motion-notify-event", self.quit_app)
        self.connect("button-press-event", self.quit_app)
        self.connect("key-press-event", self.quit_app)

        # Timer: Add a new series every 200ms
        GLib.timeout_add(200, self.update_animation)

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
        self.resize(self.width, self.height)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_app_paintable(True)

    def on_realize(self, widget):
        cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.BLANK_CURSOR)
        window = self.get_window()
        if window:
            window.set_cursor(cursor)

    def on_draw(self, widget, cr):
        # 1. DRAW BACKGROUND (If first frame, or if we want to redraw it fully)
        # Optimization: We usually don't need to redraw the FULL background every frame
        # if we aren't clearing the screen, but Cairo might require it depending on the compositor.
        # Let's draw the background once, then stack boxes.
        
        if not self.series_list:
             # If list is empty (start or reset), draw full clean background
            if self.bg_surface:
                # Scale logic for 4k TV
                img_w = self.bg_surface.get_width()
                img_h = self.bg_surface.get_height()
                scale_x = self.width / img_w
                scale_y = self.height / img_h
                
                cr.save()
                cr.scale(scale_x, scale_y)
                cr.set_source_surface(self.bg_surface, 0, 0)
                cr.paint()
                cr.restore()
            else:
                cr.set_source_rgb(0, 0, 0)
                cr.paint()

        # 2. DRAW THE SERIES
        for series in self.series_list:
            series.draw(cr)

        # 3. THE "REALITY REFRESH" EFFECT
        # Randomly draw a clean chunk of the background ON TOP of the blocks
        # This makes it look like the blocks are weaving in and out of the desktop
        if self.bg_surface and len(self.series_list) > 0:
            self.draw_reality_patch(cr)

    def draw_reality_patch(self, cr):
        # Pick a random spot
        patch_w = random.randint(100, 400)
        patch_h = random.randint(100, 400)
        patch_x = random.randint(0, self.width - patch_w)
        patch_y = random.randint(0, self.height - patch_h)

        # To grab the correct part of the source image, we need to map 
        # the screen coordinates back to image coordinates
        img_w = self.bg_surface.get_width()
        img_h = self.bg_surface.get_height()
        scale_x = self.width / img_w
        scale_y = self.height / img_h

        # Save context
        cr.save()
        
        # Define the rectangular area we want to "refresh"
        cr.rectangle(patch_x, patch_y, patch_w, patch_h)
        cr.clip() # Tell Cairo: "Only draw inside this rectangle"

        # Draw the background again
        cr.scale(scale_x, scale_y)
        cr.set_source_surface(self.bg_surface, 0, 0)
        cr.paint()
        
        # Restore (remove clip)
        cr.restore()
        
        # Optional: Draw a thin border around the patch to make it look "glitchy"
        cr.set_source_rgba(1, 1, 1, 0.3)
        cr.set_line_width(1)
        cr.rectangle(patch_x, patch_y, patch_w, patch_h)
        cr.stroke()

    def update_animation(self):
        # Reset if too many series
        if len(self.series_list) > MAX_SERIES_ON_SCREEN:
            self.series_list = []
            self.queue_draw() # This triggers a full background clear in on_draw
            return True

        # Create a new series object
        new_series = BlockSeries(self.width, self.height)
        self.series_list.append(new_series)
        
        # Trigger a redraw
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
