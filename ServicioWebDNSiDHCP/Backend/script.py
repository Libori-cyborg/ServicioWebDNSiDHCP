from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from functools import wraps
import subprocess
import os

API_KEY = "clase123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "..", "Frontend"),
    static_folder=os.path.join(BASE_DIR, "..", "Frontend"),
    static_url_path=""
)

CORS(app)

# ================= SEGURIDAD =================

def require_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if key != API_KEY:
            return jsonify({
                "success": False,
                "output": "❌ No autorizado"
            }), 401
        return f(*args, **kwargs)
    return decorated

# LOGIN REAL
@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    key = data.get("key", "")
    if key == API_KEY:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

# ================= UTIL =================

def run_service_cmd(service, cmd):
    result = subprocess.run(
        ["systemctl", cmd, service],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    return jsonify({
        "success": result.returncode == 0,
        "output": output
    })

# ================= DHCP =================

@app.route("/dhcp/status")
def dhcp_status():
    return run_service_cmd("isc-dhcp-server", "status")

@app.route("/dhcp/start", methods=["POST"])
@require_key
def dhcp_start():
    return run_service_cmd("isc-dhcp-server", "start")

@app.route("/dhcp/stop", methods=["POST"])
@require_key
def dhcp_stop():
    return run_service_cmd("isc-dhcp-server", "stop")

@app.route("/dhcp/restart", methods=["POST"])
@require_key
def dhcp_restart():
    return run_service_cmd("isc-dhcp-server", "restart")

@app.route("/dhcp/install", methods=["POST"])
@require_key
def dhcp_install():
    return run_service_cmd("isc-dhcp-server", "status")

# ================= DNS =================

@app.route("/dns/status")
def dns_status():
    return run_service_cmd("bind9", "status")

@app.route("/dns/start", methods=["POST"])
@require_key
def dns_start():
    return run_service_cmd("bind9", "start")

@app.route("/dns/stop", methods=["POST"])
@require_key
def dns_stop():
    return run_service_cmd("bind9", "stop")

@app.route("/dns/restart", methods=["POST"])
@require_key
def dns_restart():
    return run_service_cmd("bind9", "restart")

@app.route("/dns/install", methods=["POST"])
@require_key
def dns_install():
    return run_service_cmd("bind9", "status")

# ================= WEB =================

@app.route("/")
def index():
    return render_template("index.html")

# ================= MAIN =================

if __name__ == "__main__":
    print("🚀 Backend Flask activo en http://0.0.0.0:5000")
    print("⚠️ Ejecutar con sudo")
    app.run(host="0.0.0.0", port=5000, debug=False)
