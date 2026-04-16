from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import pickle
from collections import defaultdict, Counter

import numpy as np

app = Flask(__name__)
CORS(app)

# Load model and encoders
model = pickle.load(open("model.pkl", "rb"))
with open("encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

TEXT_COLS_MAP = {
    0: "Origin",
    1: "Destination",
    3: "Delivery Window",
    5: "Delivery Status",
    7: "Route Type",
    9: "Weather",
    11: "Vehicle Type",
    14: "Region",
    15: "Delivery Time of Day",
    16: "Day of Week",
}


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_dataset(path="dataset.csv"):
    records = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


DATASET = _load_dataset()

WAREHOUSES = sorted({row["Origin"] for row in DATASET})
CUSTOMERS = sorted({row["Destination"] for row in DATASET})
WINDOWS = sorted({row["Delivery Window"] for row in DATASET})
DAYS = sorted({row["Day of Week"] for row in DATASET})
WEATHERS = sorted({row["Weather"] for row in DATASET})


def _build_pair_stats(records):
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["Origin"], row["Destination"])].append(row)

    pair_stats = {}
    for key, rows in grouped.items():
        route_type = Counter(row["Route Type"] for row in rows).most_common(1)[0][0]
        region = Counter(row["Region"] for row in rows).most_common(1)[0][0]
        pair_stats[key] = {
            "distance": np.mean([_to_float(r["Distance (km)"]) for r in rows]),
            "traffic_level": np.mean(
                [_to_float(r["Traffic Level (0-10)"]) for r in rows]
            ),
            "traffic_delay": np.mean(
                [_to_float(r["Traffic Delay (mins)"]) for r in rows]
            ),
            "weather_impact": np.mean(
                [_to_float(r["Weather Impact (mins)"]) for r in rows]
            ),
            "route_type": route_type,
            "region": region,
            "count": len(rows),
        }
    return pair_stats


PAIR_STATS = _build_pair_stats(DATASET)

GLOBAL_DEFAULTS = {
    "distance": np.mean([_to_float(r["Distance (km)"]) for r in DATASET]),
    "traffic_level": np.mean([_to_float(r["Traffic Level (0-10)"]) for r in DATASET]),
    "traffic_delay": np.mean([_to_float(r["Traffic Delay (mins)"]) for r in DATASET]),
    "weather_impact": np.mean([_to_float(r["Weather Impact (mins)"]) for r in DATASET]),
}


def _mode_for_customer(customer, key, fallback):
    vals = [
        row[key] for row in DATASET if row["Destination"] == customer and row.get(key)
    ]
    if not vals:
        return fallback
    return Counter(vals).most_common(1)[0][0]


CUSTOMER_REGION = {c: _mode_for_customer(c, "Region", "East") for c in CUSTOMERS}


def _warehouse_customer_distance(warehouse, customer):
    pair = PAIR_STATS.get((warehouse, customer))
    if pair:
        return pair["distance"]
    return GLOBAL_DEFAULTS["distance"]


def _customer_vector(customer):
    return [_warehouse_customer_distance(wh, customer) for wh in WAREHOUSES]


def _customer_to_customer_distance(c1, c2):
    v1 = _customer_vector(c1)
    v2 = _customer_vector(c2)
    base = float(np.mean(np.abs(np.array(v1) - np.array(v2))))
    return max(8.0, base + 12.0)


def _encode_features(data):
    if len(data) != 17:
        raise ValueError("Expected 17 features")

    processed_data = []
    for i, val in enumerate(data):
        if i in TEXT_COLS_MAP:
            col_name = TEXT_COLS_MAP[i]
            encoder = encoders[col_name]
            val_str = str(val)
            if val_str not in encoder.classes_:
                val_str = encoder.classes_[0]
            encoded_val = encoder.transform([val_str])[0]
            processed_data.append(encoded_val)
        else:
            processed_data.append(float(val))
    return np.array([processed_data])


def _predict_delivery_time(data):
    features = _encode_features(data)
    prediction = model.predict(features)
    return round(float(prediction[0]), 2)


