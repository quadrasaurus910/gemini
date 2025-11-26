#!/usr/bin/env python3
import gi
import cairo
import random
import subprocess
import os
import time

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# --- Configuration ---
SCREENSHOT_PATH = "/tmp/screensaver_bg.png"
BOXES_PER_CYCLE = 5   # How many boxes to add every 0.1 seconds
MAX_BOXES = 300       # Restart clearing after this many boxes
SAFE_DELAY = 1.0      # Seconds to ignore mouse movement at start (prevents instant close)

# Detect if we are on Wayland or X11 to choose the right screenshot tool
IS_WAYLAND = "WAYLAND_DISPLAY" in os.environ

class GradientBox:
    def __init__(self, screen_width, screen_height):
        # Random Size
        self.width = random.randint(50, 250)
        self.height = random.randint(50, 250)
        # Random Position
        self.x = random.randint(0, screen_width - self.width)
        self.y = random.randint(0, screen_height - self.height)
        
        # Random Colors for Gradient (R, G, B)
        self.r1, self.g1, self.b1 = (random.random(), random.random(), random.random())
        self.r2, self.g2, self.b2 = (random.random(), random.random(), random.random())
        self.alpha = 0.8 # Slight transparency

    def draw(self, cr):
        # Create Linear Gradient
        gradient = cairo.LinearGradient(self.x, self.y, self.x + self.width, self.y + self.height)
        gradient.add_color_stop_rgba(0.0, self.r1, self.g1, self.b1, self.alpha)
        gradient.add_color_stop_rgba(1.0, self.r2, self.g2, self.b2, self.alpha)
        
        cr.set_source(gradient)
        cr.rectangle(self.x, self.y, self.width, self.height)
        cr.fill()

class ScreensaverWindow(Gtk.Window):
    def __init__(self):
        # 1. Take snapshot of current desktop
        self.take_screenshot()
        self.start_time = time.time()
        
        super().__init__()
        
        self.screen = self.get_screen()
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        # Load the screenshot into memory
        try:
            self.bg_surface = cairo.ImageSurface.create_from_png(SCREENSHOT_PATH)
        except Exception as e:
            print(f"Error loading background: {e}")
            self.bg_surface = None

        self.boxes = []

        self.setup_window()
        
        # 2. Connect Signals (Drawing and Input)
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)
        
        # Listen for ANY input to quit
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | 
                        Gdk.EventMask.BUTTON_PRESS_MASK | 
                        Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("motion-notify-event", self.quit_app)
        self.connect("button-press-event", self.quit_app)
        self.connect("key-press-event", self.quit_app)

        # 3. Start Animation Loop (100ms)
        GLib.timeout_add(100, self.add_new_box)

    def take_screenshot(self):
        # Remove old file
        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)

        try:
            if IS_WAYLAND:
                # Use 'grim' for Wayland (Standard Ubuntu Pi 5)
                subprocess.run(["grim", SCREENSHOT_PATH], check=True)
            else:
                # Use 'scrot' for X11 (Ubuntu on Xorg)
                subprocess.run(["scrot", "--overwrite", SCREENSHOT_PATH], check=True)
        except subprocess.CalledProcessError:
            print("Screenshot tool failed. Background will be black.")

    def setup_window(self):
        self.fullscreen()
        self.set_decorated(False) # No title bar
        self.set_keep_above(True) # Always on top
        self.set_app_paintable(True)
        
        # Hide the mouse cursor
        cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.BLANK_CURSOR)
        self.get_window().set_cursor(cursor)

    def on_draw(self, widget, cr):
        # Layer 1: The Desktop Screenshot
        if self.bg_surface:
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0, 0, 0) # Black fallback
            cr.paint()

        # Layer 2: The Gradient Boxes
        for box in self.boxes:
            box.draw(cr)

    def add_new_box(self):
        # Reset if screen is too full
        if len(self.boxes) > MAX_BOXES:
            self.boxes = []
            self.queue_draw()
            return True
            
        # Add new batch of boxes
        for _ in range(BOXES_PER_CYCLE):
            self.boxes.append(GradientBox(self.width, self.height))

        self.queue_draw()
        return True # Keep timer running

    def quit_app(self, widget, event):
        # IGNORE input for the first few seconds (Safe Start)
        # This prevents accidental closing due to jitter
        if time.time() - self.start_time > SAFE_DELAY:
            Gtk.main_quit()
            return True
        return False

if __name__ == "__main__":
    win = ScreensaverWindow()
    win.show_all()
    Gtk.main()
