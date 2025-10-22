from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os

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

# ---------- Logs endpoint ----------
@app.route('/logs', methods=['GET'])
def view_logs():
    """Mostra els fitxers de log dels serveis DHCP i DNS."""
    try:
        # Exemple simple: llegir últimes 20 línies de /var/log/syslog
        dhcp_log = subprocess.run(
            ["tail", "-n", "20", "/var/log/syslog"],
            capture_output=True, text=True, timeout=30
        ).stdout
        bind_log = subprocess.run(
            ["tail", "-n", "20", "/var/log/syslog"],
            capture_output=True, text=True, timeout=30
        ).stdout

        output = "=== ÚLTIMES SORTIDES DEL SISTEMA ===\n"
        output += "\n--- DHCP (isc-dhcp-server) ---\n" + dhcp_log
        output += "\n--- DNS (bind9) ---\n" + bind_log
        return jsonify({"output": output, "success": True})
    except Exception as e:
        return jsonify({"output": f"Error llegint logs: {str(e)}", "success": False})

# ---------- Config files endpoints ----------
@app.route('/config', methods=['GET'])
def get_config():
    """Llegeix el contingut d’un fitxer de configuració."""
    path = request.args.get('path')
    if not path or not os.path.exists(path):
        return jsonify({"content": "", "success": False, "output": f"No s'ha trobat el fitxer {path}"})
    try:
        with open(path, 'r') as f:
            content = f.read()
        return jsonify({"content": content, "success": True})
    except Exception as e:
        return jsonify({"content": "", "success": False, "output": str(e)})

@app.route('/config/save', methods=['POST'])
def save_config():
    """Desa el contingut d’un fitxer de configuració."""
    data = request.get_json()
    path = data.get("path")
    content = data.get("content")

    if not path or not os.path.exists(path):
        return jsonify({"success": False, "output": f"No s'ha trobat el fitxer {path}"})
    try:
        with open(path, 'w') as f:
            f.write(content)
        return jsonify({"success": True, "output": f"Fitxer {path} desat correctament ✅"})
    except Exception as e:
        return jsonify({"success": False, "output": f"Error desant {path}: {str(e)}"})

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
            },
            "logs": "/logs [GET]",
            "config": {
                "get": "/config?path=<ruta> [GET]",
                "save": "/config/save [POST]"
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
