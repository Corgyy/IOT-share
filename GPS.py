from machine import UART, Pin
import time
import network
import urequests

# Initialize internal LED
internalLED = Pin('LED', Pin.OUT)

# WiFi credentials
SSID = "thantanmadai"
PASSWORD = "12345678t"

# Firebase details
FIREBASE_URL = "https://iot-database-test-default-rtdb.asia-southeast1.firebasedatabase.app/data.json"

# Initialize UART for GPS
uart = UART(0, 9600)

def convert_to_decimal(raw_value, direction):
    """Chuyển từ dạng ddmm.mmmm sang decimal degrees"""
    if not raw_value or raw_value == '':
        return None
    try:
        degrees = int(float(raw_value) / 100)
        minutes = float(raw_value) - degrees * 100
        decimal = degrees + minutes / 60
        if direction in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 6)
    except:
        return None

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('Đang chờ kết nối...')
    time.sleep(1)

if wlan.isconnected():
    print('Đã kết nối WiFi!')
    print('Thông tin mạng:', wlan.ifconfig())
else:
    print('Kết nối thất bại.')
    while True:
        internalLED.on()
        time.sleep(0.5)
        internalLED.off()
        time.sleep(0.5)

# Function to send data to Firebase with retry mechanism
def send_to_firebase(data):
    max_retries = 3
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            response = urequests.request('PUT', FIREBASE_URL, json=data)
            print("Response:", response.text)
            response.close()
            # Blink LED fast to indicate success
            for _ in range(3):
                internalLED.on()
                time.sleep(0.1)
                internalLED.off()
                time.sleep(0.1)
            return True
        except Exception as e:
            print(f"Error sending to Firebase (attempt {attempt + 1}/{max_retries}):", e)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    # Blink LED slow to indicate failure
    internalLED.on()
    time.sleep(0.5)
    internalLED.off()
    time.sleep(0.5)
    return False

# Main loop
last_send_time = 0
last_valid_data = None
while True:
    current_time = time.time()
    
    if uart.any():
        line = uart.readline()
        try:
            sentence = line.decode('utf-8').strip()
            print("NMEA:", sentence)  # Debug: In tất cả câu NMEA
            if sentence.startswith('$GPRMC'):
                parts = sentence.split(',')
                if len(parts) > 6 and parts[2] == 'A':  # GPS fix valid
                    lat_raw = parts[3]
                    lat_dir = parts[4]
                    lon_raw = parts[5]
                    lon_dir = parts[6]

                    lat = convert_to_decimal(lat_raw, lat_dir)
                    lon = convert_to_decimal(lon_raw, lon_dir)

                    if lat is not None and lon is not None:
                        # Create Google Maps link
                        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                        
                        # Store valid data
                        last_valid_data = {
                            "latitude": lat,
                            "longitude": lon,
                            "google_maps_link": google_maps_link,
                            "timestamp": current_time
                        }
                        
                        print("Latitude:", lat)
                        print("Longitude:", lon)
                        print("Google Maps:", google_maps_link)
                    else:
                        print("Invalid GPS coordinates")
                        internalLED.off()  # Turn off LED if no valid data
                else:
                    print("No valid GPS fix")
                    internalLED.off()  # Turn off LED if no valid fix
            else:
                internalLED.off()  # Turn off LED for non-GPRMC sentences
        except Exception as e:
            print("Error processing GPS data:", e)
            internalLED.off()
    
    # Send data every 2 seconds if valid data exists
    if last_valid_data and current_time - last_send_time >= 2:
        if send_to_firebase(last_valid_data):
            print("Data sent to Firebase successfully!")
            last_send_time = current_time
        else:
            print("Failed to send data to Firebase after retries")
    
    time.sleep(0.1)  # Small delay to prevent CPU overload
