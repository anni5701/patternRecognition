from dataclasses import dataclass
import math
import time

import pyglet

from util import no_interrupt


# Enumerate input devices
# TODO pyglet's tablet objects seem to provide less details, but I may be wrong...
devices = pyglet.input.get_devices()
for device in devices:

    # Search by name
    if device.name == "Wacom Tablet":

        # The tablet appears twice, we need the one that has more information
        # TODO better way to check for that?
        controls = device.get_controls()
        if len(controls) == 17:
            break

else:
    raise RuntimeError("Wacom tablet not found")


# Get tablet axes
control_map = {control.raw_name: control for control in controls}
#print(list(control_map))
control_x = control_map["X-Achse"]
control_y = control_map["Y-Achse"]
control_z = control_map["Z-Achse"]
control_in_range = control_map["Im Bereich"]
control_switch = control_map["Tippschalter"]
control_pressure = control_map["Druckempfindliche Spitze"]


# Open window
window = pyglet.window.Window(1020, 576, resizable=True)
device.open(window)


# Use simple crosshair cursor
cursor = window.get_system_mouse_cursor(window.CURSOR_CROSSHAIR)
window.set_mouse_cursor(cursor)


# Wrap state in an object, for convenience
@dataclass
class State:
    x: int
    y: int
    z: int
    in_range: int
    switch: int
    pressure: int
    reset: int


# Initial state is zero
state = State(0, 0, 0, 0, 0, 0, 0)


# Rendering stuff
batch = pyglet.graphics.Batch()
circles = []
lines = []
is_drawing = False
old_x = 0
old_y = 0


@control_x.event
def on_change(value):
    state.x = value


@control_y.event
def on_change(value):
    state.y = value


@control_z.event
def on_change(value):
    state.z = value


@control_in_range.event
def on_change(value):
    state.in_range = int(value)


@control_switch.event
def on_change(value):
    state.switch = int(value)


@control_pressure.event
def on_change(value):
    state.pressure = value


@window.event
def on_mouse_enter(x, y):
    ...


@window.event
def on_mouse_leave(x, y):
    ...


@window.event
def on_mouse_press(x, y, button, modifiers):
    ...


@window.event
def on_mouse_release(x, y, button, modifiers):
    ...


@window.event
def on_mouse_motion(x, y, dx, dy):
    ...


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    ...


@window.event
def on_key_press(symbol, modifiers):

    # Use space bar to reset screen
    if symbol == pyglet.window.key.SPACE:
        state.reset = 1


@window.event
def on_key_release(symbol, modifiers):
    ...


@window.event
def on_draw():
    window.clear()
    batch.draw()


# Print CSV header
print("host_timestamp,x,y,z,in_range,touch,pressure,reset")


def on_tick(dt):
    global is_drawing, old_x, old_y

    # Use the same system-wide clock as `collect_imu.py`
    timestamp = time.perf_counter_ns()
    
    # Planar coordinates are in normalized screen space (i.e. both X and Y are in [0, 65535], regardless of screen resolution)
    # Note: make sure to enable Force Proportion in Wacom Tablet Properties!
    window_x, window_y = window.get_location()
    window_width, window_height = window.size
    screen_width = window.screen.width
    screen_height = window.screen.height
    true_x = state.x / 65535 * screen_width - window_x
    true_y = window_height - state.y / 65535 * screen_height + window_y

    # Output sampled signal
    values = (
        timestamp,
        true_x,
        true_y,
        state.z,
        state.in_range,
        state.switch,
        state.pressure,
        state.reset,
    )
    with no_interrupt():
        print(",".join(map(str, values)))

    # Only draw a line if there was a change
    if is_drawing and (true_x != old_x or true_y != old_y):
        line = pyglet.shapes.Line(old_x, old_y, true_x, true_y, color=(255, 255, 255, 255), batch=batch)
        lines.append(line)

    # Start drawing on touch
    if not is_drawing and state.switch:
        circle = pyglet.shapes.Circle(true_x, true_y, 5, color=(255, 255, 255, 255), batch=batch)
        circles.append(circle)
        is_drawing = True

    # Stop drawing if left button is released
    if not state.switch:
        is_drawing = False

    # Reset also clears the screen
    if state.reset:
        is_drawing = False
        lines.clear()
        circles.clear()

    # Update state
    old_x = true_x
    old_y = true_y
    state.reset = 0


# Try to run at 100Hz
# Note: in practice, it will be slower than that
sample_rate = 100
pyglet.clock.schedule_interval(on_tick, 1 / sample_rate)


# Let pyglet handle the main loop
pyglet.app.run()
