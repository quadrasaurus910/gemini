#!/usr/bin/env python3
import gi
import cairo
import random
import subprocess
import os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# --- Configuration ---
SCREENSHOT_PATH = "/tmp/screensaver_bg.png"

# DETECT SESSION TYPE to choose the right screenshot tool
# If 'WAYLAND_DISPLAY' is in environment variables, use grim. Otherwise scrot.
IS_WAYLAND = "WAYLAND_DISPLAY" in os.environ

class GradientBox:
    def __init__(self, screen_width, screen_height):
        self.width = random.randint(50, 200)
        self.height = random.randint(50, 200)
        self.x = random.randint(0, screen_width - self.width)
        self.y = random.randint(0, screen_height - self.height)
        
        # Colors
        self.r1, self.g1, self.b1 = (random.random(), random.random(), random.random())
        self.r2, self.g2, self.b2 = (random.random(), random.random(), random.random())
        self.alpha = 0.7 

    def draw(self, cr):
        gradient = cairo.LinearGradient(self.x, self.y, self.x + self.width, self.y + self.height)
        gradient.add_color_stop_rgba(0.0, self.r1, self.g1, self.b1, self.alpha)
        gradient.add_color_stop_rgba(1.0, self.r2, self.g2, self.b2, self.alpha)
        cr.set_source(gradient)
        cr.rectangle(self.x, self.y, self.width, self.height)
        cr.fill()

class ScreensaverWindow(Gtk.Window):
    def __init__(self):
        # 1. TAKE THE SCREENSHOT BEFORE CREATING THE WINDOW
        self.take_screenshot()
        
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
        self.max_boxes = 200

        self.setup_window()
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)
        
        GLib.timeout_add(100, self.add_new_box)

    def take_screenshot(self):
        # Delete old screenshot if exists
        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)

        try:
            if IS_WAYLAND:
                # Use 'grim' for Wayland
                subprocess.run(["grim", SCREENSHOT_PATH], check=True)
            else:
                # Use 'scrot' for X11
                subprocess.run(["scrot", "--overwrite", SCREENSHOT_PATH], check=True)
        except subprocess.CalledProcessError:
            print("Failed to take screenshot. Screen will be black.")

    def setup_window(self):
        self.fullscreen()
        self.set_decorated(False)
        self.set_keep_above(True)
        
        # WE NO LONGER NEED 'TRUE' TRANSPARENCY SETUP
        # Because we are painting a picture of the desktop, 
        # the window itself can be opaque.
        self.set_app_paintable(True)

    def on_draw(self, widget, cr):
        # 1. Draw the Screenshot (The "Fake" Desktop)
        if self.bg_surface:
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.paint()
        else:
            # Fallback to black if screenshot failed
            cr.set_source_rgb(0, 0, 0)
            cr.paint()

        # 2. Draw all the animation boxes on top
        for box in self.boxes:
            box.draw(cr)

    def add_new_box(self):
        if len(self.boxes) > self.max_boxes:
            self.boxes = [] 
            self.queue_draw()
            return True
            
        # Add a group of boxes (e.g., 5 at a time)
        for _ in range(5):
            new_box = GradientBox(self.width, self.height)
            self.boxes.append(new_box)

        self.queue_draw()
        return True

if __name__ == "__main__":
    win = ScreensaverWindow()
    win.show_all()
    
    def on_key_press(widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            
    win.connect("key-press-event", on_key_press)
    Gtk.main()
