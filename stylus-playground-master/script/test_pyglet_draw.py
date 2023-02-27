import random

import pyglet


window = pyglet.window.Window(1020, 576)


cursor = window.get_system_mouse_cursor(window.CURSOR_CROSSHAIR)
window.set_mouse_cursor(cursor)


class Handler:
    def __init__(self):
        self.is_drawing = False
        self.old_x = 0
        self.old_y = 0
        self.batch = pyglet.graphics.Batch()
        # TODO could maybe put each set of lines in a group?
        self.circles = []
        self.lines = []
        self.color = None

    def begin(self, x, y):
        self.end()
        self.is_drawing = True
        self.old_x = x
        self.old_y = y
        self.color = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255
        circle = pyglet.shapes.Circle(x, y, 5, color=self.color, batch=self.batch)
        self.circles.append(circle)
    
    def update(self, x, y):
        if self.is_drawing:
            if self.old_x != x or self.old_y != y:
                line = pyglet.shapes.Line(self.old_x, self.old_y, x, y, color=self.color, batch=self.batch)
                self.lines.append(line)
        self.old_x = x
        self.old_y = y
        
    def end(self):
        if self.is_drawing:
            self.is_drawing = False

    def clear(self):
        self.end()
        self.circles.clear()
        self.lines.clear()


handler = Handler()


@window.event
def on_mouse_enter(x, y):
    pass


@window.event
def on_mouse_leave(x, y):
    handler.update(x, y)
    handler.end()


@window.event
def on_mouse_press(x, y, button, modifiers):
    if button & pyglet.window.mouse.LEFT:
        handler.begin(x, y)


@window.event
def on_mouse_release(x, y, button, modifiers):
    if button & pyglet.window.mouse.LEFT:
        handler.update(x, y)
        handler.end()


@window.event
def on_mouse_motion(x, y, dx, dy):
    handler.update(x, y)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    handler.update(x, y)


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        handler.clear()


@window.event
def on_key_release(symbol, modifiers):
    pass


@window.event
def on_draw():
    window.clear()
    handler.batch.draw()


pyglet.app.run()
