import network
import socket
import machine

SSID = "thantanmadai"
PASSWORD = "1234578t"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)  # Bật WiFi

if not wlan.isconnected():
    wlan.connect(SSID, PASSWORD)
    for _ in range(10):  # Chờ tối đa 10 giây
        if wlan.isconnected():
            break
        time.sleep(1)

ip = wlan.ifconfig()[0]
if wlan.isconnected():
    print("Connected! IP Address:", ip)
else:
    print("Không kết nối được WiFi!")

led = machine.Pin("LED", machine.Pin.OUT)

server = socket.socket()
server.bind((ip, 80))
server.listen(5)

while True:
    conn, addr = server.accept()
    print("Client connected from:", addr)
    
    request = conn.recv(1024).decode()
    print("Request:", request)
    
    if "GET /on" in request:
        print("Turning LED ON")
        led.value(1)
    elif "GET /off" in request:
        print("Turning LED OFF")
        led.value(0)
    
    conn.send("HTTP/1.1 200 OK\n\nLED command received")
    conn.close()
