import network
import urequests
import time

# WiFi credentials
SSID = "thantanmadai"
PASSWORD = "12345678t"

# Firebase details
FIREBASE_URL = "https://iot-database-test-default-rtdb.asia-southeast1.firebasedatabase.app/data.json"

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

# Wait for connection
while not wlan.isconnected():
    print("Connecting to WiFi...")
    time.sleep(1)

print("Connected to WiFi:", wlan.ifconfig())

# Function to send data to Firebase
def send_to_firebase(data):
    response = urequests.patch(FIREBASE_URL, json=data)
    print("Response:", response.text)
    response.close()

# Example data to send
data = {
    "message": "hello, "
}

# Send data to Firebase every 10 seconds
while True:
    send_to_firebase(data)
    print("Da Gui!!")
    time.sleep(10)
    break
