from flask import Flask, jsonify, request
import requests
from flask_cors import CORS
import time
import random
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app)

# Tải mô hình AI
model = joblib.load("route_optimizer_model.pkl")

# Firebase Realtime Database URL
FIREBASE_URL = "https://iot-database-test-default-rtdb.asia-southeast1.firebasedatabase.app/data.json"
ACCIDENT_DB_URL = "https://iot-database-test-default-rtdb.asia-southeast1.firebasedatabase.app/accidents.json"
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
    ) + "&alternatives=true"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            route_data = response.json()
            routes = []
            for route in route_data['routes']:
                accident_count, avg_severity = get_accident_stats(route['geometry']['coordinates'])
                distance = route['distance'] / 1000
                input_data = pd.DataFrame({
                    'distance': [distance],
                    'accident_count': [accident_count],
                    'avg_severity': [avg_severity]
                })
                # Dự đoán safety_score
                safety_score = model.predict(input_data)[0]
                routes.append({
                    'coordinates': route['geometry']['coordinates'],
                    'distance': distance,
                    'accident_count': accident_count,
                    'avg_severity': avg_severity,
                    'safety_score': safety_score,
                    'reason': f"Tuyến đường có {accident_count} tai nạn, mức nghiêm trọng trung bình {avg_severity:.2f}"
                })
            
            # Chọn tuyến có safety_score thấp nhất
            best_route = min(routes, key=lambda x: x['safety_score'])
            return {
                'coordinates': best_route['coordinates'],
                'distance': best_route['distance'],
                'accident_count': best_route['accident_count'],
                'avg_severity': best_route['avg_severity'],
                'safety_score': best_route['safety_score'],
                'reason': best_route['reason']
            }
        return None
    except Exception as e:
        print(f"Lỗi khi gọi OSRM API: {e}")
        return None

def save_accident_data(data):
    try:
        response = requests.post(ACCIDENT_DB_URL, json={
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'timestamp': int(time.time()),
            'severity': random.choice(["light", "medium", "heavy"])
        })
        if response.status_code == 200:
            print("Lưu dữ liệu tai nạn thành công")
        else:
            print(f"Lỗi khi lưu dữ liệu tai nạn: {response.status_code}")
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu tai nạn: {e}")
        
def get_accident_stats(route_coords):
    try:
        response = requests.get(ACCIDENT_DB_URL)
        if response.status_code == 200:
            accidents = response.json()
            if not accidents:
                return 0, 1.0  # Không có tai nạn, severity mặc định là light
            count = 0
            severity_scores = []
            severity_map = {"light": 1, "medium": 2, "heavy": 3}
            for acc in accidents.values():
                if acc and 'latitude' in acc and 'longitude' in acc:
                    for coord in route_coords:
                        if (abs(acc['latitude'] - coord[1]) < 0.01 and 
                            abs(acc['longitude'] - coord[0]) < 0.01):
                            count += 1
                            if acc.get('severity'):
                                severity_scores.append(severity_map[acc['severity']])
                            break
            avg_severity = np.mean(severity_scores) if severity_scores else 1.0
            return count, avg_severity
        return 0, 1.0
    except Exception as e:
        print(f"Lỗi khi đếm tai nạn: {e}")
        return 0, 1.0

# API để lấy trạng thái tai nạn và đường đi
@app.route('/analyze', methods=['GET'])
def analyze():
    try:
        start_lat = request.args.get('start_lat', default=10.8506, type=float)
        start_lng = request.args.get('start_lng', default=106.7693, type=float)

        if not (-90 <= start_lat <= 90) or not (-180 <= start_lng <= 180):
            return jsonify({'error': 'Tọa độ bắt đầu không hợp lệ'}), 400

        data = get_firebase_data()
        if not data:
            return jsonify({'error': 'Không có dữ liệu từ Firebase'}), 500

        accident_info = detect_accident(data)
        
        if accident_info['accident_detected']:
            save_accident_data(accident_info)
            start = {'lat': start_lat, 'lng': start_lng}
            end = {'lat': accident_info['latitude'], 'lng': accident_info['longitude']}
            route = get_route(start, end)
            if route:
                accident_info['route'] = route['coordinates']
                accident_info['distance'] = route['distance']
                accident_info['accident_count'] = route['accident_count']
                accident_info['avg_severity'] = route['avg_severity']
                accident_info['safety_score'] = route['safety_score']
                accident_info['reason'] = route['reason']
            else:
                accident_info['route'] = None
                accident_info['distance'] = None
                accident_info['accident_count'] = 0
                accident_info['avg_severity'] = 1.0
                accident_info['safety_score'] = None
                accident_info['error'] = 'Không thể tính đường đi'

        return jsonify(accident_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)