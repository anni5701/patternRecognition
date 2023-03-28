

from collections import deque

import numpy as np

import matplotlib.pyplot as plt

import serial
from serial.tools.list_ports import comports


port_name = None

# If none is provided, just take the first one
if port_name is None:
    info = comports()[0]
    port_name = info.device


with serial.Serial(port_name, 9600, timeout=1) as port:

    # Create interactive figure
    plt.ion()
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(6, 4))
    (line_Ax,) = axes[0].plot([], [], c="r", alpha=0.5)
    (line_Ay,) = axes[0].plot([], [], c="g", alpha=0.5)
    (line_Az,) = axes[0].plot([], [], c="b", alpha=0.5)
    (line_Gx,) = axes[1].plot([], [], c="r", alpha=0.5)
    (line_Gy,) = axes[1].plot([], [], c="g", alpha=0.5)
    (line_Gz,) = axes[1].plot([], [], c="b", alpha=0.5)
    axes[1].set_xlabel("time [s]")
    axes[0].set_ylabel("acceleration [g]")
    axes[1].set_ylabel("angular velocity [rad/s]")
    plt.tight_layout()

    # Buffers
    T = deque()
    Ax = deque()
    Ay = deque()
    Az = deque()
    Gx = deque()
    Gy = deque()
    Gz = deque()

    # Drop first line, in case it was partially read before
    port.readline()

    while True:

        # Read a few lines, without updating the plot
        for _ in range(10):

            # Wait for next line
            line = port.readline().decode("ascii").rstrip()

            # Parse values
            t, ax, ay, az, gx, gy, gz, _ = map(float, line.split(","))

            # Update buffers
            T.append(t * 1e-3)
            Ax.append(ax)
            Ay.append(ay)
            Az.append(az)
            Gx.append(gx)
            Gy.append(gy)
            Gz.append(gz)

        # Drop old data points
        while T[-1] - T[0] > 5.0:
            T.popleft()
            Ax.popleft()
            Ay.popleft()
            Az.popleft()
            Gx.popleft()
            Gy.popleft()
            Gz.popleft()

        # Update data
        line_Ax.set_data(T, Ax)
        line_Ay.set_data(T, Ay)
        line_Az.set_data(T, Az)
        line_Gx.set_data(T, Gx)
        line_Gy.set_data(T, Gy)
        line_Gz.set_data(T, Gz)
        axes[0].set_xlim(min(T), max(T))
        A_max = np.abs([*Ax, *Ay, *Az]).max()
        axes[0].set_ylim(-A_max, A_max)
        G_max = np.abs([*Gx, *Gy, *Gz]).max()
        axes[1].set_ylim(-G_max, G_max)

        # Redraw and handle window events
        fig.canvas.draw()
        fig.canvas.flush_events()

