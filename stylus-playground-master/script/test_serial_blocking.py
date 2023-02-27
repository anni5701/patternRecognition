import serial
from serial.tools.list_ports import comports


port_name = None

# If none is provided, just take the first one
if port_name is None:
    info = comports()[0]
    port_name = info.device


with serial.Serial(port_name, 9600, timeout=1) as port:
    
    # Drop first line, in case it was partially read before
    port.readline()
    
    while True:
        line = port.readline().decode("ascii").rstrip()
        print(line)