def _window_to_time_of_day(window):
    if window.startswith("08:00"):
        return "Morning"
    if window.startswith("12:00"):
        return "Afternoon"
    return "Evening"


def _vehicle_for_distance(distance):
    if distance >= 110:
        return "Truck", 0.10
    if distance >= 55:
        return "Van", 0.05
    return "Motorcycle", 0.05


def _leg_distance(prev_node, next_customer, warehouse):
    if prev_node == warehouse:
        return _warehouse_customer_distance(warehouse, next_customer)
    return _customer_to_customer_distance(prev_node, next_customer)


def _build_leg_prediction_features(
    warehouse,
    destination,
    leg_distance,
    delivery_window,
    day,
    weather,
    leg_index,
):
    pair = PAIR_STATS.get((warehouse, destination), {})
    route_type = pair.get("route_type", "Suburban")
    region = pair.get("region", CUSTOMER_REGION.get(destination, "East"))

    traffic_level = pair.get("traffic_level", GLOBAL_DEFAULTS["traffic_level"])
    traffic_delay = pair.get("traffic_delay", GLOBAL_DEFAULTS["traffic_delay"])
    weather_impact = pair.get("weather_impact", GLOBAL_DEFAULTS["weather_impact"])

    if weather == "Clear":
        weather_impact = 0.0
    elif weather == "Rain":
        weather_impact = max(weather_impact, 14.0)
    elif weather == "Fog":
        weather_impact = max(weather_impact, 18.0)
    elif weather == "Snow":
        weather_impact = max(weather_impact, 24.0)

    traffic_delay = traffic_delay + leg_index * 1.5
    vehicle_type, fuel_eff = _vehicle_for_distance(leg_distance)
    fuel_consumption = leg_distance * fuel_eff

    return [
        warehouse,
        destination,
        round(float(leg_distance), 2),
        delivery_window,
        1,
        "On-time",
        round(float(traffic_level), 2),
        route_type,
        round(float(traffic_delay), 2),
        weather,
        round(float(weather_impact), 2),
        vehicle_type,
        round(float(fuel_eff), 3),
        round(float(fuel_consumption), 2),
        region,
        _window_to_time_of_day(delivery_window),
        day,
    ]


def _nearest_neighbor_route(warehouse, customers):
    if not customers:
        return []

    unvisited = set(customers)
    route = []
    current = warehouse
    current_region = None

    while unvisited:
        ranked = sorted(
            unvisited,
            key=lambda c: (
                _leg_distance(current, c, warehouse),
                0 if current_region and CUSTOMER_REGION.get(c) == current_region else 1,
                c,
            ),
        )
        chosen = ranked[0]
        route.append(chosen)
        unvisited.remove(chosen)
        current = chosen
        current_region = CUSTOMER_REGION.get(chosen)

    return route


def _current_route_order(filtered_rows):
    ordered = []
    seen = set()
    for row in filtered_rows:
        customer = row["Destination"]
        if customer not in seen:
            ordered.append(customer)
            seen.add(customer)
    return ordered


def _build_route_legs(warehouse, customer_sequence, delivery_window, day, weather):
    legs = []
    prev = warehouse
    total_distance = 0.0
    total_time = 0.0
    total_fuel = 0.0

    for idx, customer in enumerate(customer_sequence):
        distance = _leg_distance(prev, customer, warehouse)
        features = _build_leg_prediction_features(
            warehouse=warehouse,
            destination=customer,
            leg_distance=distance,
            delivery_window=delivery_window,
            day=day,
            weather=weather,
            leg_index=idx,
        )
        predicted_time = _predict_delivery_time(features)
        _, fuel_eff = _vehicle_for_distance(distance)
        fuel_used = distance * fuel_eff

        legs.append(
            {
                "leg": idx + 1,
                "from": prev,
                "to": customer,
                "distance": round(float(distance), 2),
                "predicted_time": round(float(predicted_time), 2),
                "region": CUSTOMER_REGION.get(customer, "East"),
                "fuel_liters": round(float(fuel_used), 2),
            }
        )
        prev = customer
        total_distance += distance
        total_time += predicted_time
        total_fuel += fuel_used

    return {
        "legs": legs,
        "total_distance": round(float(total_distance), 2),
        "total_time": round(float(total_time), 2),
        "total_fuel_liters": round(float(total_fuel), 2),
    }


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json["features"]
        predicted_delivery_time = _predict_delivery_time(data)
        return jsonify({"predicted_delivery_time": predicted_delivery_time})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/optimizer-options", methods=["GET"])
