
import pyglet


tablets = pyglet.input.get_tablets()

assert len(tablets) > 0
tablet = tablets[0]

print(tablet.name)

window = pyglet.window.Window(1020, 576)
canvas = tablet.open(window)


@canvas.event
def on_enter(cursor):
    print("enter", cursor)


@canvas.event
def on_leave(cursor):
    print("leave", cursor)


@canvas.event
def on_motion(cursor, x, y, pressure, a, b, is_touching):
    print("motion", cursor, x, y, pressure, is_touching)


pyglet.app.run()
