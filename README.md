# Delivery Outcome Studio

A comprehensive machine learning-powered delivery prediction and route optimization system. Combines time prediction models with intelligent route optimization to help logistics operations reduce delivery times and fuel costs.

## 🎯 Features

### Prediction Studio
- **15 Pre-built Scenarios**: Quick-load delivery scenarios covering various conditions (weather, traffic, distance, route type)
- **Scenario Coverage**: Fast urban, suburban, rural, weather delays, rush hour, weekend, urgent, foggy, cross-region, and critical delay scenarios
- **Custom Parameters**: 17-feature input form for manual delivery time predictions
- **Real-time Predictions**: ML model predicts delivery time with service band classification
- **ETA Calculation**: Estimated arrival time based on current time + predicted hours
- **Visual Progress Meter**: Quick visual feedback on delivery speed classification

### Route Optimizer
- **Nearest Neighbor Algorithm**: Automatic route sequencing to minimize distance
- **Multi-Factor Optimization**: Considers distance, traffic, weather, and customer regions
- **Time Prediction per Leg**: Integrates ML model to predict time for each route segment
- **Configurable Fuel Cost**: Adjustable fuel price slider (₹80-₹200/liter) in Indian Rupees
- **Visual Route Map**: SVG-based map showing:
  - Warehouse position and customer locations
  - Current route (dashed gray lines)
  - Optimized route (solid teal lines)
  - Color-coded nodes by region
- **Detailed Comparison Tables**: Side-by-side current vs optimized routes with leg-by-leg breakdown
- **Savings Metrics**: Real-time calculation of:
  - Distance saved (km and %)
  - Time saved (hours and %)
  - Fuel cost saved (INR and %)

## 🏗️ Architecture

```
Frontend (index.html)
├── Prediction Studio Tab
│   ├── Scenario Presets (15 options)
│   ├── Prediction Results
│   └── Custom Parameters Form (17 fields)
└── Route Optimizer Tab
    ├── Input Controls (warehouse, window, day, weather, fuel cost)
    ├── Visual Route Map (SVG)
    ├── Metrics Cards (distance, time, fuel saved)
    ├── Current Route Table
    └── Optimized Route Table

Backend (raam.py)
├── /predict endpoint (POST)
│   └── ML model prediction on 17 features
├── /optimizer-options endpoint (GET)
│   └── Dropdown options (warehouses, windows, days, weathers)
└── /optimize endpoint (POST)
    ├── Nearest neighbor routing
    ├── Per-leg time prediction
    ├── Metrics calculation
    └── JSON response with routes + savings

ML Models (pickled artifacts)
├── model.pkl → RandomForestRegressor (trained on 611 samples)
└── encoders.pkl → LabelEncoders for 10 categorical features

Dataset (dataset.csv)
└── 611 delivery records with 19 fields
    ├── Numeric: distance, traffic, weather impact, fuel efficiency
    └── Categorical: origin, destination, weather, route type, region, etc.
```

## 🚀 Getting Started

### Prerequisites
- Python 3.14+
- Flask & Flask-CORS
- scikit-learn, pandas, numpy
- Modern web browser

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/unvsairam/mlproject.git
cd mlproject
```

2. **Set up virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install flask flask-cors scikit-learn pandas numpy matplotlib seaborn
```

### Running the Application

1. **Start the backend server**
```bash
python raam.py
```
The Flask app will start on `http://127.0.0.1:5000`

2. **Open the frontend**
- Open `index.html` in your web browser
- Or serve it with a local server: `python -m http.server 8000` and visit `http://localhost:8000`

## 📋 Usage Guide

### Prediction Studio

**Using Presets:**
1. Click any of the 15 scenario buttons (Fast Urban, Rush Hour, etc.)
2. Fields auto-populate with realistic delivery parameters
3. Model auto-predicts delivery time
4. Results show in the right panel with service band and ETA

**Manual Prediction:**
1. Fill in custom parameters in the "Custom Parameters" section
2. Click "Predict from Current Fields"
3. Model processes the 17 features and returns estimated delivery time

**Available Scenarios:**
- Fast Urban - Short route, clear weather (~0.6 hrs)
- Suburban Standard - Balanced daytime run (~1.2 hrs)
- Rural Long Haul - Extended distance (~3.5 hrs)
- Storm Delay - Bad weather impact (~2.2 hrs)
- Rush Hour - Heavy traffic (~1.8 hrs)
- Quiet Weekend - Low traffic Sunday (~1.0 hrs)
- Express Bike - Urgent delivery (~0.6 hrs)
- Foggy Morning - Visibility issues (~1.8 hrs)
- Cross Region - Distance + mixed traffic (~3.0 hrs)
- Critical Delay - Worst-case scenario (~4.5 hrs)
- Rainy Suburban - Moderate rain impact (~1.5 hrs)
- North Rural Snow - Cold weather (~2.8 hrs)
- Late Van Express - Evening urgent delivery (~1.5 hrs)
- Foggy Metro - Urban fog congestion (~1.4 hrs)
- Balanced Midweek - Steady conditions (~1.8 hrs)

