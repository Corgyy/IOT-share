import network
import time

# Thay đổi SSID và PASSWORD thành thông tin WiFi của bạn
SSID = "thantanmadai"
PASSWORD = "12345678t"

# Khởi tạo đối tượng WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Kết nối đến WiFi
wlan.connect(SSID, PASSWORD)

# Chờ kết nối
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('Đang chờ kết nối...')
    time.sleep(1)

# Kiểm tra trạng thái kết nối
if wlan.isconnected():
    print('Đã kết nối WiFi!')
    print('Thông tin mạng:', wlan.ifconfig())
else:
    print('Kết nối thất bại.')
