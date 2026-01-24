import FreeCAD as App
import Part

def create_lcd_cutout(thickness):
    """Creates a 'negative' of the LCD to cut out of a plate."""
    # 1. Dimensions from the PDF
    [span_2](start_span)v_area_w = 64.50  # Viewing area width[span_2](end_span)
    [span_3](start_span)v_area_h = 14.50  # Viewing area height[span_3](end_span)
    [span_4](start_span)hole_pitch_x = 75.00  #[span_4](end_span)
    [span_5](start_span)hole_pitch_y = 31.00  #[span_5](end_span)
    [span_6](start_span)hole_rad = 1.35       #[span_6](end_span)

    # Create the screen viewing hole
    screen_cut = Part.makeBox(v_area_w, v_area_h, thickness + 2)
    # Center the screen hole (relative to the module center)
    screen_cut.translate(App.Vector(-v_area_w/2, -v_area_h/2, -1))

    # Create the 4 mounting holes
    holes = []
    offsets = [
        (-hole_pitch_x/2, -hole_pitch_y/2),
        (hole_pitch_x/2, -hole_pitch_y/2),
        (hole_pitch_x/2, hole_pitch_y/2),
        (-hole_pitch_x/2, hole_pitch_y/2)
    ]
    
    for x, y in offsets:
        h = Part.makeCylinder(hole_rad, thickness + 2)
        h.translate(App.Vector(x, y, -1))
        holes.append(h)

    # Fuse all "cutout" parts into one tool
    cutout_tool = screen_cut
    for h in holes:
        cutout_tool = cutout_tool.fuse(h)
        
    return cutout_tool

# --- MAIN BUILD ---
doc = App.newDocument("PicoBuild")
plate_thickness = 3.0  # Your variable thickness

# 1. Create the main faceplate
# We make it slightly larger than the LCD module (100x60)
faceplate = Part.makeBox(100, 60, plate_thickness)
faceplate.translate(App.Vector(-50, -30, 0)) # Center it

# 2. Get the LCD "Stamp" and subtract it
lcd_tool = create_lcd_cutout(plate_thickness)
final_plate = faceplate.cut(lcd_tool)

# 3. Add to document
obj = doc.addObject("Part::Feature", "FrontPanel")
obj.Shape = final_plate
doc.recompute()
