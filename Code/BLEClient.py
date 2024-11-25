import sys
import uasyncio as asyncio
import aioble
import bluetooth
import struct
from machine import Pin

# Define the UUIDs to match the server's UUIDs
_ENV_SENSE_UUID = bluetooth.UUID(0x2BA1)
_BUTTON_CHAR_UUID = bluetooth.UUID(0x2A4B)
_LOCK_STATE_CHAR_UUID = bluetooth.UUID(0x1133)

button_pin = Pin(14, Pin.IN, Pin.PULL_DOWN)
green_led = Pin(13, Pin.OUT)
red_led = Pin(12, Pin.OUT)

class BLEClient:
    def __init__(self):
        self.device = None
        self.connection = None
        self.button_characteristic = None
        self.lock_state_characteristic = None

    async def connect(self, device):
        try:
            print("Connecting to", device)
            self.connection = await device.connect()
            print("Connected")
        except asyncio.TimeoutError:
            print("Timeout during connection")
            return

        try:
            print("Discovering services...")
            env_service = await self.connection.service(_ENV_SENSE_UUID)
            self.button_characteristic = await env_service.characteristic(_BUTTON_CHAR_UUID)
            self.lock_state_characteristic = await env_service.characteristic(_LOCK_STATE_CHAR_UUID)
            
            await self.lock_state_characteristic.subscribe(notify=True)
            #await self.lock_state_characteristic.subscribe(notify=True)
            print("Subscribed to lock state characteristics")

        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            return
        
    async def handle_lock_state_notifications(self, value):
        state = value.decode('utf-8')
        print(f"Lock state updated: {state}")
        if state =="Unlocked":
            await self.blink_led(green_led)
        elif state == "Locked":
            await self.blink_led(red_led)
    
    async def blink_led(self, led, times=3, interval=0.5):
        for _ in range(times):
            led.value(1)
            await asyncio.sleep(interval)
            led.value(0)
            await asyncio.sleep(interval)

    async def send_command(self, command):
        try:
            print(f"Sending command: {command}")
            await self.button_characteristic.write(command.encode())
            data = await self.lock_state_characteristic.notified()
            
            state = data.decode('utf-8')
            print(f"Received state: {state}")
            
            if state == "Unlocked":
                await self.blink_led(green_led)
            elif state == "Locked":
                await self.blink_led(red_led)
            
            print (data)
        except asyncio.TimeoutError:
            print("Timeout while sending command. Attempting to reconnect...")
            await self.reconnect()
        except asyncio.TypeError:
            print("Cant send command")


    async def disconnect(self):
        if self.connection:
            await self.connection.disconnect()
            print("Disconnected")
            
    async def monitor_connection(self):
        while True:
            if not self.connection or not self.connection.is_connected():
                print("Connection lost. Attempting to reconnect...")
                await self.reconnect()
            await asyncio.sleep(5)
    
    async def reconnect(self):
        async with aioble.scan(5000, 30000, 30000, active=True) as scanner:
            async for result in scanner:
                if result.name() == "Andreas-write" and _ENV_SENSE_UUID in result.services():
                    device = result.device
                    await self.connect(device)
                    break
            else:
                print("ESP32 server not found. Will retry...")
    
async def button_monitor(client):
    button_state = 1
    last_button_state = 1
    debounce_delay = 0.2
    
    while True:
        current_state = button_pin.value()
        
        if current_state == 1 and last_button_state == 0:
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
    asyncio.create_task(client.monitor_connection())
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    await client.disconnect()
# Run the main function
asyncio.run(main())






