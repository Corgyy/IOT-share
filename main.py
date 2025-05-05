#main.py = wifi + car_control

from machine import Pin, PWM
import network
import socket
import time

# Khởi tạo LED nội bộ
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

# Hàm điều khiển động cơ A
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

# Hàm điều khiển động cơ B
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

# Hàm điều khiển xe - đồng bộ tín hiệu
def car_forward(speed=50000):
    IN1.high()
    IN2.low()
    IN3.high()
    IN4.low()
    ENA.duty_u16(speed)
    ENB.duty_u16(speed)

def car_backward(speed=50000):
    IN1.low()
    IN2.high()
    IN3.low()
    IN4.high()
    ENA.duty_u16(speed)
    ENB.duty_u16(speed)

def car_left(speed=50000):
    IN1.low()
    IN2.high()
    IN3.high()
    IN4.low()
    ENA.duty_u16(speed)
    ENB.duty_u16(speed)

def car_right(speed=50000):
    IN1.high()
    IN2.low()
    IN3.low()
    IN4.high()
    ENA.duty_u16(speed)
    ENB.duty_u16(speed)

def car_stop():
    IN1.low()
    IN2.low()
    IN3.low()
    IN4.low()
    ENA.duty_u16(0)
    ENB.duty_u16(0)

# Kết nối Wi-Fi
SSID = "thantanmadai"
PASSWORD = "12345678t"
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
    ip = wlan.ifconfig()[0]
else:
    print('Kết nối thất bại.')
    while True:
        pass

# Tạo socket server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Tái sử dụng địa chỉ
server.bind((ip, 80))
server.listen(5)
print("Server đang lắng nghe tại", ip, "...")

# Main loop
while True:
    internalLED.value(1)
    try:
        conn, addr = server.accept()
        print("Client kết nối từ:", addr)
        
        # Nhận và xử lý yêu cầu
        request = conn.recv(1024).decode()
        print("Request:", request)
        
        # Xử lý các lệnh HTTP
        if "GET /forward" in request:
            car_forward()
            print("Tiến")
        elif "GET /backward" in request:
            car_backward()
            print("Lùi")
        elif "GET /left" in request:
            car_left()
            print("Trái")
        elif "GET /right" in request:
            car_right()
            print("Phải")
        elif "GET /stop" in request:
            car_stop()
            print("Dừng")
        
        # Gửi phản hồi HTTP
        response = "HTTP/1.1 200 OK\nContent-Type: text/html\n\nCommand received"
        conn.send(response)
        conn.close()
        
    except Exception as e:
        print("Lỗi:", e)
        conn.close()
    finally:
        internalLED.value(0)  # Tắt LED sau khi xử lý


#neo-6m
"""
from machine import UART, Pin
import time

uart = UART(0, 9600)
internalLED = Pin('LED', Pin.OUT)

while True:
    if uart.any():
        internalLED.value(1)
        data = uart.read()
        if data:
            try:
                gps_reading = data.decode('utf-8')
                print(gps_reading)
            except UnicodeError:
                # Nếu không giải mã được, bỏ qua dòng lỗi
                pass
        time.sleep(0.1)
        internalLED.value(0)

"""




#firebase
"""
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
"""




#HC-SR04
"""
from machine import Pin, time_pulse_us
import utime

TRIG = Pin(3, Pin.OUT)
ECHO = Pin(2, Pin.IN)

def do_measure():
    TRIG.low()
    utime.sleep_us(2)
    TRIG.high()
    utime.sleep_us(10)
    TRIG.low()

    duration = time_pulse_us(ECHO, 1, 30000)  # Timeout 30ms
    distance = duration * 0.0343 / 2  # Tốc độ âm thanh ~343m/s

    return distance

while True:
    d = do_measure()
    print("Khoảng cách: {:.2f} cm".format(d))
    utime.sleep(1)

"""

#Web

"""
import network
import urequests
import utime
from machine import Pin

SSID = "thantanmadai"
PASSWORD = "12345678t"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    print("Đang kết nối WiFi...")
    utime.sleep(1)

print("WiFi đã kết nối:", wlan.ifconfig())




# Cấu hình Firebase
FIREBASE_URL = "https://iot-database-test-default-rtdb.asia-southeast1.firebasedatabase.app/led_status.json"

# Cấu hình LED tích hợp trên Pico W
led = Pin("LED", Pin.OUT)

# Hàm lấy trạng thái LED từ Firebase
def get_led_status():
    try:
        response = urequests.get(FIREBASE_URL)
        status = response.text.replace('"', '')  # Loại bỏ dấu ngoặc kép
        response.close()
        return status
    except Exception as e:
        print("Lỗi đọc Firebase:", e)
        return None

# Vòng lặp kiểm tra trạng thái LED
while True:
    led_status = get_led_status()
    print("Trạng thái từ Firebase:", led_status)  # Debug thông tin nhận được

    if led_status == "ON":
        led.value(1)  # Bật LED
    elif led_status == "OFF":
        led.value(0)  # Tắt LED
    
    utime.sleep(2)  # Kiểm tra trạng thái mỗi 2 giây

"""