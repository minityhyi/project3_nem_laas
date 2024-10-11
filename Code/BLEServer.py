import uasyncio as asyncio
from machine import Pin
import aioble
import bluetooth
from neopixel import NeoPixel
from time import sleep
import door

_ENV_SENSE_UUID = bluetooth.UUID(0x2BA1)
_BUTTON_CHAR_UUID = bluetooth.UUID(0x2A4B)
_CHAR_PROP_WRITE = const(0x08)
_ADV_INTERVAL_US = const(25000)

class BLEPeripheral:
    def __init__(self):
        self.service = aioble.Service(_ENV_SENSE_UUID)
        self.button_char = aioble.Characteristic(self.service, _BUTTON_CHAR_UUID, write=True, capture=True)
        aioble.register_services(self.service)
        
    async def advertise(self):
        """Start BLE advertising"""
        while True:
            async with await aioble.advertise(
                _ADV_INTERVAL_US,
                name="Andreas-write",
                services=[_ENV_SENSE_UUID],
                appearance=_CHAR_PROP_WRITE
            ) as connection:
				print("Connection from", connection.device)
				await connection.disconnected(timeout_ms=None)
    
    async def receive(self):
        """Handle BLE write commands"""
        while True:
            connection, data = await self.button_char.written()
            data = data.decode('utf-8')
            print("Received:", data)
            await self.process_command(data)
    
    async def process_command(self, command):
        """Process received commands and control motor."""
        if command == "run":
            door.step_motor(512, 0.001)
            
async def main():
    ble = BLEPeripheral()
    t1 = asyncio.create_task(ble.advertise())
    t2 = asyncio.create_task(ble.receive())
    await asyncio.gather(t1, t2)
    
asyncio.run(main())


