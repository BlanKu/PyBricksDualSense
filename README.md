# 🚘 PyBricksDualSense [Lego Spike Prime]

Control your LEGO SPIKE Prime or Robot Inventor robot over Bluetooth using Python and the Pybricks firmware. 
The project enables real-time motor control from your PC (and optionally a PS5 controller 🎮) through simple BLE text commands.

## 🧩 Project Overview

This project connects a Python script running on a computer to a LEGO hub running Pybricks via Bluetooth Low Energy (BLE).
The PC sends commands such as fwd, rev, stp, and the hub interprets and executes them instantly.

It’s a minimal, fast, and flexible communication system between your computer and the LEGO hub — ideal for robotics experiments, remote control, or custom automation setups.

## ⚙️ Features

- Bluetooth (BLE) communication between PC and LEGO Hub
- Real-time command execution
- Support for text-based control commands:

Command	Description
|fwd	| Move forward |
|-------|--------------|
|rev	| Move backward |
|stp	| Stop motors |
|lfw	| Left turn|
|rfw |Right turn|
|lre |Left back turn|
|rre |Right back turn
|bye	| Terminate the program |

The hub responds with "rdy" when it’s ready for the next command.
Optional PS5 controller input via pydualsense.

## 🧠 Architecture
On the PC (WINDOWS)

Python 3.10+

|Bleak: | for Bluetooth LE communication |
|--------------|-------------------|
|pydualsense |  (optional) for PS5 controller input |

Script that sends commands to the hub (remoteControllerPS5.py)

### On the LEGO Hub (Pybricks):

Pybricks Firmware v3.3+

Custom MicroPython script (hubCode.py) that listens for BLE input and drives motors.

## 💻 Example Usage

**On Hub:**

```py
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait

# Standard MicroPython modules
from usys import stdin, stdout
from uselect import poll

motorR = Motor(Port.A)
motorL = Motor(Port.B)

# Optional: Register stdin for polling. This allows
# you to wait for incoming data without blocking.
keyboard = poll()
keyboard.register(stdin)

while True:

    # Let the remote program know we are ready for a command.
    stdout.buffer.write(b"rdy")

    # Optional: Check available input.
    while not keyboard.poll(0):
        # Optional: Do something here.
        wait(1)

    # Read three bytes.
    cmd = stdin.buffer.read(3)

    # Decide what to do based on the command.
    if cmd == b"fwd":
        motorR.dc(-50)
        motorL.dc(50)
    elif cmd == b"rev":
        motorR.dc(50)
        motorL.dc(-50)
    elif cmd == b"stp":
        motorR.stop()
        motorL.stop()
    elif cmd == b"rfw":
        motorL.dc(25)
        motorR.dc(-50)
    elif cmd == b"lfw":
        motorR.dc(-25)
        motorL.dc(50)
    elif cmd == b"rre":
        motorL.dc(-25)
        motorR.dc(50)
    elif cmd == b"lre":
        motorR.dc(25)
        motorL.dc(-50)
    elif cmd == b"bye":
        break
    else:
        motorR.stop()
        motorL.stop()
```

**On PC:**

```py
import asyncio
from contextlib import suppress
from bleak import BleakScanner, BleakClient
from pydualsense import pydualsense, TriggerModes

PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"
HUB_NAME = "Pybricks Hub"
TIME_BETWEEN_ACTIONS = 0.1

#
ds = pydualsense()
ds.init()

ds.light.setColorI(0,255,0)


async def main():
    main_task = asyncio.current_task()

    def handle_disconnect(_):
        print("Hub disconnected.")

        if not main_task.done():
            main_task.cancel()

    ready_event = asyncio.Event()

    def handle_rx(_, data: bytearray):
        if data[0] == 0x01:  # "write stdout" event (0x01)
            payload = data[1:]

            if payload == b"rdy":
                ready_event.set()
            else:
                print("Received:", payload)

    # Do a Bluetooth scan to find the hub.
    device = await BleakScanner.find_device_by_name(HUB_NAME)

    if device is None:
        print(f"could not find hub with name: {HUB_NAME}")
        return

    # Connect to the hub.
    async with BleakClient(device, handle_disconnect) as client:

        # Subscribe to notifications from the hub.
        await client.start_notify(PYBRICKS_COMMAND_EVENT_CHAR_UUID, handle_rx)

        # Shorthand for sending some data to the hub.
        async def send(data):
            # Wait for hub to say that it is ready to receive data.
            await ready_event.wait()
            # Prepare for the next ready event.
            ready_event.clear()
            # Send the data to the hub.
            await client.write_gatt_char(
                PYBRICKS_COMMAND_EVENT_CHAR_UUID,
                b"\x06" + data,  # prepend "write stdin" command (0x06)
                response=True
            )

        # Tell user to start program on the hub.
        print("Start the program on the hub now with the button.")

        # Send a few messages to the hub.

        while True:
            if ds.state.R2_value and not ds.state.DpadRight and not ds.state.DpadLeft:
                await send(b"fwd")
                await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                print("Send: fwd")
                print(".", end="", flush=True)
                if ds.state.R2_value < 10:
                    await send(b"stp")
                    await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                    print("Send: stp")
                    print(".", end="", flush=True)

            if ds.state.R2_value > 10 and ds.state.DpadRight:
                await send(b"rfw")
                await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                print("Send: rfw")
                print(".", end="", flush=True)
                if ds.state.R2_value < 10:
                    await send(b"stp")
                    await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                    print("Send: stp")
                    print(".", end="", flush=True)

            if ds.state.R2_value > 10 and ds.state.DpadLeft:
                await send(b"lfw")
                await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                print("Send: lfw")
                print(".", end="", flush=True)
                if ds.state.R2_value < 10:
                    await send(b"stp")
                    await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                    print("Send: stp")
                    print(".", end="", flush=True)

            if ds.state.L2_value > 10 and not ds.state.DpadRight and not ds.state.DpadLeft:
                await send(b"rev")
                await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                print("Send: rev")
                print(".", end="", flush=True)
                if ds.state.L2_value < 10:
                    await send(b"stp")
                    await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                    print("Send: stp")
                    print(".", end="", flush=True)

            if ds.state.L2_value > 10 and ds.state.DpadRight:
                await send(b"rre")
                await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                print("Send: rre")
                print(".", end="", flush=True)
                if ds.state.L2_value < 10:
                    await send(b"stp")
                    await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                    print("Send: stp")
                    print(".", end="", flush=True)

            if ds.state.L2_value > 10 and ds.state.DpadLeft:
                await send(b"lre")
                await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                print("Send: lre")
                print(".", end="", flush=True)
                if ds.state.L2_value < 10:
                    await send(b"stp")
                    await asyncio.sleep(TIME_BETWEEN_ACTIONS)
                    print("Send: stp")
                    print(".", end="", flush=True)

        # Send a message to indicate stop.
        await send(b"bye")

        print("done.")

    # Hub disconnects here when async with block exits.


# Run the main async program.
if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())
```

## 📦 Dependencies

Install the required libraries on your PC:

```bash
pip install bleak pydualsense asyncio
```

# 🧱 Hardware Setup

- LEGO SPIKE Prime or Robot Inventor Hub
- 2 motors (e.g., Ports A and B)
- Computer with Bluetooth LE and Python 3.10+
- DualSense PS5 Controller (USB or Bluetooth)

# 📄 License

This project is released under the MIT License.
Feel free to use, modify, and share.