from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
import ipaddress
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------- Utilitats ----------
def sh(cmd, timeout=30):
    """Executa una comanda al sistema i retorna (returncode, stdout+stderr)."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return res.returncode, (res.stdout or "") + (res.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT: {' '.join(cmd)}"
    except Exception as e:
        return 1, f"ERROR executant {' '.join(cmd)}: {e}"

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

# ---------- Funció genèrica per systemctl ----------
def run_service_cmd(service, cmd):
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

def pick_dhcp_pool(network: ipaddress.IPv4Network, router_ip: ipaddress.IPv4Address, excluded_set, pool_size: int):
    """Troba un rang contigu de 'pool_size' IPs dins de la xarxa evitant excloses i la IP del router."""
    usable = [ip for ip in network.hosts()]
    # Evitar router i excloses
    blocked = set(excluded_set)
    blocked.add(router_ip)

    # prova cada inici possible fins trobar un bloc contigu net
    for i in range(0, len(usable) - pool_size):
        candidate = usable[i:i+pool_size]
        if any(ip in blocked for ip in candidate):
            continue
        return candidate[0], candidate[-1]
    # fallback: tria el primer bloc ignorant exclusions (avis)
    return usable[1], usable[1+pool_size-1]

@app.route('/dhcp/configure', methods=['POST'])
def dhcp_configure():
    data = request.get_json(force=True)
    try:
        network_cidr = data.get("network_cidr", "").strip()
        router_ip_s = data.get("router_ip", "").strip()
        iface = data.get("iface", "").strip()
        dns_list_s = data.get("dns_list", "").strip()  # ex: "1.1.1.1,8.8.8.8"
        excluded_s = data.get("excluded", "").strip()
        pool_size = int(data.get("pool_size", 50))
        default_lease = int(data.get("default_lease", 600))
        max_lease = int(data.get("max_lease", 7200))

        if not network_cidr or not router_ip_s or not iface:
            return jsonify({"success": False, "output": "Falten camps obligatoris: network_cidr, router_ip, iface."}), 400

        net = ipaddress.ip_network(network_cidr, strict=False)
        router_ip = ipaddress.ip_address(router_ip_s)
        if router_ip not in net:
            return jsonify({"success": False, "output": "La IP del router no pertany a la xarxa especificada."}), 400

        excluded = set()
        if excluded_s:
            for x in [y.strip() for y in excluded_s.split(",") if y.strip()]:
                try:
                    ipx = ipaddress.ip_address(x)
                    if ipx in net:
                        excluded.add(ipx)
                except Exception:
                    pass

        dns_list = []
        if dns_list_s:
            for x in [y.strip() for y in dns_list_s.split(",") if y.strip()]:
                try:
                    ipx = ipaddress.ip_address(x)
                    dns_list.append(str(ipx))
                except Exception:
                    pass

        start_ip, end_ip = pick_dhcp_pool(net, router_ip, excluded, pool_size)

        dhcp_conf = f"""# Generat automàticament ({datetime.utcnow().isoformat()}Z)
default-lease-time {default_lease};
max-lease-time {max_lease};
authoritative;

option domain-name "local";
option domain-name-servers {', '.join(dns_list) if dns_list else router_ip};

subnet {net.network_address} netmask {net.netmask} {{
  range {start_ip} {end_ip};
  option routers {router_ip};
  option subnet-mask {net.netmask};
  option broadcast-address {net.broadcast_address};
}}
"""
        isc_defaults_path = "/etc/default/isc-dhcp-server"
        dhcpd_conf_path = "/etc/dhcp/dhcpd.conf"

        # Escriure fitxers
        write_file(dhcpd_conf_path, dhcp_conf)

        # Actualitzar interfície a /etc/default/isc-dhcp-server
        defaults_content = f"""# Generat automàticament ({datetime.utcnow().isoformat()}Z)
