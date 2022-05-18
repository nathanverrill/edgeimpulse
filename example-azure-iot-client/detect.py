"""
Run Edge Impulse trained computer vision models on images, videos, directories, streams, etc.
"""
import argparse
import os
import sys
from pathlib import Path
import datetime
from flask import Flask, render_template, send_from_directory, Response
from pyngrok import ngrok

from edge_impulse_linux.image import ImageImpulseRunner
import cv2

# Helper routines for common edge iot tasks
import edge_iot_util
import datetime
import logging

#Initialize the Flask app
app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

class SkillInputs:
    def __init__(self):
        self.sendSummaryFrequency = 5
        self.includeObjectsFilter = []
        self.noSave = True
        self.cameraURL = None

    def parse_twin(self,twin_data):
        logging.info(f'parsing twin_data {twin_data}')
        print(twin_data)

        if "inputs" in twin_data:
            inputs = twin_data["inputs"]
            if "summaryFrequencyMinutes" in inputs:
                self.sendSummaryFrequency = int(inputs["summaryFrequencyMinutes"])
                logging.info(f'Set Summary Frequency to {self.sendSummaryFrequency}')

            if "includeObjectsFilter" in inputs:
                templist = []
                tempstring = inputs["includeObjectsFilter"]
                if tempstring:
                    parts = tempstring.split(',')
                    for item in parts:
                        item = item.strip()
                        if item:
                            templist.append(item)

                self.includeObjectsFilter = templist
                logging.info(f'Set includeObjectsFilters to {self.includeObjectsFilter}')

        self.cameraURL = edge_iot_util.find_camera_url_in_twin_data(twin_data)

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

def gen_classify_stream(impulse: ImageImpulseRunner, stream: cv2.VideoCapture) -> tuple[dict, ...]:
    """ Generator method, runs inference with the provided impulse & opencv video stream

    Returns tuple of inference result and processed image features
    """
    while True:
        success, img = stream.read()
        if success:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            features, cropped = impulse.get_features_from_image(img)

            res = impulse.classify(features)
            yield res, cropped

def optra_stream_impulse_runner(impulse_file_path: str, source: str, viewport: bool = False):
    """Event loop for an Optra skill. Runs an Edge Impulse classifier on a video stream
    """
    start_time = datetime.datetime.now()
    

    # Stream
    source = str(source)
    stream, w, h, fps = init_video_stream(source)

    # Impulse
    impulse = ImageImpulseRunner(impulse_file_path);
    
    # get Impulse info for debugging
    model_info = impulse.init();
    impulse_name = model_info['project']['name']
    labels = model_info['model_parameters']['labels']
    model_type = model_info['model_parameters']['model_type']
    sensor_type = model_info['model_parameters']['sensor']

    print('current time:', datetime.datetime.now())
    print(f'Loaded Impulse {impulse_name}: A {model_type} impulse classifying {labels}')

    # Track all the unique objects seen in a set - no duplicates
    objects_seen = set()
    
    # Run inference
    # print('inference result: ', datetime.datetime.now())
    frame_counter = 0
    for res, img in gen_classify_stream(impulse, stream):
        frame_counter += 1
        #If the last frame is reached, reset the capture and the frame_counter
        if frame_counter == stream.get(cv2.CAP_PROP_FRAME_COUNT):
            frame_counter = 0 
            stream.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if "classification" in res["result"].keys():
            #print('Result (%d ms.) ' % (res['timing']['dsp'] + res['timing']['classification']), end='')
            for label in labels:
                score = res['result']['classification'][label]
                # Implement the Skill Objects Seen Filtering
                if score > threshold:
                    if len(skill_inputs.includeObjectsFilter)>0:
                        if label in skill_inputs.includeObjectsFilter:
                            objects_seen.add(label)
                    else:
                        objects_seen.add(label)
                print('%s: %.2f\t' % (label, score), end='')
            print('', flush=True)

        elif "bounding_boxes" in res["result"].keys():
            #print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
            for bb in res["result"]["bounding_boxes"]:
                #print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
                img = cv2.rectangle(img, (bb['x'], bb['y']), (bb['x'] + bb['width'], bb['y'] + bb['height']), (255, 0, 0), 1)

        # resize to 720x720 for clean viewing
        ret, buffer = cv2.imencode('.jpg', cv2.resize(img, (720, 720)))
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

        # Implement Skill Summary Messages
        # Send IoT message every x minutes with objects that have been seen
        current_time = datetime.datetime.now()
        elapsed_time = current_time - start_time
        if elapsed_time > datetime.timedelta(minutes=skill_inputs.sendSummaryFrequency):
            if objects_seen:
                data = {
                    "objectsDetectedList" : list(objects_seen)
                }
                msg = edge_iot_util.EdgeMessage(data)
                try:
                    module_client.send_message(msg)
                    print(f'Sent IoT Edge message : {str(msg)}')
                except Exception as e:
                    print(f'IoT Edge message send exception {e}: {str(msg)}')
                objects_seen.clear()
            # Reset new start time
            start_time = datetime.datetime.now()

    # if for loop quits, means something stopped the stream and this should exit
    module_client.disconnect()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(optra_stream_impulse_runner('./modelfile.eim', source, True), mimetype='multipart/x-mixed-replace; boundary=frame')

def init_webhooks(base_url):
    # Update inbound traffic via APIs to use the public-facing ngrok URL
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--no_optra', 
            type=bool,
            help='set true if this is not running as an optra device')
    parser.add_argument(
            '--backup-source', 
            type=str,
            help='video source if no Optra Camera is passed to the skill. accepts webcam device id, HTTP, RTSP, or RTMP')
    args, unknown = parser.parse_known_args()

    if not args.no_optra:
        skill_inputs = SkillInputs()

        # We need a IoT module client to get our input parameters and send messages
        module_client = edge_iot_util.setup_iot_module_client()

        # Fetch twin data and parse it for skill parameters
        twin_data = edge_iot_util.get_iot_twin_parameters(module_client)
        skill_inputs.parse_twin(twin_data)

        # Setup a listener for future twin changes
        def handle_twin_changed(twin_patch):
            logging.info(f"twin_changed")
            skill_inputs.parse_twin(twin_patch)
    
        module_client.on_twin_desired_properties_patch_received = handle_twin_changed

        # Use Camera if one has been setup for our device
        if skill_inputs.cameraURL:
            source = skill_inputs.cameraURL
            print(f'Found the camera {source}')
        else:
            source = args.backup_source
            print(f'No Camera Found, using passed in source')
    else:
        source 

    # Initialize our ngrok settings into Flask
    app.config.from_mapping(
        BASE_URL="http://localhost:5000",
    )

    port = 5000

    # Open a ngrok tunnel to the dev server
    ngrok.set_auth_token(os.environ.get("NGROK_AUTH_TOKEN"))
    public_url = ngrok.connect(port, hostname="ei-optra.ngrok.io").public_url
    print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}\"".format(public_url, port))

    # Update any base URLs or webhooks to use the public ngrok URL
    app.config["BASE_URL"] = public_url
    init_webhooks(public_url)

    app.run()

