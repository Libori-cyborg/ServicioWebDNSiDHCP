from flask import Flask, jsonify
from flask_cors import CORS
import subprocess

# NECESARI INSTAL·LAR Python3, pip, flask i flask-cors
# sudo apt -y python3 python3-pio 
# sudo pip3 --upgrade pip
# sudo pip3 install flask flask-cors
# Executar sudo python3 script.py


app = Flask(__name__)
CORS(app)

# ---------- Funció genèrica per systemctl ----------
def run_service_cmd(service, cmd):
    try:
        result = subprocess.run(
            ["systemctl", cmd, service],
            capture_output=True,
            text=True
        )
        output = result.stdout + "\n" + result.stderr
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"output": f"Error executant {cmd} {service}: {e}"})


# ---------- DHCP ----------
@app.route('/dhcp/status', methods=['GET'])
def dhcp_status():
    return run_service_cmd("isc-dhcp-server", "status")

@app.route('/dhcp/start', methods=['POST'])
def dhcp_start():
    return run_service_cmd("isc-dhcp-server", "start")

@app.route('/dhcp/stop', methods=['POST'])
def dhcp_stop():
    return run_service_cmd("isc-dhcp-server", "stop")

@app.route('/dhcp/restart', methods=['POST'])
def dhcp_restart():
    return run_service_cmd("isc-dhcp-server", "restart")

@app.route('/dhcp/install', methods=['POST'])
def dhcp_install():
    try:
        result = subprocess.run(
            ["bash", "-c", "apt update && apt install -y isc-dhcp-server"],
            capture_output=True,
            text=True
        )
        output = result.stdout + "\n" + result.stderr
        return jsonify({"output": "DHCP instal·lat\n" + output})
    except Exception as e:
        return jsonify({"output": f"Error instal·lat DHCP: {e}"})
            

# ---------- DNS ----------
@app.route('/dns/status', methods=['GET'])
def dns_status():
    return run_service_cmd("bind9", "status")

@app.route('/dns/start', methods=['POST'])
def dns_start():
    return run_service_cmd("bind9", "start")

@app.route('/dns/stop', methods=['POST'])
def dns_stop():
    return run_service_cmd("bind9", "stop")

@app.route('/dns/restart', methods=['POST'])
def dns_restart():
    return run_service_cmd("bind9", "restart")
   
@app.route('/dns/install', methods=['POST'])
def dns_install():
    try:
        result = subprocess.run(
            ["bash", "-c", "apt update && apt install -y bind9"],
            capture_output=True,
            text=True
        )
        output = result.stdout + "\n" + result.stderr
        return jsonify({"output": "DNS instal·lat\n" + output})
    except Exception as e:
        return jsonify({"output": f"Error instal·lat DNS: {e}"})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
