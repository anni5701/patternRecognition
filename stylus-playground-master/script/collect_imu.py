import argparse
import time

import serial
from serial.tools.list_ports import comports

from util import no_interrupt


if __name__ == "__main__":

    # Expect an (optional) port name as argument
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?")
    args = parser.parse_args()

    # Default to the first available port
    if args.port is None:
        info = comports()[0]
        args.port = info.device

    # Open serial port, according to the Arduino parameters
    with serial.Serial(args.port, 9600, timeout=1) as port:

        # Drop first line, in case it was partially read before
        port.readline()

        # Print CSV header
        print("host_timestamp,arduino_timestamp,ax,ay,az,gx,gy,gz,temperature")

        # Run forever
        while True:

            # Fetch a single line
            line = port.readline()

            # Use the most precise clock available
            # Note: this is system-wide, so another process will use the same reference, whatever that is
            timestamp = time.perf_counter_ns()

            # Write without interruption
            line = str(timestamp) + "," + line.decode("ascii").rstrip()
            with no_interrupt():
                print(line)