def optimizer_options():
    return jsonify(
        {
            "warehouses": WAREHOUSES,
            "delivery_windows": WINDOWS,
            "days": DAYS,
            "weathers": WEATHERS,
            "fuel_cost_default": 120,
        }
    )


@app.route("/optimize", methods=["POST"])
def optimize():
    try:
        payload = request.json or {}
        warehouse = payload.get("warehouse", "Warehouse A")
        delivery_window = payload.get("delivery_window", "08:00 - 12:00")
        day = payload.get("day", "Monday")
        weather = payload.get("weather", "Clear")
        fuel_cost_per_liter = _to_float(payload.get("fuel_cost_per_liter", 120), 120)

        filtered = [
            row
            for row in DATASET
            if row["Origin"] == warehouse
            and row["Delivery Window"] == delivery_window
            and row["Day of Week"] == day
        ]
        if not filtered:
            filtered = [
                row
                for row in DATASET
                if row["Origin"] == warehouse
                and row["Delivery Window"] == delivery_window
            ]
        if not filtered:
            filtered = [row for row in DATASET if row["Origin"] == warehouse]
        if not filtered:
            return jsonify({"error": "No data available for selected warehouse"}), 400

        customers = sorted({row["Destination"] for row in filtered})
        if not customers:
            return jsonify({"error": "No destinations found for selected filters"}), 400

        current_order = _current_route_order(filtered)
        optimized_order = _nearest_neighbor_route(warehouse, customers)

        current_route = _build_route_legs(
            warehouse, current_order, delivery_window, day, weather
        )
        optimized_route = _build_route_legs(
            warehouse, optimized_order, delivery_window, day, weather
        )

        current_fuel_cost = current_route["total_fuel_liters"] * fuel_cost_per_liter
        optimized_fuel_cost = optimized_route["total_fuel_liters"] * fuel_cost_per_liter

        distance_saved = (
            current_route["total_distance"] - optimized_route["total_distance"]
        )
        time_saved = current_route["total_time"] - optimized_route["total_time"]
        fuel_saved_inr = current_fuel_cost - optimized_fuel_cost

        return jsonify(
            {
                "warehouse": warehouse,
                "filters": {
                    "delivery_window": delivery_window,
                    "day": day,
                    "weather": weather,
                    "fuel_cost_per_liter": round(float(fuel_cost_per_liter), 2),
                },
                "current_route": current_route["legs"],
                "optimized_route": optimized_route["legs"],
                "metrics": {
                    "current": {
                        "total_distance": current_route["total_distance"],
                        "total_time": current_route["total_time"],
                        "total_fuel_liters": current_route["total_fuel_liters"],
                        "fuel_cost_inr": round(float(current_fuel_cost), 2),
                    },
                    "optimized": {
                        "total_distance": optimized_route["total_distance"],
                        "total_time": optimized_route["total_time"],
                        "total_fuel_liters": optimized_route["total_fuel_liters"],
                        "fuel_cost_inr": round(float(optimized_fuel_cost), 2),
                    },
                    "improvement": {
                        "distance_saved_km": round(float(distance_saved), 2),
                        "time_saved_hrs": round(float(time_saved), 2),
                        "fuel_saved_inr": round(float(fuel_saved_inr), 2),
                        "distance_saved_pct": round(
                            (distance_saved / current_route["total_distance"] * 100)
                            if current_route["total_distance"]
                            else 0,
                            2,
                        ),
                        "time_saved_pct": round(
                            (time_saved / current_route["total_time"] * 100)
                            if current_route["total_time"]
                            else 0,
                            2,
                        ),
                        "fuel_saved_pct": round(
                            (fuel_saved_inr / current_fuel_cost * 100)
                            if current_fuel_cost
                            else 0,
                            2,
                        ),
                    },
                },
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True)
