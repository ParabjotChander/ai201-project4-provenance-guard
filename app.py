import uuid
import json
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timezone
from config import LOG_PATH
from signal1 import signal1_response

# Content ID: a05bc3f5-ee58-4409-a443-873393ff0bf4
# 10563a28-820e-4255-81c1-baa11a25c233

app = Flask(__name__)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

@app.route("/")
def home():
    return "Provenance Guard is running."

@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json()
    text = data.get("text")
    creator_id = data.get("creator_id")
    content_id = str(uuid.uuid4())
    
    # Placeholder response — wire in your detection signal next.
    s1_output = signal1_response(text)
    s1_attribution = s1_output['classification']
    s1_score = s1_output['llm_confidence_score']
    

    log_entry = {
        "timestamp": "...",
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": s1_attribution,
        "signal_1_score": s1_score 
    }

    log_event(log_entry)

    return jsonify({
        "content_id": content_id,
        "attribution": s1_attribution,
        "confidence": 0.5,
        "label": "We're not sure who wrote this.",
    })

@app.route("/log", methods=["GET"])
def view_log():
    return jsonify({"entries": read_log()})

@app.route("/appeal", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def appeal():
    data = request.get_json()
    content_id = data.get("content_id")
    reasoning = data.get("creator_reasoning")

    # Update the content's status and log the appeal (see section 6).
    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Your appeal was received and is under review.",
    })

# A Simple Audit Log Helper 
def log_event(entry):
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def read_log(limit=20):
    try:
        with open(LOG_PATH) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []
    return [json.loads(line) for line in lines[-limit:]]


if __name__ == "__main__":
    app.run(port=5000, debug=True)