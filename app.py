import uuid
import json
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timezone
from config import LOG_PATH
from signal1 import signal1_response
from signal2 import signal2_response
from confidence_score import compute_confidence_score

# Content ID (Appeal Workflow Test for Milestone 5) 
# aa34a1f6-e9dd-4b99-801f-9a07b6673d8a

transparency_labels = {
    "Likely Human": "This content appears to be human-written with high confidence.",
    "Uncertain": "The system could not confidently determine the origin of this content.",
    "Likely AI": "This content was classified as AI-generated with high confidence"
}

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
    
    s2_output = signal2_response(text)
    s2_score = s2_output['stylometric_score']

    confidence = compute_confidence_score(s1_score, s2_score)

    overall_attribution = ""

    if confidence <= 0.39:
        overall_attribution = "Likely Human"
    elif 0.40 <= confidence <= 0.60:
        overall_attribution = "Uncertain"
    else:
        overall_attribution = "Likely AI"
    
    log_entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": "...",
        "attribution": overall_attribution,
        "confidence": confidence,
        "llm_score": s1_score,
        "stylometric_score": s2_score,
        "status": "classified" 
    }

    log_event(log_entry)

    return jsonify({
        "content_id": content_id,
        "attribution": overall_attribution,
        "confidence": confidence,
        "label": transparency_labels[overall_attribution],
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

    if not content_id:
        return jsonify({"error": "content_id is required."}), 400
    if not reasoning or not reasoning.strip():
        return jsonify({"error": "creator_reasoning is required."}), 400
    
    # Find the original classification entry in the audit log
    all_entries = read_log(limit=None)
    original = next(
        (e for e in all_entries if e.get("content_id") == content_id),
        None
    )

    if original is None:
        return jsonify({"error": "content_id not found in audit log."}), 404

    original_status = original.get("status", "classified")
    if original_status == "under_review":
        return jsonify({
            "content_id": content_id,
            "status": "under_review",
            "message": "An appeal for this content is already under review.",
        }), 409
    
    appeal_entry = {
        "content_id": content_id,
        "creator_id": original.get("creator_id"),
        "event": "appeal_submitted",
        "status": "under_review",
        "original_attribution": original.get("attribution"),
        "original_confidence": original.get("confidence"),
        "llm_score": original.get("llm_score"),
        "stylometric_score": original.get("stylometric_score"),
        "creator_reasoning": reasoning.strip(),
    }
    
    log_event(appeal_entry)
    
    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "original_attribution": original.get("attribution"),
        "message": "Your appeal was received and is under review.",
    }), 200

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
    if limit is None:
        return [json.loads(line) for line in lines]
    return [json.loads(line) for line in lines[-limit:]]


if __name__ == "__main__":
    app.run(port=5000, debug=True)

"""
Submit Workflow: Submit at least 3 entries 
CLI COMMANDS 
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The sun dipped below the horizon, painting the sky in hues of amber and rose. I sat on the porch, coffee in hand, watching the neighborhood slowly go quiet.", "creator_id": "test-user-1"}' | python -m json.tool

curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.", "creator_id": "test-user-1"}' | python -m json.tool

curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won't go back unless someone drags me there", "creator_id": "test-user-1"}' | python -m json.tool  

"""


"""
Appeal Workflow 

CLI COMMAND 
curl -s -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "aa34a1f6-e9dd-4b99-801f-9a07b6673d8a", "creator_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."}' | python -m json.tool

OUTPUT
{
    "content_id": "aa34a1f6-e9dd-4b99-801f-9a07b6673d8a",
    "message": "Your appeal was received and is under review.",
    "original_attribution": "Uncertain",
    "status": "under_review"
}
"""

"""
Rating Limiting Test 

CLI COMMAND 
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test submission for rate limit testing purposes only.", "creator_id": "ratelimit-test"}'
done

TERMINAL:
(.venv) parabjotchander@parabs-air ai201-project4-provenance-guard % for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test submission for rate limit testing purposes only.", "creator_id": "ratelimit-test"}'
done
200
200
200
200
200
200
200
200
200
200
429
429
"""