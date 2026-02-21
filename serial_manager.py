import serial
import serial.tools.list_ports
import threading
import time
from config_manager import load_config

def list_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

def send_open_command():
    thread = threading.Thread(target=_send_sequence, daemon=True)
    thread.start()

def _send_sequence():
    config = load_config()
    port = config["SERIAL"]["port"]
    baudrate = int(config["SERIAL"]["baudrate"])

    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            # Send unlock
            ser.write(b"$001")
            ser.flush()

            # Wait 1 second
            time.sleep(1)

            # Send lock
            ser.write(b"$000")
            ser.flush()

    except Exception as e:
        print("Serial error:", e)

