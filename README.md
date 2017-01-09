Securitas
---------
Home safety system using Raspberry Pi and Nexmo API.


* Uses Raspberry Pi camera for motion detection
* Uses Sense HAT for heat detection
* Uploads pictures taken to Dropbox
* Sends SMS via Nexmo

Watch demo on YouTube:

[![Securitas demo](https://i.ytimg.com/vi/PaA48O9YiLc/0.jpg?time=1483920263101)](https://youtu.be/PaA48O9YiLc)

How to run:
* `export FLASK_APP=server.py`
* `flask run --host=0.0.0.0 --port=8000`
* Visit `/start` (or configure Alexa to make a web request to this URL) to start detection
* Visit `/stop` to stop detection