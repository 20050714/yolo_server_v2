from flask import Flask, request, jsonify, render_template, Response
import time
import requests

app = Flask(__name__)

# ------------------
# data
# ------------------
latest_data = {"count":0,"total":0,"lat":0,"lng":0}
history = []

# ------------------
# Jetson auto
# ------------------
jetsons = {}
TIMEOUT = 5

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    ip = data["ip"]

    jetsons[ip] = {"last": time.time()}
    return {"status":"ok"}

def get_jetson():
    now = time.time()

    # clear if offline
    for ip in list(jetsons.keys()):
        if now - jetsons[ip]["last"] > TIMEOUT:
            del jetsons[ip]

    if not jetsons:
        return None

    return list(jetsons.keys())[-1]

# ------------------
# update data
# ------------------
@app.route('/update', methods=['POST'])
def update():
    global latest_data, history

    latest_data = request.json

    if latest_data["count"] > 0:
        history.append({
            "lat": latest_data["lat"],
            "lng": latest_data["lng"],
            "weight": latest_data["count"]
        })

    return {"status":"ok"}

# ------------------
# API
# ------------------
@app.route('/data')
def data():
    return jsonify(latest_data)

@app.route('/heatmap')
def heatmap():
    return jsonify(history)

# ------------------
# proxy video
# ------------------
@app.route('/video')
def video():
    ip = get_jetson()

    if ip is None:
        return "No Jetson", 503

    url = f"http://{ip}:5000/video"

    return Response(
        requests.get(url, stream=True).raw,
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

# ------------------
# LLM-like
# ------------------
@app.route('/analysis')
def analysis():
    total = sum(p["weight"] for p in history)

    if total < 5:
        risk = "Low"
        action = "maintain"
    elif total < 15:
        risk = "Medium"
        action = "more frequently"
    else:
        risk = "High"
        action = "action now"

    return f"""
[Risk] {risk}
[Total Activity] {total}
[Action] {action}
"""

# ------------------
# index
# ------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------
# main
# ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
