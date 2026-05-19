from flask import Flask, request, jsonify, render_template, Response
import time

app = Flask(__name__)

# ------------------
# DATA STORE
# ------------------
latest_data = {
    "count": 0,
    "total": 0,
    "lat": 0,
    "lng": 0
}

history = []

latest_frame = None


# ------------------
# PUSH endpoint (Jetson -> Server)
# ------------------
@app.route('/upload', methods=['POST'])
def upload():
    global latest_data, history, latest_frame

    # frame
    file = request.files.get("frame")
    if file:
        latest_frame = file.read()

    # data
    data = request.form.to_dict()

    # convert to float safely
    try:
        data = {k: float(v) for k, v in data.items()}
    except:
        return {"status": "bad data"}

    latest_data = data

    # heatmap update
    if data.get("count", 0) > 0:
        history.append({
            "lat": data["lat"],
            "lng": data["lng"],
            "weight": data["count"]
        })

    return {"status": "ok"}


# ------------------
# latest data API
# ------------------
@app.route('/data')
def data():
    return jsonify(latest_data)


# ------------------
# heatmap API
# ------------------
@app.route('/heatmap')
def heatmap():
    return jsonify(history)


# ------------------
# LIVE VIDEO (from memory frame)
# ------------------
def gen():
    global latest_frame

    while True:
        if latest_frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
        time.sleep(0.03)


@app.route('/video')
def video():
    return Response(
        gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# ------------------
# simple AI analysis
# ------------------
@app.route('/analysis')
def analysis():
    total = sum(p["weight"] for p in history)

    if total < 5:
        risk = "Low"
        action = "maintain"
    elif total < 15:
        risk = "Medium"
        action = "increase monitoring"
    else:
        risk = "High"
        action = "action required"

    return f"""
[Risk] {risk}
[Total Activity] {total}
[Action] {action}
"""


# ------------------
# UI
# ------------------
@app.route('/')
def index():
    return render_template('index.html')


# ------------------
# MAIN
# ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
