import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

# Tạo dữ liệu giả lập
np.random.seed(42)
num_samples = 1000
data = {
    "distance": np.random.uniform(5, 20, num_samples),  # Khoảng cách: 5-20 km
    "accident_count": np.random.randint(0, 10, num_samples),  # Số tai nạn: 0-10
    "avg_severity": np.random.uniform(1, 3, num_samples),  # 1: light, 2: medium, 3: heavy
}
# Tính safety_score (giả lập): thấp hơn là an toàn hơn
data["safety_score"] = (
    data["distance"] * 0.5 + 
    data["accident_count"] * 10 + 
    data["avg_severity"] * 15
)

df = pd.DataFrame(data)
X = df[["distance", "accident_count", "avg_severity"]]
y = df["safety_score"]

# Huấn luyện mô hình
model = RandomForestRegressor(n_estimators=50, random_state=42)
model.fit(X, y)

# Lưu mô hình
joblib.dump(model, "route_optimizer_model.pkl")
print("Mô hình đã được lưu vào route_optimizer_model.pkl")