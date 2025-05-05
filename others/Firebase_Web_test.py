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
