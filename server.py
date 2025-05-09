from flask import Flask, jsonify, request
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Thêm CORS để tránh lỗi khi gọi API từ web

# Firebase Realtime Database URL
FIREBASE_URL = "https://iot-database-test-default-rtdb.asia-southeast1.firebasedatabase.app/data.json"

# URL OSRM để tính đường đi
OSRM_URL = "http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"

# Route mặc định để kiểm tra server
@app.route('/')
def home():
    return jsonify({'message': 'Server is running. Use /analyze to get accident data.'})

# Lấy dữ liệu từ Firebase qua REST API
def get_firebase_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Firebase response status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu từ Firebase: {e}")
        return None

# Phát hiện tai nạn
def detect_accident(data):
    if data and 'distance' in data and data['distance'] < 8:
        return {
            'accident_detected': True,
            'latitude': data['latitude'],
            'longitude': data['longitude']
        }
    return {'accident_detected': False}

# Tính đường đi ngắn nhất
def get_route(start, end):
    url = OSRM_URL.format(
        start_lng=start['lng'], start_lat=start['lat'],
        end_lng=end['lng'], end_lat=end['lat']
    )
    try:
        response = requests.get(url)
        if response.status_code == 200:
            route_data = response.json()
            if route_data['routes'] and len(route_data['routes']) > 0:
                return {
                    'coordinates': route_data['routes'][0]['geometry']['coordinates'],
                    'distance': route_data['routes'][0]['distance'] / 1000  # km
                }
        return None
    except Exception as e:
        print(f"Lỗi khi gọi OSRM API: {e}")
        return None

# API để lấy trạng thái tai nạn và đường đi
@app.route('/analyze', methods=['GET'])
def analyze():
    try:
        # Lấy tọa độ bắt đầu từ query parameters
        start_lat = request.args.get('start_lat', default=10.8506, type=float)
        start_lng = request.args.get('start_lng', default=106.7693, type=float)

        # Kiểm tra tọa độ hợp lệ
        if not (-90 <= start_lat <= 90) or not (-180 <= start_lng <= 180):
            return jsonify({'error': 'Tọa độ bắt đầu không hợp lệ'}), 400

        # Lấy dữ liệu từ Firebase
        data = get_firebase_data()
        if not data:
            return jsonify({'error': 'Không có dữ liệu từ Firebase'}), 500

        # Phát hiện tai nạn
        accident_info = detect_accident(data)
        
        # Nếu phát hiện tai nạn, tính đường đi
        if accident_info['accident_detected']:
            start = {'lat': start_lat, 'lng': start_lng}
            end = {'lat': accident_info['latitude'], 'lng': accident_info['longitude']}
            route = get_route(start, end)
            if route:
                accident_info['route'] = route['coordinates']
                accident_info['distance'] = route['distance']
            else:
                accident_info['route'] = None
                accident_info['distance'] = None
                accident_info['error'] = 'Không thể tính đường đi'

        return jsonify(accident_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)