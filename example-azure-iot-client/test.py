#Import necessary libraries
from flask import Flask, render_template, send_from_directory, Response
import cv2
#Initialize the Flask app
app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

def init_video_stream(s: str) -> tuple[cv2.VideoCapture, int, int, int]:
    """ initialize a webcam, RTSP, RTMP, or HTTP stream

    Accepts a string either defining the numeric device id of a webcam, or a supported url

    Returns the opencv streaming object, width, height, and fps
    """
    s = eval(s) if s.isnumeric() else s  # i.e. s = '0' local webcam
    stream = cv2.VideoCapture(s)
    assert stream.isOpened(), f'Failed to initialize video stream {s}'
    w = int(stream.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = stream.get(cv2.CAP_PROP_FPS)  # warning: may return 0 or nan

    stream.read()  # guarantee first read success

    return stream, w, h, fps


camera, w, h, fps = init_video_stream('http://a06c-2600-1700-7d10-425f-d905-3ede-a742-d79.ngrok.io/stream.wmv')

def gen_frames():  
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='localhost', port=49154)
