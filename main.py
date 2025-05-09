from machine import Pin, PWM, UART, time_pulse_us
import utime
import time
import network
import socket
import urequests

# Cấu hình chân
TRIG = Pin(20, Pin.OUT)    # GPIO20 (chân 26) cho Trigger
ECHO = Pin(28, Pin.IN)     # GPIO28 (chân 36) cho Echo
BUZZER = Pin(16, Pin.OUT)  # GPIO16 (chân 21) cho Buzzer
internalLED = Pin('LED', Pin.OUT)

# Khởi tạo các chân điều khiển động cơ
IN1 = Pin(11, Pin.OUT)
IN2 = Pin(12, Pin.OUT)
ENA = PWM(Pin(10))
ENA.freq(1000)
IN3 = Pin(14, Pin.OUT)
IN4 = Pin(15, Pin.OUT)
ENB = PWM(Pin(13))
ENB.freq(1000)

# WiFi credentials
SSID = "thantanmadai"
PASSWORD = "12345678t"

# Firebase details
FIREBASE_URL = "https://iot-database-test-default-rtdb.asia-southeast1.firebasedatabase.app/data.json"

# Initialize UART for GPS
uart = UART(0, 9600)

# Hàm đo khoảng cách từ HC-SR04
def do_measure():
    TRIG.low()
    utime.sleep_us(5)
    TRIG.high()
    utime.sleep_us(10)
    TRIG.low()
    try:
        duration = time_pulse_us(ECHO, 1, 30000)
        if duration > 0:
            distance = duration * 0.0343 / 2
            if 2 <= distance <= 500:
                return distance
    except:
        pass
    return None

# Hàm chuyển đổi tọa độ GPS
def convert_to_decimal(raw_value, direction):
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

# Hàm điều khiển động cơ
def motorA_forward(speed=50000):
    IN1.high()
    IN2.low()
    ENA.duty_u16(speed)

def motorA_backward(speed=50000):
    IN1.low()
    IN2.high()
    ENA.duty_u16(speed)

def motorA_stop():
    ENA.duty_u16(0)
    IN1.low()
    IN2.low()

def motorB_forward(speed=50000):
    IN3.high()
    IN4.low()
    ENB.duty_u16(speed)

def motorB_backward(speed=50000):
    IN3.low()
    IN4.high()
    ENB.duty_u16(speed)

def motorB_stop():
    ENB.duty_u16(0)
    IN3.low()
    IN4.low()

def car_forward():
    motorA_forward()
    motorB_forward()

def car_backward():
    motorA_backward()
    motorB_backward()

def car_left():
    motorA_backward()
    motorB_forward()

def car_right():
    motorA_forward()
    motorB_backward()

def car_stop():
    motorA_stop()
    motorB_stop()

# Kết nối WiFi
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
    for _ in range(2):
        internalLED.on()
        time.sleep(0.01)
        internalLED.off()
        time.sleep(0.01)
    print('Đã kết nối WiFi!')
    print('Thông tin mạng:', wlan.ifconfig())
    ip = wlan.ifconfig()[0]
else:
    print('Kết nối thất bại.')
    while True:
        internalLED.on()
        time.sleep(0.5)
        internalLED.off()
        time.sleep(0.5)

# Tạo socket server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((ip, 80))
server.listen(5)
print("Server đang lắng nghe tại", ip, "...")

# Hàm gửi dữ liệu lên Firebase
def send_to_firebase(data):
    max_retries = 1
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            response = urequests.request('PUT', FIREBASE_URL, json=data)
            print(f"Firebase response (attempt {attempt + 1}): {response.text}")
            response.close()
            for _ in range(2):
                internalLED.on()
                time.sleep(0.01)
                internalLED.off()
                time.sleep(0.01)
            return True
        except Exception as e:
            pass
            #print(f"Error sending to Firebase (attempt {attempt + 1}/{max_retries}): {str(e)}")
            #if attempt < max_retries - 1:
                #time.sleep(retry_delay)
    return False

