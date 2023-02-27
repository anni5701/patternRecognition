import serial
from serial.tools.list_ports import comports

import pyglet


class Reader:
    def __init__(self, port):
        self.port = port
        self.chunks = []

    def update(self):
        lines = []

        available = self.port.in_waiting
        if available > 0:
            chunk = port.read(available).decode("ascii")

            while "\n" in chunk:
                end = chunk.index("\n") + 1
                self.chunks.append(chunk[:end])
                
                line = "".join(self.chunks).rstrip()
                lines.append(line)

                self.chunks.clear()
                chunk = chunk[end:]
            
            self.chunks.append(chunk)

        return lines


port_name = None

# If none is provided, just take the first one
if port_name is None:
    info = comports()[0]
    port_name = info.device


with serial.Serial(port_name, 9600, timeout=1) as port:
    reader = Reader(port)


    window = pyglet.window.Window(1020, 576)


    # TODO could draw stuff, but this seems to work, no need to test more


    def tick(dt):
        lines = reader.update()
        for line in lines:
            print(line)

    pyglet.clock.schedule_interval(tick, 0.1)


    pyglet.app.run()