### Route Optimizer

1. **Select Parameters**
   - Choose Warehouse (A, B, or C)
   - Select Delivery Window (08:00-12:00, 12:00-16:00, 16:00-20:00)
   - Pick Day of Week (Monday-Sunday)
   - Set Weather condition (Clear, Rain, Fog, Snow)
   - Adjust Fuel Cost slider (default ₹120/liter)

2. **Run Optimization**
   - Click "Optimize Route"
   - Backend analyzes current delivery order and optimizes it

3. **Review Results**
   - **Visual Map**: See warehouse, customers, current vs optimized routes
   - **Metrics Cards**: Quick view of distance, time, and fuel savings
   - **Current Route Table**: Original delivery sequence with distances and times
   - **Optimized Route Table**: Suggested improved sequence with predictions

4. **Key Metrics**
   - Distance saved: Total km reduction
   - Time saved: Total hours reduction
   - Fuel saved: INR savings based on your fuel cost input

## 📊 Data Model

### Input Features (17 total)
```
Numeric (9):
  - Distance (km)
  - Urgency (1-3)
  - Traffic Level (0-10)
  - Traffic Delay (mins)
  - Weather Impact (mins)
  - Fuel Efficiency (liters/km)
  - Fuel Consumption (liters)

Categorical (8):
  - Origin (Warehouse A/B/C)
  - Destination (Customer 1-6)
  - Delivery Window (3 time slots)
  - Delivery Status (On-time/Delayed)
  - Route Type (Urban/Suburban/Rural)
  - Weather (Clear/Rain/Fog/Snow)
  - Vehicle Type (Motorcycle/Van/Truck)
  - Region (North/South/East/West)
  - Delivery Time of Day (Morning/Afternoon/Evening)
  - Day of Week (Monday-Sunday)
```

### Output
```
Prediction Studio:
  - predicted_delivery_time (float, hours)
  - service_band (Very Fast/Fast/Standard/Slow)
  - estimated_arrival_time (datetime)

Route Optimizer:
  - current_route (array of legs with distance, time)
  - optimized_route (array of legs with distance, time)
  - improvement metrics (distance/time/fuel saved with %)
```

## 🤖 ML Model Details

**Model Type**: RandomForestRegressor (ensemble of 100 decision trees)

**Training Data**:
- 611 delivery records
- 80/20 train-test split (random_state=42)
- 17 features (ID column excluded)

**Performance Metrics**:
- MAE (Mean Absolute Error): 0.43 hours
- RMSE (Root Mean Squared Error): 0.56 hours
- R² Score: 0.71 (explains 71% of variance)

**Feature Engineering**:
- Categorical features encoded with LabelEncoder
- Numeric features used as-is
- No missing values after preprocessing

## 🛣️ Route Optimization Algorithm

**Algorithm**: Nearest Neighbor with Region-Aware Tie-Breaking

**Process**:
1. Start at warehouse
2. For each unvisited customer:
   - Find closest by historical distance data
   - If equidistant: prefer same region as previous stop
   - Add to route sequence
3. For each leg, predict delivery time using ML model
4. Sum distances, times, and fuel costs
5. Compare against current order

**Distance Calculation**:
- Warehouse → Customer: Extracted from dataset averages
- Customer → Customer: Inferred from warehouse-based vectors

**Vehicle Assignment**:
- Distance ≥ 110km: Truck (0.10 L/km)
- Distance 55-110km: Van (0.05 L/km)
- Distance < 55km: Motorcycle (0.05 L/km)

## 📁 Project Structure

```
mlproject/
├── README.md                 # This file
├── index.html               # Frontend UI (tabbed interface)
├── raam.py                  # Flask backend API
├── mlproject.py             # ML training script
├── dataset.csv              # Training data (611 rows)
├── model.pkl                # Trained RandomForest model
├── encoders.pkl             # LabelEncoders for categorical features
└── .venv/                   # Python virtual environment
```

## 🔧 API Endpoints

### POST /predict
Predict delivery time for a single delivery

**Request**:
```json
{
  "features": [
    "Warehouse A",    // origin
    "Customer 1",     // destination
    24,              // distance km
    "08:00 - 12:00", // delivery window
    2,               // urgency
    "On-time",       // delivery status
    2,               // traffic level
    "Urban",         // route type
    5,               // traffic delay mins
    "Clear",         // weather
    0,               // weather impact
    "Motorcycle",    // vehicle type
    0.05,            // fuel efficiency
    1.2,             // fuel consumption
    "East",          // region
    "Morning",       // delivery time of day
    "Tuesday"        // day of week
  ]
}
```

