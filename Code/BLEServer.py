import uasyncio as asyncio
from machine import Pin
import aioble
import bluetooth
import time
import door
import wifi
import socket
import urequests


_ENV_SENSE_UUID = bluetooth.UUID(0x2BA1)
_BUTTON_CHAR_UUID = bluetooth.UUID(0x2A4B)
_CHAR_PROP_WRITE = const(0x08)
_ADV_INTERVAL_US = const(25000)

AUTHORIZED_MAC = b'\x94\xb9~kI\xc2'
LOG_FILE = "door_lock_log.csv"

WIFI_SSID = "Licensmanden"
WIFI_PASS = "JbpSg10iN"
UPLOAD_INTERVAL = 12 * 60 * 60

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
                
                client_mac = connection.device.addr
                
                print(f"Attempting connection from MAC: {client_mac}")
                
                if client_mac == AUTHORIZED_MAC:
                    print(f"Authorized client {client_mac} connected")
                    await connection.disconnected(timeout_ms=None)
                else:
                    print(f"Unauthorized client {client_mac} tried to connect. Disconnecting...")
    
    async def receive(self):
        """Handle BLE write commands"""
        while True:
            connection, data = await self.button_char.written()
            data = data.decode('utf-8')
            print("Received:", data)
            await self.process_command(data)
    
    async def upload_log_file(self):
        while True:
            print("Attempting to connect to Wi-Fi...")
            ip = wifi.activate(WIFI_SSID, WIFI_PASS)
            
            if ip:
                print("Wi-Fi connected. IP:", ip)
                
                try:
                    with open(LOG_FILE, 'r') as f:
                        csv_data = f.read()
                        
                    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
                    multipart_data = (
						"--{0}\r\n"
                        'Content-Disposition: form-data; name="file"; filename="door_lock_log.csv"\r\n'
                        "Content-Type: text/csv\r\n\r\n"
                        "{1}\r\n"
						"--{0}--\r\n"
                    ).format(boundary, csv_data)

                    headers = {
                        'Content-Type': 'multipart/form-data; boundary={}'.format(boundary)
                    }
                    
                    url = "http://192.168.99.123:5000/upload"
                        
                    response = urequests.post(url, data=multipart_data, headers=headers)
                    print(f"Server response: {response.status_code}")
                    print(f"Response content: {response.text}")
                    response.close()
                        
                    print("CSV file sent successfully!")
                        
                except Exception as e:
                    print("Error during file upload:", e)
                    
                wifi.disconnect()
                print("Wi-Fi disconnected. Re-enabling BLE advertising..")
                
            await asyncio.sleep(UPLOAD_INTERVAL)


    
    async def process_command(self, command):
        """Process received commands and control motor."""
        if command == "run":
            door.step_motor(512, 0.001)
            self.log_activation()
            
    def log_activation(self):
        timestamp = time.localtime()
        timestamp_str = f"{timestamp[0]}-{timestamp[1]:02}-{timestamp[2]:02} {timestamp[3]:02}:{timestamp[4]:02}:{timestamp[5]:02}"
        action = "Lock Activated"
        try:
            with open(LOG_FILE, 'a') as f:
                if f.tell() == 0:
                    f.write(f"{timestamp_str},{action}\n")
                f.write(f"{timestamp_str},{action}\n")
        except OSError as e:
            print("Error writing to log file:", e)
            
async def main():
    ble = BLEPeripheral()
    t1 = asyncio.create_task(ble.advertise())
    t2 = asyncio.create_task(ble.receive())
    t3 = asyncio.create_task(ble.upload_log_file())
    await asyncio.gather(t1, t2, t3)
    
asyncio.run(main())

