INTERFACESv4="{iface}"
INTERFACESv6=""
"""
        write_file(isc_defaults_path, defaults_content)

        # Comprovació de sintaxi (si disponible)
        code, check_out = sh(["dhcpd", "-t", "-cf", dhcpd_conf_path], timeout=20)

        # Reinici servei
        rc, out = sh(["systemctl", "restart", "isc-dhcp-server"])

        output = "=== DHCP CONFIGURAT ===\n"
        output += f"Xarxa: {network_cidr}\n"
        output += f"Pool: {start_ip} - {end_ip} ({pool_size} IPs)\n"
        output += f"Router: {router_ip}\nInterfície: {iface}\n"
        if dns_list:
            output += f"DNS: {', '.join(dns_list)}\n"
        if excluded:
            output += f"Exclosos: {', '.join(map(str, excluded))}\n"
        output += f"\nFitxer: {dhcpd_conf_path}\n{dhcp_conf}\n"
        output += f"\nComprovació dhcpd (-t) rc={code}\n{check_out}\n"
        output += f"\nReinici servei rc={rc}\n{out}\n"

        return jsonify({"success": rc == 0 and code in (0, 1), "output": output})
    except Exception as e:
        return jsonify({"success": False, "output": f"Error configurant DHCP: {e}"}), 500

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

@app.route('/dns/configure', methods=['POST'])
def dns_configure():
    data = request.get_json(force=True)
    try:
        domain = data.get("domain", "").strip().rstrip(".")
        server_ip = data.get("server_ip", "").strip()
        ns_host = data.get("ns_host", "ns1").strip()
        forwarders = data.get("forwarders", "").strip()  # "1.1.1.1;8.8.8.8"

        if not domain or not server_ip or not ns_host:
            return jsonify({"success": False, "output": "Falten camps obligatoris: domain, server_ip, ns_host."}), 400

        # Fitxers
        named_local = "/etc/bind/named.conf.local"
        named_opts = "/etc/bind/named.conf.options"
        zone_file = f"/etc/bind/db.{domain}"

        # named.conf.local
        local_conf = f"""// Generat automàticament ({datetime.utcnow().isoformat()}Z)
zone "{domain}" {{
  type master;
  file "{zone_file}";
}};
"""

        # named.conf.options
        forwarders_block = ""
        if forwarders:
            cleaned = [x for x in forwarders.replace(",", ";").split(";") if x.strip()]
            forwarders_block = "        forwarders {\n            " + ";\n            ".join(cleaned) + ";\n        };\n"
        opts_conf = f"""// Generat automàticament ({datetime.utcnow().isoformat()}Z)
options {{
        directory "/var/cache/bind";
{forwarders_block if forwarders_block else ""}
        dnssec-validation auto;
        listen-on-v6 {{ any; }};
        listen-on {{ any; }};
        allow-query {{ any; }};
        recursion yes;
}};
"""

        # Zone file (SOA+NS+A bàsic)
        serial = datetime.utcnow().strftime("%Y%m%d%H")
        zone_content = f""";; Generat automàticament ({datetime.utcnow().isoformat()}Z)
$TTL    604800
@       IN      SOA     {ns_host}.{domain}. admin.{domain}. (
                        {serial} ; Serial
                        604800   ; Refresh
                        86400    ; Retry
                        2419200  ; Expire
                        604800 ) ; Negative Cache TTL
;
@       IN      NS      {ns_host}.{domain}.
@       IN      A       {server_ip}
{ns_host} IN      A       {server_ip}
www     IN      A       {server_ip}
"""

        # Escriure fitxers
        write_file(named_local, local_conf)
        write_file(named_opts, opts_conf)
        write_file(zone_file, zone_content)

        # Comprovació de sintaxi
        rc_check, out_check = sh(["named-checkconf"], timeout=20)
        rc_zone, out_zone = sh(["named-checkzone", domain, zone_file], timeout=20)

        # Reinici
        rc_reload, out_reload = sh(["systemctl", "restart", "bind9"])

        output = "=== BIND9 CONFIGURAT ===\n"
        output += f"Domini: {domain}\nServidor: {server_ip}\nNS: {ns_host}.{domain}\n"
        if forwarders:
            output += f"Forwarders: {forwarders}\n"
        output += f"\n{named_local}\n{local_conf}\n"
        output += f"\n{named_opts}\n{opts_conf}\n"
        output += f"\n{zone_file}\n{zone_content}\n"
        output += f"\nCheckconf rc={rc_check}\n{out_check}\n"
        output += f"Checkzone rc={rc_zone}\n{out_zone}\n"
        output += f"\nReinici rc={rc_reload}\n{out_reload}\n"

        ok = (rc_check == 0 and rc_zone == 0 and rc_reload == 0)
        return jsonify({"success": ok, "output": output})
    except Exception as e:
        return jsonify({"success": False, "output": f"Error configurant BIND9: {e}"}), 500

# ---------- Logs endpoint ----------
@app.route('/logs', methods=['GET'])
def view_logs():
    try:
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
        "version": "2.0",
        "endpoints": {
            "health": "/health",
            "dhcp": {
                "status": "/dhcp/status [GET]",
                "start": "/dhcp/start [POST]",
                "stop": "/dhcp/stop [POST]",
                "restart": "/dhcp/restart [POST]",
                "install": "/dhcp/install [POST]",
                "configure": "/dhcp/configure [POST]"
            },
            "dns": {
                "status": "/dns/status [GET]",
                "start": "/dns/start [POST]",
                "stop": "/dns/stop [POST]",
                "restart": "/dns/restart [POST]",
                "install": "/dns/install [POST]",
                "configure": "/dns/configure [POST]"
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
