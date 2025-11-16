#!/usr/bin/env python3
import gi
import cairo
import random

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# --- Your Animation Logic Goes Here ---
# Let's create a class to hold the state of one gradient box
class GradientBox:
    def __init__(self, screen_width, screen_height):
        # Pick a random size and position
        self.width = random.randint(50, 200)
        self.height = random.randint(50, 200)
        self.x = random.randint(0, screen_width - self.width)
        self.y = random.randint(0, screen_height - self.height)

        # Create a random gradient
        self.r1, self.g1, self.b1 = (random.random(), random.random(), random.random())
        self.r2, self.g2, self.b2 = (random.random(), random.random(), random.random())
        self.alpha = 0.7 # You wanted a transparent overlay

    def draw(self, cr):
        # This creates the linear gradient
        gradient = cairo.LinearGradient(self.x, self.y, self.x + self.width, self.y + self.height)
        gradient.add_color_stop_rgba(0.0, self.r1, self.g1, self.b1, self.alpha)
        gradient.add_color_stop_rgba(1.0, self.r2, self.g2, self.b2, self.alpha)

        # Draw the rectangle
        cr.set_source(gradient)
        cr.rectangle(self.x, self.y, self.width, self.height)
        cr.fill()

# --- The Main Window Class ---
class ScreensaverWindow(Gtk.Window):
    def __init__(self):
        super().__init__()

        self.screen = self.get_screen()
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()

        # A list to hold all the boxes we've drawn
        # This is how you'll "over lay the previous until the whole screen is full"
        self.boxes = []
        self.max_boxes = 200 # Set a limit

        self.setup_window()
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)

        # This is your animation loop!
        # Call the `self.add_new_box` function every 100ms (0.1 seconds)
        # Adjust this timing for your "stagger" effect
        GLib.timeout_add(100, self.add_new_box)

    def setup_window(self):
        # Make the window fullscreen
        self.fullscreen()
        # Remove title bar, borders, etc.
        self.set_decorated(False)
        # Make it stay on top
        self.set_keep_above(True)
        
        # This is the magic for transparency!
        # We need a screen that supports an "alpha" (transparency) channel
        visual = self.screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        
        # Tell GTK we're drawing on a transparent window
        self.set_app_paintable(True)

    def on_draw(self, widget, cr):
        # On the very first draw, fill with transparent black
        # On subsequent draws, this isn't strictly needed since we're
        # just drawing on top of what's already there.
        if not self.boxes:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()

        # Redraw all existing boxes
        # The prompt said "Each sequence would over lay the previous"
        # To do that, we just draw all of them, every time.
        for box in self.boxes:
            box.draw(cr)

    def add_new_box(self):
        if len(self.boxes) > self.max_boxes:
            # Once the screen is full, you could stop, or...
            # ...reset by clearing the list
            self.boxes = [] 
            
            # To clear the screen fully, we need to re-draw
            self.queue_draw()
            return True # Keep the timer running
            
        # This is your "grouping" of 5-20 boxes
        # Here I just add one for simplicity. You could add a loop
        # to add 5 at a time.
        new_box = GradientBox(self.width, self.height)
        self.boxes.append(new_box)

        # Tell the window it needs to be redrawn
        self.queue_draw()
        
        # Return True to keep the GLib.timeout_add timer running
        return True

# --- Run the Program ---
if __name__ == "__main__":
    win = ScreensaverWindow()
    win.show_all()
    
    # Add a key-press event to quit easily while testing
    def on_key_press(widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            
    win.connect("key-press-event", on_key_press)
    
    Gtk.main()
