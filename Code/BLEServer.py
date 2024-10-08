import asyncio
from machine import Pin
import aioble
import bluetooth
from neopixel import NeoPixel
from time import sleep

rled = Pin(15, Pin.OUT)

# Correct UUIDs
_ENV_SENSE_UUID = bluetooth.UUID(0x2BA1)
_BUTTON_CHAR_UUID = bluetooth.UUID(0x2A4B)
_CHAR_PROP_WRITE = const(0x08)

_ADV_INTERVAL_US = const(250000)

# Correct the service UUID
env_service = aioble.Service(_ENV_SENSE_UUID)

# Create the characteristic with the correct service
button_characteristic = aioble.Characteristic(
    env_service, _BUTTON_CHAR_UUID, write=True, capture=True
)

# Register the services correctly
aioble.register_services(env_service)

# Start advertising in a while loop
async def host():
    while True:
        async with await aioble.advertise(
                _ADV_INTERVAL_US,
                name="Andreas-write",
                services=[_ENV_SENSE_UUID],
                appearance=_CHAR_PROP_WRITE
            ) as connection:
                print("Connection from", connection.device)
                await connection.disconnected(timeout_ms=None)
                
async def recieve():
    while True:
        connection, data = await button_characteristic.written()
        print(data)
        data = data.decode()
        if data == "on":
            rled.value(1)
        elif data =="off":
            rled.value(0)
    
                
async def main():
    t1 = asyncio.create_task(host())
    t2 = asyncio.create_task(recieve())
    await asyncio.gather(t1,t2)
    
asyncio.run(main())