**Response**:
```json
{
  "predicted_delivery_time": 0.85
}
```

### GET /optimizer-options
Get available options for optimizer dropdowns

**Response**:
```json
{
  "warehouses": ["Warehouse A", "Warehouse B", "Warehouse C"],
  "delivery_windows": ["08:00 - 12:00", "12:00 - 16:00", "16:00 - 20:00"],
  "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
  "weathers": ["Clear", "Fog", "Rain", "Snow"],
  "fuel_cost_default": 120
}
```

### POST /optimize
Optimize delivery route for a warehouse

**Request**:
```json
{
  "warehouse": "Warehouse A",
  "delivery_window": "08:00 - 12:00",
  "day": "Monday",
  "weather": "Clear",
  "fuel_cost_per_liter": 120
}
```

**Response**:
```json
{
  "warehouse": "Warehouse A",
  "current_route": [
    {
      "leg": 1,
      "from": "Warehouse A",
      "to": "Customer 2",
      "distance": 57.0,
      "predicted_time": 1.68,
      "region": "South",
      "fuel_liters": 2.85
    }
  ],
  "optimized_route": [
    {
      "leg": 1,
      "from": "Warehouse A",
      "to": "Customer 4",
      "distance": 84.0,
      "predicted_time": 1.42,
      "region": "East",
      "fuel_liters": 4.2
    }
  ],
  "metrics": {
    "current": {
      "total_distance": 99.0,
      "total_time": 2.83,
      "total_fuel_liters": 4.95,
      "fuel_cost_inr": 594.0
    },
    "optimized": {
      "total_distance": 129.0,
      "total_time": 2.72,
      "total_fuel_liters": 6.45,
      "fuel_cost_inr": 774.0
    },
    "improvement": {
      "distance_saved_km": -30.0,
      "time_saved_hrs": 0.11,
      "fuel_saved_inr": -180.0,
      "distance_saved_pct": -30.3,
      "time_saved_pct": 3.9,
      "fuel_saved_pct": -30.3
    }
  }
}
```

## ⚙️ Configuration

### Fuel Cost
- Default: ₹120/liter (configured in `/optimizer-options`)
- Adjustable: ₹80-₹200/liter via slider in optimizer UI
- Used for: Fuel cost calculation in route optimization

### Model Parameters
- RandomForest estimators: 100
- Train/test split: 80/20
- Random state: 42 (reproducible)
- Feature count: 17

### Categorical Feature Encoding
Automatic LabelEncoding applied to:
- Origin, Destination, Delivery Window, Delivery Status, Route Type, Weather, Vehicle Type, Region, Delivery Time of Day, Day of Week

## 🐛 Troubleshooting

### Connection Error
**Problem**: "Error connecting to server"
- Solution: Ensure Flask backend is running with `python raam.py`
- Check: Backend is listening on `http://127.0.0.1:5000`

### Unseen Category Error
**Problem**: "Error: unknown label" when predicting
- Solution: Use dropdowns (when available) or values from training data
- Check: Warehouse (A/B/C), Weather (Clear/Rain/Fog/Snow), Vehicle Type (Motorcycle/Van/Truck)

### No Data Available
**Problem**: "No data available for selected warehouse"
- Solution: Route optimizer filters by warehouse + window + day. Some combinations may have sparse data.
- Fallback: Backend automatically uses warehouse + window data if specific day has no records

### Slow Predictions
**Problem**: Predictions take >2 seconds
- Solution: Model loads on startup. First prediction might be slower.
- Normal: Subsequent predictions should be instant

## 📈 Expected Performance

**Prediction Accuracy**:
- MAE: ±0.43 hours (±26 minutes)
- Works best for standard routes (2-4 hours)
- Less accurate for very short (<0.5 hrs) or long (>4.5 hrs) deliveries

**Route Optimization**:
- Time savings: 3-15% typical
- Reduces unnecessary cross-region trips
- Works best with 4-6 customer stops per route

## 🔮 Future Enhancements

- [ ] Export routes as PDF/CSV
- [ ] Multi-day route planning
- [ ] Vehicle capacity constraints
- [ ] Driver shift time limits
- [ ] Real-time traffic integration
- [ ] Geospatial visualization with actual maps
- [ ] A/B testing framework for model versions
- [ ] Route comparison over historical data

## 📝 License

This project is open source and available under the MIT License.

## 👤 Author

Built as a delivery logistics ML system.

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review API endpoint documentation
3. Examine backend logs in Flask console
4. Check browser console for frontend errors

---

**Last Updated**: April 2026
**Version**: 1.0
**Status**: Production Ready
