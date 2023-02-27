
import pyglet


devices = pyglet.input.get_devices()

for device in devices:
    if device.name == "Wacom Tablet":
        
        controls = device.get_controls()
        
        # The tablet appears twice, we need the one that has more information
        # TODO better way to check for that?
        if len(controls) == 17:
            break

else:
    raise RuntimeError("Wacom tablet not found")


control_map = {control.raw_name: control for control in controls}

# Coordinate in plane
control_x = control_map["X Axis"]
control_y = control_map["Y Axis"]

# "button" activated when in range
control_in_range = control_map["In Range"]

# Distance to surface (when in range)
control_z = control_map["Z Axis"]

# Pressure on the tip (when touching the surface)
# Note: it seems that pressing a button on the pen triggers that as well?
control_pressure = control_map["Tip Pressure"]

# TODO more controls?


window = pyglet.window.Window(1020, 576)
canvas = device.open(window)

# TODO isn't canvas supposed to be something?


@control_x.event
def on_change(e):
    print(e)

@control_in_range.event
def on_change(e):
    print(e)

# TODO handle events properly


pyglet.app.run()