# Main loop tối ưu
#last_send_time = 0
last_gps_data = None  # Lưu trữ dữ liệu GPS hợp lệ
#last_log_time = 0  # Theo dõi thời gian in log


last_firebase_time = 0
last_sensor_time = 0
last_gps_time = 0
# Đặt socket ở chế độ non-blocking
server.settimeout(0.5)  # Timeout ngắn để kiểm tra nhanh

while True:
    # Xử lý socket (điều khiển xe)
    try:
        conn, addr = server.accept()
        #print("Client connected from:", addr)
        
        request = conn.recv(1024).decode()
        #print("Request:", request)
        
        # -- Handle HTTP Requests
        if "GET /forward" in request:
            car_forward()
            #print("forward")
        elif "GET /backward" in request:
            car_backward()
            #print("backward")
        elif "GET /left" in request:
            car_left()
            #print("left")
        elif "GET /right" in request:
            car_right()
            #print("right")
        elif "GET /stop" in request:
            car_stop()
            #print("stop")
        
        # -- Send HTTP response
        response = "HTTP/1.1 200 OK\nContent-Type: text/html\n\nCommand received"
        conn.send(response)
        conn.close()
    except OSError:
        pass 

    # Xử lý các tác vụ khác (thêm vào đây)
    current_time = utime.ticks_ms()  # Lấy thời gian hiện tại (mili giây)
    
    # Đo khoảng cách từ HC-SR04 mỗi 100ms
    if utime.ticks_diff(current_time, last_sensor_time) >= 100:
        distance = do_measure()
        if distance is not None:
            print("Khoảng cách: {:.2f} cm".format(distance))
            if 5 <= distance <= 12:
                car_stop()
                BUZZER.on()
            else:
                BUZZER.off()
        last_sensor_time = current_time

    # Ví dụ: Đọc GPS mỗi 500ms (nếu có)
    if utime.ticks_diff(current_time, last_gps_time) >= 500:
        if uart.any():
            try:
                line = uart.readline()
                sentence = line.decode('utf-8').strip()
                #print("NMEA:", sentence)
                if sentence.startswith('$GPRMC'):
                    parts = sentence.split(',')
                    if len(parts) > 6 and parts[2] == 'A':
                        lat_raw = parts[3]
                        lat_dir = parts[4]
                        lon_raw = parts[5]
                        lon_dir = parts[6]
                        lat = convert_to_decimal(lat_raw, lat_dir)
                        lon = convert_to_decimal(lon_raw, lon_dir)
                        if lat is not None and lon is not None:
                            google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                            last_gps_data = {
                                "latitude": lat,
                                "longitude": lon,
                                "google_maps_link": google_maps_link,
                                "timestamp": current_time
                            }
                            print("Latitude:", lat)
                            print("Longitude:", lon)
                            #print("Google Maps:", google_maps_link)
            except Exception as e:
                print("Error processing GPS data:", str(e))
        last_gps_time = current_time

    # Ví dụ: Gửi dữ liệu Firebase mỗi 1000ms (nếu có)
    if utime.ticks_diff(current_time, last_firebase_time) >= 1000:
        if distance is not None and 5 <= distance <= 12:
            data_to_send = {
                "latitude": last_gps_data['latitude'] if last_gps_data else None,
                "longitude": last_gps_data['longitude'] if last_gps_data else None,
                "google_maps_link": last_gps_data['google_maps_link'] if last_gps_data else None,
                "distance": round(distance, 2),
                "timestamp": current_time
            }
            print("Chuẩn bị gửi dữ liệu lên Firebase:", data_to_send)
            if send_to_firebase(data_to_send):
                car_backward()
                time.sleep(2)
                car_stop()
                print("Data sent to Firebase successfully!")
            else:
                car_backward()
                time.sleep(2)
                car_stop()
                print("Failed to send data to Firebase")
        last_firebase_time = current_time

    # Ngăn CPU quá tải, sleep ngắn
    time.sleep(0.01)
