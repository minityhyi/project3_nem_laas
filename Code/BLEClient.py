import sys
import uasyncio as asyncio
import aioble
import bluetooth
import struct
from machine import Pin

# Define the UUIDs to match the server's UUIDs
_ENV_SENSE_UUID = bluetooth.UUID(0x2BA1)
_BUTTON_CHAR_UUID = bluetooth.UUID(0x2A4B)

button_pin = Pin(26, Pin.IN, Pin.PULL_UP)

class BLEClient:
    def __init__(self):
        self._device = None
        self._connection = None
        self._button_characteristic = None

    async def connect(self, device):
        try:
            print("Connecting to", device)
            self._connection = await device.connect()
            print("Connected")
        except asyncio.TimeoutError:
            print("Timeout during connection")
            return

        try:
            print("Discovering services...")
            env_service = await self._connection.service(_ENV_SENSE_UUID)
            self._button_characteristic = await env_service.characteristic(_BUTTON_CHAR_UUID)
        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            return

    async def send_command(self, command):
        print(f"Sending command: {command}")
        await self._button_characteristic.write(command.encode())

    async def disconnect(self):
        if self._connection:
            await self._connection.disconnect()
            print("Disconnected")
    
async def button_monitor(client):
    button_state = 1
    last_button_state = 1
    debounce_delay = 0.2
    
    while True:
        current_state = button_pin.value()
        
        if current_state == 0 and last_button_state == 1:
            print ("Button Pressed")
            await client.send_command("run")
            print("Run command sent")
            await asyncio.sleep(debounce_delay)
        
        last_button_state = current_state
        
        await asyncio.sleep(0.05)

async def main():
    async with aioble.scan(5000, 30000, 30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == "Andreas-write" and _ENV_SENSE_UUID in result.services():
                device = result.device
                break
        else:
            print("ESP32 server not found")
            return

    client = BLEClient()
    await client.connect(device)
    
    asyncio.create_task(button_monitor(client))
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    await client.disconnect()
# Run the main function
asyncio.run(main())


