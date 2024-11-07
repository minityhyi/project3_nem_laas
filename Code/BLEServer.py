import uasyncio as asyncio
from machine import Pin
import aioble
import bluetooth
import time
import door
import wifi
import urequests
import sys
import select


_ENV_SENSE_UUID = bluetooth.UUID(0x2BA1)
_BUTTON_CHAR_UUID = bluetooth.UUID(0x2A4B)
_CHAR_PROP_WRITE = const(0x08)
_ADV_INTERVAL_US = const(25000)
_LOCK_STATE_CHAR_UUID = bluetooth.UUID(0x2A5B)

'''AUTHORIZED_MAC = b'\x94\xb9~kI\xc2'
WIFI_SSID = "Licensmanden"
WIFI_PASS = "JbpSg10iN"'''

SETTINGS_FILE = "settings.txt"
LOG_FILE = "door_lock_log.csv"
UPLOAD_INTERVAL = 12 * 60 * 60


class Config:
    def __init__(self):
        self.settings = {}
        self.load_settings()
        
    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                for line in f:
                    key, value = line.strip().split('=')
                    if key == 'authorized_mac':
                        self.settings[key] = bytes.fromhex(value)
                    else:
                        self.settings[key] = value
                print("Settings loaded:", self.settings)
        
        except OSError:
            print("No settings file found. Using default values.")
                
            self.settings = {
                'wifi_ssid': 'ittek#1_2.4G',
                'wifi_pass': 'MaaGodt*7913',
                'authorized_mac': bytes.fromhex('94b97e6b49c2'),
                'advertising_name': 'Andreas-write'
            }
    
    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f:
            for key, value in self.settings.items():
                if isinstance(value, bytes):
                    f.write(f"{key}={value.hex}\n")
                else:
                    f.write(f"{key}={value}\n")
            print("Settings saved:", self.settings)
    
    def configure(self):
        self.settings['wifi_ssid'] = input("Enter Wi-Fi SSID: ")
        self.settings['wifi_pass'] = input("Enter Wi-Fi Pass: ")
        self.settings['authorized_mac'] = input("Enter Authorized MAC Address: ")
        self.settings['advertising_name'] = input("Enter advertising name: ")
        self.save_settings()


class BLEPeripheral:
    def __init__(self, config):
        self.config = config	
        self.service = aioble.Service(_ENV_SENSE_UUID)
        self.button_char = aioble.Characteristic(self.service, _BUTTON_CHAR_UUID, write=True, capture=True)
        aioble.register_services(self.service)
        self.load_configuration()
        self.current_direction = 1
        
    async def advertise(self):
        """Start BLE advertising"""
        while True:
            async with await aioble.advertise(
                _ADV_INTERVAL_US,
                name=self.config.settings['advertising_name'],
                services=[_ENV_SENSE_UUID],
                appearance=_CHAR_PROP_WRITE
            ) as connection:
                
                client_mac = connection.device.addr
                
                print(f"Attempting connection from MAC: {client_mac}")
                
                authorized_mac_bytes = self.config.settings['authorized_mac']
                
                if client_mac == authorized_mac_bytes:
                    print(f"Authorized client {client_mac} connected")
                    await connection.disconnected(timeout_ms=None)
                else:
                    print(f"Unauthorized client {client_mac} tried to connect. Disconnecting...")
    
    def load_configuration(self):
        print("Current configuration:")
        print(f"SSID: {self.config.settings['wifi_ssid']}")
        print(f"Authorized MAC: {self.config.settings['authorized_mac']}")
        print(f"Advertising Name: {self.config.settings['advertising_name']}")
    
    async def wait_for_enter(self, timeout):
        print("Press Enter within {} seconds to configure settings...".format(timeout))
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                input()  # Read the input, this should not block
                return True
            await asyncio.sleep(0.1)
        return False
    
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
            ip = wifi.activate(self.config.settings['wifi_ssid'], self.config.settings['wifi_pass'])
            
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
            if self.current_direction == 1:
                door.step_motor(100, 0.001, door.seq_clockwise)
            else:
                door.step_motor(100, 0.001, door.seq_counterclockwise)
            
            self.current_direction*= -1
        else:
            print("Unknown command received.")
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
            
    async def main(self):
        if await self.wait_for_enter(5):
            self.config.configure()
        else:
            print("Using existing configuration form settings.txt")
            self.load_configuration()
            
            
async def main():
    config = Config()
    ble = BLEPeripheral(config)
    
    await ble.main()
    
    t1 = asyncio.create_task(ble.advertise())
    t2 = asyncio.create_task(ble.receive())
    t3 = asyncio.create_task(ble.upload_log_file())
    await asyncio.gather(t1, t2, t3)
    
asyncio.run(main())
