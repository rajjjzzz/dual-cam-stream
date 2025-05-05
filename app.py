from flask import Flask, Response, render_template
from picamera2 import Picamera2, Preview
from libcamera import Transform
import cv2
import time
import threading

app = Flask(__name__)

# ------------ Pi Camera Setup ------------
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"size": (640, 480)},
    transform=Transform(hflip=1)
))
picam2.start()
time.sleep(2)  # Let the camera warm up

# Enable auto white balance temporarily
picam2.set_controls({"AwbEnable": True})
time.sleep(2)  # Let it settle and adjust

# Get the auto-detected color gains
gains = picam2.capture_metadata()["ColourGains"]
print("Auto-detected gains:", gains)

# Lock the gains to prevent color drift
picam2.set_controls({
    "AwbEnable": False,
    "ColourGains": gains
})


# ------------ USB Webcam Setup ------------
usb_cam = cv2.VideoCapture(1)  # Change to 0 if needed
usb_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
usb_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
usb_cam.set(cv2.CAP_PROP_FPS, 15)  # or try 30


def generate_pi_frames():
    while True:
        frame = picam2.capture_array()
        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
        ret, jpeg = cv2.imencode('.jpg', frame_rgb)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

def generate_usb_frames():
    while True:
        success, frame = usb_cam.read()
        if not success:
            continue
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_pi_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/usb_feed')
def usb_feed():
    return Response(generate_usb_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
