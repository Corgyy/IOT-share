# Imports
from machine import Pin, UART
import time

# Pin and Peripheral Setup
internalLED = Pin('LED', Pin.OUT)

# NEO-6M GPS Module
uart = UART(0, 9600)

# GPS Data Processing
def parse_gps_data(gps_reading):
    """Parse $GPGGA NMEA sentence to extract latitude and longitude."""
    try:
        lines = gps_reading.split('\n')
        for line in lines:
            if line.startswith('$GPGGA'):
                parts = line.split(',')
                if len(parts) >= 10 and parts[2] and parts[4]:  # Check for valid lat/lon
                    # Latitude: DDMM.MMMM, N/S
                    lat = float(parts[2]) / 100  # Convert to decimal degrees
                    lat_dir = parts[3]
                    if lat_dir == 'S':
                        lat = -lat
                    # Longitude: DDDMM.MMMM, E/W
                    lon = float(parts[4]) / 100
                    lon_dir = parts[5]
                    if lon_dir == 'W':
                        lon = -lon
                    return {'latitude': lat, 'longitude': lon}
        return None
    except Exception as e:
        print("GPS parse error:", e)
        return None

# Main Loop
gps_buffer = ""
while True:
    internalLED.value(1)
    try:
        # Read GPS data from UART
        if uart.any():
            try:
                data = uart.read().decode('utf-8')
                gps_buffer += data
                if '\n' in gps_buffer:
                    gps_data = parse_gps_data(gps_buffer)
                    gps_buffer = ""  # Clear buffer
                    if gps_data:
                        print("GPS data:", gps_data)
                    else:
                        print("No valid GPS data")
            except UnicodeError:
                gps_buffer = ""  # Clear on invalid data
                print("Invalid GPS data")
    except Exception as e:
        print("Lỗi:", e)
    finally:
        internalLED.value(0)
        time.sleep(0.1)  # Prevent tight looping