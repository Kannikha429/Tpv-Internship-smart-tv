from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

CHIP_TOOL = "./chip-tool"
ENDPOINT = "1"

def run_chip(args):
    cmd = [CHIP_TOOL] + args
    print("Running:", cmd)
    subprocess.run(cmd)

@app.route("/")
def home():
    return "Matter Server Running"

@app.route("/on", methods=["POST"])
def on():
    node = str(request.json["node_id"])
    run_chip(["onoff", "on", node, ENDPOINT])
    return jsonify({"status": "on"})

@app.route("/off", methods=["POST"])
def off():
    node = str(request.json["node_id"])
    run_chip(["onoff", "off", node, ENDPOINT])
    return jsonify({"status": "off"})

@app.route("/brightness", methods=["POST"])
def brightness():
    node = str(request.json["node_id"])
    level = str(request.json["level"])
    run_chip(["levelcontrol", "move-to-level", level, "1", node, ENDPOINT])
    return jsonify({"status": "brightness set"})

@app.route("/color", methods=["POST"])
def color():
    node = str(request.json["node_id"])
    hue = str(request.json["hue"])
    sat = str(request.json["sat"])
    run_chip(["colorcontrol", "move-to-hue-and-saturation", hue, sat, "1", node, ENDPOINT])
    return jsonify({"status": "color set"})

app.run(host="0.0.0.0", port=5000)