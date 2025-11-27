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
BOXES_PER_CYCLE = 5   
MAX_BOXES = 300       
SAFE_DELAY = 1.0      

class GradientBox:
    def __init__(self, screen_width, screen_height):
        # Random Size
        self.width = random.randint(50, 250)
        self.height = random.randint(50, 250)
        # Random Position
        self.x = random.randint(0, screen_width - self.width)
        self.y = random.randint(0, screen_height - self.height)
        
        # Random Colors for Gradient
        self.r1, self.g1, self.b1 = (random.random(), random.random(), random.random())
        self.r2, self.g2, self.b2 = (random.random(), random.random(), random.random())
        self.alpha = 0.8 

    def draw(self, cr):
        gradient = cairo.LinearGradient(self.x, self.y, self.x + self.width, self.y + self.height)
        gradient.add_color_stop_rgba(0.0, self.r1, self.g1, self.b1, self.alpha)
        gradient.add_color_stop_rgba(1.0, self.r2, self.g2, self.b2, self.alpha)
        cr.set_source(gradient)
        cr.rectangle(self.x, self.y, self.width, self.height)
        cr.fill()

class ScreensaverWindow(Gtk.Window):
    def __init__(self):
        self.start_time = time.time()
        
        # 1. Take Screenshot
        self.take_screenshot()
        
        super().__init__()
        
        # 2. Get Screen Size 
        self.calculate_screen_size()

        # Load screenshot
        try:
            self.bg_surface = cairo.ImageSurface.create_from_png(SCREENSHOT_PATH)
        except Exception as e:
            print(f"Background load failed: {e}")
            self.bg_surface = None

        self.boxes = []
        self.setup_window()
        
        # 3. Connect Signals
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)
        
        # CRITICAL FIX: Only hide cursor AFTER window is realized
        self.connect("realize", self.on_realize)
        
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | 
                        Gdk.EventMask.BUTTON_PRESS_MASK | 
                        Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("motion-notify-event", self.quit_app)
        self.connect("button-press-event", self.quit_app)
        self.connect("key-press-event", self.quit_app)

        GLib.timeout_add(100, self.add_new_box)

    def calculate_screen_size(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        if monitor:
            geometry = monitor.get_geometry()
            self.width = geometry.width
            self.height = geometry.height
        else:
            # Fallback if monitor detection fails
            self.width = 1920
            self.height = 1080

    def take_screenshot(self):
        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)

        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
        
        try:
            if "GNOME" in desktop or "UBUNTU" in desktop:
                # GNOME needs the 'gnome-screenshot' package
                subprocess.run(["gnome-screenshot", "-f", SCREENSHOT_PATH], check=True)
            elif "WAYLAND_DISPLAY" in os.environ:
                subprocess.run(["grim", SCREENSHOT_PATH], check=True)
            else:
                subprocess.run(["scrot", "--overwrite", SCREENSHOT_PATH], check=True)
        except Exception as e:
            print(f"Screenshot failed: {e}")

    def setup_window(self):
        self.fullscreen()
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_app_paintable(True)
        # REMOVED: Cursor setting here caused the crash

    def on_realize(self, widget):
        # This runs only when the window is actually created on screen
        cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.BLANK_CURSOR)
        window = self.get_window()
        if window:
            window.set_cursor(cursor)

    def on_draw(self, widget, cr):
        if self.bg_surface:
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0, 0, 0)
            cr.paint()

        for box in self.boxes:
            box.draw(cr)

    def add_new_box(self):
        if len(self.boxes) > MAX_BOXES:
            self.boxes = []
            self.queue_draw()
            return True
            
        for _ in range(BOXES_PER_CYCLE):
            self.boxes.append(GradientBox(self.width, self.height))

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
