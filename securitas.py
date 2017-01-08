from pyimagesearch.tempimage import TempImage
from dropbox.client import DropboxOAuth2FlowNoRedirect
from dropbox.client import DropboxClient
from picamera.array import PiRGBArray
from picamera import PiCamera
from sense_hat import SenseHat
import datetime
import imutils
import json
import time
import cv2
import nexmo

conf = json.load(open("conf.json"))
nexmo_client = nexmo.Client(key=conf["nexmo_key"], secret=conf["nexmo_secret"])
dropbox_client = DropboxClient(conf["dropbox_token"])

camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
raw_capture = PiRGBArray(camera, size=tuple(conf["resolution"]))

sense = SenseHat()

print "[SECURITAS] Initializing..."
time.sleep(conf["camera_warmup_time"])
average = None
last_motion_uploaded = last_temp_uploaded = datetime.datetime.now()
motion_counter = 0
timestamp = None

def upload_picture(frame, kind):
    t = TempImage()
    cv2.imwrite(t.path, frame)

    print "[SECURITAS]" + kind + " detected! Uploading photo to Dropbox..."
    path = "{timestamp}.jpg".format(timestamp=timestamp.strftime('%Y%m%d%H%M'))
    dropbox_file = dropbox_client.put_file(path, open(t.path, "rb"))
    media = dropbox_client.media(path)
    print "[SECURITAS] Sending SMS..."
    sms = nexmo_client.send_message({
        'from': conf["nexmo_number"] , 
        'to': conf["phone_number"], 
        'text': 
            kind + ' detected at ' + 
            timestamp.strftime('%Y-%m-%d %I:%M %p') + 
            ': ' + media['url']
    })
    t.cleanup()

for f in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
    frame = f.array
    timestamp = datetime.datetime.now()
    motion = False

    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if average is None:
        print "[SECURITAS] Starting to monitor..."
        average = gray.copy().astype("float")
        raw_capture.truncate(0)
        continue

    cv2.accumulateWeighted(gray, average, 0.5)
    frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(average))

    threshold = cv2.threshold(frame_delta, conf["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
    threshold = cv2.dilate(threshold, None, iterations=2)
    _, contours, _ = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        if cv2.contourArea(c) < conf["min_area"]:
            continue

        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        motion = True

    cv2.putText(
        frame, 
        timestamp.strftime("%a %d %b %Y %I:%M:%S %p"), 
        (10, frame.shape[0] - 10), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.35, 
        (255, 255, 255), 
        1
    )

    if motion:
        if (timestamp - last_motion_uploaded).seconds >= conf["min_upload_seconds"]:
            motion_counter += 1
            
            if motion_counter >= conf["min_motion_frames"]:
                upload_picture(frame, "Motion")

                last_motion_uploaded = timestamp
                motion_counter = 0

    else:
        motion_counter = 0
    if conf["show_video"]:
        cv2.imshow("Securitas", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
    raw_capture.truncate(0)

    if sense.get_temperature() > conf["temp_thresh"] and \
        (timestamp - last_temp_uploaded).seconds >= (conf["min_upload_seconds"] * 4):
        upload_picture(frame, "High temperature")
        last_temp_uploaded = timestamp