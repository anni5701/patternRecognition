import time

import serial
from serial.tools.list_ports import comports


port_name = None

# If none is provided, just take the first one
if port_name is None:
    info = comports()[0]
    port_name = info.device


with serial.Serial(port_name, 9600, timeout=1) as port:

    chunks = []

    while True:
        
        available = port.in_waiting
        if available > 0:
            chunk = port.read(available).decode("ascii")
            
            while "\n" in chunk:
                end = chunk.index("\n") + 1
                chunks.append(chunk[:end])
                
                line = "".join(chunks).rstrip()
                print(line)

                chunks.clear()
                chunk = chunk[end:]
            
            chunks.append(chunk)

        time.sleep(0.1)
