from flask import Flask, request, jsonify
from pymongo import MongoClient
import certifi
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Biar bisa diakses Streamlit via browser

# Koneksi ke MongoDB Atlas
client = MongoClient(
    "mongodb+srv://lukasaustin16:lukaslukas@buildless.ev4l8.mongodb.net/?retryWrites=true&w=majority&appName=Buildless",
    tls=True,
    tlsCAFile=certifi.where()
)
db = client["iot_sensors"]
collection = db["assignment"]

@app.route('/')
def index():
    return "Coba API pake POSTMAN"

@app.route("/api/sensor", methods=["POST"])
def receive_data():
    data = request.json
    print("📩 Received data:", data)  # Debug
    try:
        result = collection.insert_one(data)
        data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
        return jsonify({"status": "success", "data": data}), 201
    except Exception as e:
        print("❌ MongoDB Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/sensor/latest", methods=["GET"])
def get_latest_data():
    try:
        data = list(collection.find().sort([("_id", -1)]).limit(1))
        if data:
            data[0]["_id"] = str(data[0]["_id"])  # Convert ObjectId to string
            return jsonify(data[0])
        else:
            return jsonify({})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/sensor/all", methods=["GET"])
def get_all_data():
    try:
        data = list(collection.find().sort([("_id", -1)]).limit(20))
        for item in data:
            item["_id"] = str(item["_id"])  # Convert ObjectId to string for all items
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
