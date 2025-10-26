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

