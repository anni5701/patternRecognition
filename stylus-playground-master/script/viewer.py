import argparse
import logging

import numpy as np

import serial
from serial.tools.list_ports import comports

from direct.gui.DirectGui import DirectLabel
from direct.showbase.ShowBase import ShowBase
from direct.stdpy import threading

from panda3d.core import (
    LMatrix4,
    LQuaternion,
    Material,
    Spotlight,
    TextNode,
    TransformState,
    Vec3,
    loadPrcFileData,
)


# Run serial port management in background thread
class IMU:
    def __init__(self, port, on_event=None):
        self.port = port
        self.on_event = on_event
        self.abort = False
        self.thread = None
        self.event = 0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

    def open(self):
        assert self.thread is None
        self.abort = False
        self.thread = threading.Thread(target=self.run, name="IMU")
        self.thread.start()

    def close(self):
        self.abort = True
        self.thread.join()
        self.thread = None

    def run(self):
        
        # Connect to serial device
        with serial.Serial(args.port, 9600, timeout=1) as port:
        
            # Drop first line, in case it was partially read before
            port.readline()
            
            # Loop until the end
            while not self.abort:
                line = port.readline().decode("ascii")
                
                t, ax, ay, az, gx, gy, gz, _ = line.rstrip().split(",")
                t = int(t)
                a = float(ax), float(ay), float(az)
                g = float(gx), float(gy), float(gz)
                
                a = np.array(a)
                g = np.array(g)
                
                self.event = t, a, g
                
                on_event = self.on_event
                if on_event is not None:
                    on_event(t, a, g)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.close()


class Viewer(ShowBase):
    def __init__(self):
        super().__init__(self)

        # Add ground plane
        plane = self.loader.loadModel("../data/square.obj")
        plane.reparentTo(self.render)
        plane.setScale(20, 20, 1)

        # Create axes
        self.ax = self.make_axes()
        self.ax.setPos(0, 0, 1)

        # Add arrow for acceleration
        self.acc = self.make_arrow("A", (1.0, 0.8, 0.2, 1.0))
        self.acc.reparentTo(self.ax)
        self.update_arrow(self.acc, np.array([0.0, 0.0, 0.0]))

        # We need a monospaced font for the label to look pretty
        font = loader.loadFont("../data/RobotoMono-Regular.ttf")

        # Create label for current timestamp
        self.label = DirectLabel(
            text="-:--:--.--",
            pos=(-1.05, 0, -0.9),
            scale=0.05,
            text_align=TextNode.ARight,
            text_font=font,
            text_fg=(1, 0.5, 0.5, 1),
            frameColor=(0, 0, 0, 0),
        )

        # A simple spotlight
        spotlight = Spotlight("Spotlight")
        spotlight.setColorTemperature(6000)
        spotlight.setShadowCaster(True, 2048, 2048)
        # spotlight.showFrustum()
        spotlight = self.render.attachNewNode(spotlight)
        spotlight.setPos(-2, -5, 30)
        spotlight.lookAt(plane)
        self.render.setLight(spotlight)

        # Automatically generate the required shaders (for shadow mapping)
        self.render.setShaderAuto()

        # Set camera center on the origin of the device
        # TODO better mouse controller, this one is painful...
        self.trackball.node().setOrigin((0, 0, 1))
        self.trackball.node().setY(50)
        self.trackball.node().setP(30)

    def make_arrow(self, name=None, color=(1.0, 1.0, 1.0, 1.0)):
        arrow = self.loader.loadModel("../data/arrow.obj")
        material = Material()
        material.setDiffuse(color)
        arrow.setMaterial(material, 1)
        if name is not None:
            arrow.setName(name)
        return arrow

    def make_axes(self, scale=1.0):
        axes = self.render.attachNewNode("Axes")
        arrow_x = self.make_arrow("X", (1.0, 0.2, 0.2, 1.0))
        arrow_x.setScale(scale)
        arrow_x.reparentTo(axes)
        arrow_y = self.make_arrow("Y", (0.2, 1.0, 0.2, 1.0))
        arrow_y.setH(90)
        arrow_y.setScale(scale)
        arrow_y.reparentTo(axes)
        arrow_z = self.make_arrow("Z", (0.2, 0.2, 1.0, 1.0))
        arrow_z.setR(270)
        arrow_z.setScale(scale)
        arrow_z.reparentTo(axes)
        return axes

    def update_arrow(self, arrow, vector):

        # Compute length
        # Note: small arrows are just hidden
        length = np.sqrt(vector @ vector)
        if length < 0.01:
            arrow.hide()
            return
        arrow.show()

        # Compute local frame
        x = vector / length
        up = np.array([0.0, 0.0, 1.0])
        if abs(x @ up) > 0.9:
            up = np.array([1.0, 0.0, 0.0])
        y = np.cross(up, x)
        y /= np.sqrt(y @ y)
        z = np.cross(x, y)

        # Uniform scaling
        x *= length
        y *= length
        z *= length

        # Compute transformation matrix
        if np.isnan(x).any() or np.isnan(y).any() or np.isnan(z).any():
            return
        matrix = LMatrix4(*x, 0.0, *y, 0.0, *z, 0.0, 0.0, 0.0, 0.0, 1.0)
        transform = TransformState.makeMat(matrix)
        arrow.setTransform(transform)

    def on_event(self, t, a, g):

        # Show time
        t /= 1000.0
        h, r = divmod(t, 3600)
        m, r = divmod(r, 60)
        s, r = divmod(r, 1)
        time = f"{int(h):d}:{int(m):02d}:{int(s):02d}.{int(r*1000):03d}"
        self.label["text"] = time
        
        # Update position
        # TODO get position somehow
        p = (0.0, 0.0, 1.0)
        
        # Update orientation
        # TODO get quaternion somehow
        q = (1.0, 0.0, 0.0, 0.0)
        self.ax.setQuat(LQuaternion(*q))

        # Update acceleration vector
        # Note: scaling the force, to avoid large arrow
        self.update_arrow(self.acc, a / 10.0)


if __name__ == "__main__":

    # Configure simple logging strategy
    logging.basicConfig(level=logging.DEBUG)

    # Setup panda3d
    config = """
    win-size 1280 720
    window-title Viewer
    show-frame-rate-meter True
    load-file-type p3assimp
    model-cache-dir
    """
    loadPrcFileData("", config)

    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?")
    args = parser.parse_args()
    if args.port is None:
        info = comports()[0]
        args.port = info.device

    # Run app
    viewer = Viewer()
    with IMU(args.port, viewer.on_event) as imu:
        viewer.run()
