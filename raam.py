from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes so frontend can send requests

# Load model and encoders
model = pickle.load(open("model.pkl", "rb"))
with open("encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json["features"]
        
        # We expect 18 features in exact dataset order
        # Categorical Text Indices: 1, 2, 4, 6, 8, 10, 12, 15, 16, 17
        text_cols_map = {
            1: "Origin", 2: "Destination", 4: "Delivery Window", 
            6: "Delivery Status", 8: "Route Type", 10: "Weather",
            12: "Vehicle Type", 15: "Region", 16: "Delivery Time of Day", 
            17: "Day of Week"
        }
        
        processed_data = []
        for i, val in enumerate(data):
            if i in text_cols_map:
                col_name = text_cols_map[i]
                # Transform text based fields using the loaded LabelEncoder
                encoded_val = encoders[col_name].transform([str(val)])[0]
                processed_data.append(encoded_val)
            else:
                processed_data.append(float(val))
        
        # Create a 2D features array for prediction
        features = np.array([processed_data])
        prediction = model.predict(features)
        
        return jsonify({
            "predicted_delivery_time": round(float(prediction[0]), 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
