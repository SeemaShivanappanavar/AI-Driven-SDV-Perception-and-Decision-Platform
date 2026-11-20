from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError("Laptop webcam could not be opened")

# Reduce camera buffering to favour the newest available frame.
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

def generate_frames():
    while True:
        success, frame = camera.read()

        if not success:
            time.sleep(0.1)
            continue

        success, buffer = cv2.imencode(
            ".jpg", frame,
            [cv2.IMWRITE_JPEG_QUALITY, 75]
        )

        if not success:
            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + buffer.tobytes()
            + b'\r\n'
        )

@app.route("/health")
def health():
    return {"status": "Webcam server running"}

@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    print("Webcam server listening on port 5001 (use the laptop IP to connect)")
    app.run(host="0.0.0.0", port=5001, threaded=True)
