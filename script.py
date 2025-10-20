from flask import Flask, jsonify
from flask_cors import CORS
import subprocess

# INSTAL·LACIÓ NECESSÀRIA:
# sudo apt update
# sudo apt install -y python3 python3-pip
# sudo pip3 install --upgrade pip
# sudo pip3 install flask flask-cors
#
# EXECUTAR AMB:
# sudo python3 script.py

app = Flask(__name__)
CORS(app)

# ---------- Funció genèrica per systemctl ----------
def run_service_cmd(service, cmd):
    """Executa una comanda systemctl per a un servei."""
    try:
        result = subprocess.run(
            ["systemctl", cmd, service],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout + "\n" + result.stderr
        
        # Afegir informació addicional
        status_info = f"=== Comanda: systemctl {cmd} {service} ===\n"
        status_info += f"Codi de sortida: {result.returncode}\n"
        status_info += "=" * 50 + "\n\n"
        
        return jsonify({
            "output": status_info + output,
            "success": result.returncode == 0,
            "command": f"systemctl {cmd} {service}"
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            "output": f"TIMEOUT: La comanda 'systemctl {cmd} {service}' ha trigat massa temps.",
            "success": False
        })
    except Exception as e:
        return jsonify({
            "output": f"ERROR executant '{cmd}' per al servei '{service}':\n{str(e)}",
            "success": False
        })


# ---------- Funció per instal·lar paquets ----------
def install_package(package_name, service_name):
    """Instal·la un paquet usant apt."""
    try:
        update_result = subprocess.run(
            ["apt", "update"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        install_result = subprocess.run(
            ["apt", "install", "-y", package_name],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = "=== APT UPDATE ===\n"
        output += update_result.stdout + "\n" + update_result.stderr + "\n\n"
        output += f"=== INSTAL·LANT {package_name.upper()} ===\n"
        output += install_result.stdout + "\n" + install_result.stderr + "\n"
        
        if install_result.returncode == 0:
            output += f"\n✅ {service_name} instal·lat correctament!\n"
        else:
            output += f"\n❌ Error durant la instal·lació de {service_name}\n"
        
        return jsonify({
            "output": output,
            "success": install_result.returncode == 0
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            "output": f"TIMEOUT: La instal·lació de {package_name} ha trigat massa temps.",
            "success": False
        })
    except Exception as e:
        return jsonify({
            "output": f"ERROR durant la instal·lació de {service_name}:\n{str(e)}",
            "success": False
        })


# ---------- Endpoint de health check ----------
@app.route('/health', methods=['GET'])
def health_check():
    """Comprova que el backend està funcionant."""
    return jsonify({
        "status": "ok",
        "message": "Backend Flask actiu i funcionant",
        "services": ["DHCP (isc-dhcp-server)", "DNS (bind9)"]
    })


# ---------- DHCP (isc-dhcp-server) ----------
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
    return install_package("isc-dhcp-server", "DHCP")


# ---------- DNS (bind9) ----------
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
    return install_package("bind9", "DNS")


# ---------- Informació de l'API ----------
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "API de Control de Serveis DHCP i DNS",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "dhcp": {
                "status": "/dhcp/status [GET]",
                "start": "/dhcp/start [POST]",
                "stop": "/dhcp/stop [POST]",
                "restart": "/dhcp/restart [POST]",
                "install": "/dhcp/install [POST]"
            },
            "dns": {
                "status": "/dns/status [GET]",
                "start": "/dns/start [POST]",
                "stop": "/dns/stop [POST]",
                "restart": "/dns/restart [POST]",
                "install": "/dns/install [POST]"
            }
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Iniciant servidor Flask...")
    print("=" * 60)
    print("📡 Servidor escoltant a: http://0.0.0.0:5000")
    print("⚠️  Recorda: Aquest script necessita permisos sudo!")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=5000, debug=False)