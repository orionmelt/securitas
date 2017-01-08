import json
import subprocess

from dropbox.client import DropboxOAuth2FlowNoRedirect
from dropbox.client import DropboxClient

from flask import Flask, render_template, redirect, request
app = Flask(__name__)
flow = None
process = None

config = json.load(open("conf.json"))

@app.route("/")
def home():
    global flow
    dropbox_flow_url = None
    if "dropbox_token" not in config:
        flow = DropboxOAuth2FlowNoRedirect(config["dropbox_key"], config["dropbox_secret"])
        dropbox_flow_url = str(flow.start())
    return render_template("index.html", config=config, dropbox_flow_url=dropbox_flow_url)

@app.route("/auth-dropbox", methods=['POST'])
def auth_dropbox():
    global flow
    authcode = request.form["authcode"]
    if not authcode:
        return redirect("/")
    (access_token, _) = flow.finish(authcode)
    config["dropbox_token"] = access_token
    json.dump(config, open("conf.json", "w"))
    return redirect("/")


@app.route("/start")
def start_monitoring():
    global process
    process = subprocess.Popen("exec python securitas.py --conf conf.json", shell=True)
    return "OK"

@app.route("/stop")
def stop_monitoring():
    global processs
    process.kill()
    return "OK"
