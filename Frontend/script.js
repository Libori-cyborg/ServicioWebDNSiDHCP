const API_URL = `${window.location.protocol}//${window.location.hostname}:5000`;

const API_KEY = "clase123";  // 🔑 misma clave que en Flask


function updateOutput(message, isError = false) {
  const output = document.getElementById('resultat');
  const timestamp = new Date().toLocaleTimeString('ca-ES');
  const prefix = isError ? '❌ ERROR' : '✅';
  output.textContent = `[${timestamp}] ${prefix}\n${message}\n\n${output.textContent}`;
}

function fetchService(url, method = "GET", body = null) {
  updateOutput(`Executant: ${method} ${url}...`, false);

 const opts = {
  method: method,
  headers: {
    "X-API-KEY": API_KEY
  }
  };

  if (body) {
    opts.headers = {
  "Content-Type": "application/json",
  "X-API-KEY": API_KEY
  };
    opts.body = JSON.stringify(body);
  }

  fetch(url, opts)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      updateOutput(data.output || JSON.stringify(data, null, 2), !data.success && data.success !== undefined);
    })
    .catch(err => {
      updateOutput(`Error de connexió: ${err.message}\nAssegura't que el backend està executant-se (sudo python3 script.py)`, true);
      updateBackendStatus(false);
    });
}

function updateBackendStatus(isActive) {
  const indicator = document.getElementById('backendIndicator');
  const statusText = document.getElementById('backendStatusText');

  if (isActive) {
    indicator.classList.add('active');
    statusText.textContent = 'Backend: ✅ Actiu';
  } else {
    indicator.classList.remove('active');
    statusText.textContent = 'Backend: ❌ Inactiu';
  }
}

function checkBackend() {
  updateOutput('Comprovant connexió amb el backend...', false);

  fetch(`${API_URL}/dhcp/status`)
    .then(res => {
      if (res.ok) {
        updateBackendStatus(true);
        updateOutput('Backend connectat correctament! ✅', false);
      } else {
        throw new Error('Backend no respon');
      }
    })
    .catch(err => {
      updateBackendStatus(false);
      updateOutput(`No es pot connectar amb el backend.\nExecuta: sudo python3 script.py`, true);
    });
}

// ---------- Validacions ----------
function validateIP(ip) {
  const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
  if (!ipRegex.test(ip)) return false;
  
  const parts = ip.split('.');
  return parts.every(part => {
    const num = parseInt(part, 10);
    return num >= 0 && num <= 255;
  });
}

function validateCIDR(cidr) {
  const parts = cidr.split('/');
  if (parts.length !== 2) return false;
  
  const ip = parts[0];
  const mask = parseInt(parts[1], 10);
  
  return validateIP(ip) && mask >= 0 && mask <= 32;
}

function validateInterface(iface) {
  // Permet noms d'interfície comuns: eth0, enp0s3, wlan0, etc.
  const ifaceRegex = /^[a-zA-Z0-9]+$/;
  return ifaceRegex.test(iface) && iface.length > 0 && iface.length < 16;
}

function validateDomain(domain) {
  // Valida dominis bàsics
  const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-_.]*[a-zA-Z0-9]$/;
  return domainRegex.test(domain) && domain.length > 1 && domain.length < 255;
}

function validateHostname(hostname) {
  // Valida noms d'host
  const hostnameRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$/;
  return hostnameRegex.test(hostname) && hostname.length > 0 && hostname.length < 64;
}

function showError(message) {
  const modal = document.createElement('div');
  modal.className = 'error-modal';
  modal.innerHTML = `
    <div class="error-content">
      <h3>⚠️ Error de Validació</h3>
      <p>${message}</p>
      <button onclick="this.parentElement.parentElement.remove()" class="btn btn-close">Tancar</button>
    </div>
  `;
  document.body.appendChild(modal);
  setTimeout(() => modal.remove(), 5000);
}

// ---------- DHCP ----------
function dhcpStatus() { fetchService(`${API_URL}/dhcp/status`); }
function dhcpStart() { fetchService(`${API_URL}/dhcp/start`, 'POST'); }
function dhcpStop() { fetchService(`${API_URL}/dhcp/stop`, 'POST'); }
function dhcpRestart() { fetchService(`${API_URL}/dhcp/restart`, 'POST'); }
function dhcpInstall() { fetchService(`${API_URL}/dhcp/install`, 'POST'); }

// ---------- DNS ----------
function dnsStatus() { fetchService(`${API_URL}/dns/status`); }
function dnsStart() { fetchService(`${API_URL}/dns/start`, 'POST'); }
function dnsStop() { fetchService(`${API_URL}/dns/stop`, 'POST'); }
function dnsRestart() { fetchService(`${API_URL}/dns/restart`, 'POST'); }
function dnsInstall() { fetchService(`${API_URL}/dns/install`, 'POST'); }

// ---------- Logs i Configuració ----------
function openLogs() {
  updateOutput('📂 Obrint sortides del sistema...', false);

  fetch(`${API_URL}/logs`)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      updateOutput(data.output, false);
    })
    .catch(err => {
      updateOutput(`Error en obrir sortides: ${err.message}`, true);
    });
}

function editConfigs() {
  document.getElementById("editorModal").style.display = "flex";
  loadConfigFile();
}

function closeEditor() {
  document.getElementById("editorModal").style.display = "none";
}

function loadConfigFile() {
  const path = document.getElementById("configSelector").value;
  updateOutput(`📄 Obrint fitxer: ${path}`, false);

  if (path === "/etc/default/isc-dhcp-server") {
    updateOutput("💡 Consell: en aquest fitxer pots definir la interfície de xarxa per al DHCP.\nExemple:\nINTERFACESv4=\"enp0s3\"", false);
  }

  fetch(`${API_URL}/config?path=${encodeURIComponent(path)}`)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      document.getElementById("configEditor").value = data.content || "";
      document.getElementById("editorTitle").textContent = `📝 Editant: ${path}`;
      updateOutput(`Fitxer carregat correctament ✅`, false);
    })
    .catch(err => {
      updateOutput(`Error carregant fitxer: ${err.message}`, true);
    });
}

function saveConfig() {
  const path = document.getElementById("configSelector").value;
  const content = document.getElementById("configEditor").value;
  updateOutput(`💾 Desant canvis a: ${path}`, false);

  fetch(`${API_URL}/config/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, content })
  })
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      updateOutput(data.output, !data.success);
      if (data.success) alert("Fitxer desat correctament ✅");
    })
    .catch(err => {
      updateOutput(`Error desant fitxer: ${err.message}`, true);
    });
}

// ---------- Wizards ----------
function openDhcpWizard(){ document.getElementById('dhcpModal').style.display='flex'; }
function closeDhcpWizard(){ document.getElementById('dhcpModal').style.display='none'; }
function openDnsWizard(){ document.getElementById('dnsModal').style.display='flex'; }
function closeDnsWizard(){ document.getElementById('dnsModal').style.display='none'; }

function submitDhcpConfig(){
  const network_cidr = document.getElementById('dhcp_network').value.trim();
  const router_ip = document.getElementById('dhcp_router').value.trim();
  const iface = document.getElementById('dhcp_iface').value.trim();
  const dns_list = document.getElementById('dhcp_dns').value.trim();
  const excluded = document.getElementById('dhcp_excluded').value.trim();
  const pool_size = parseInt(document.getElementById('dhcp_pool').value, 10);
  const default_lease = parseInt(document.getElementById('dhcp_dflt_lease').value, 10);
  const max_lease = parseInt(document.getElementById('dhcp_max_lease').value, 10);

  // Validacions
  if (!network_cidr || !router_ip || !iface || !pool_size) {
    showError("Omple com a mínim: Xarxa CIDR, IP del router, Interfície i Nº d'IPs.");
    return;
  }

  if (!validateCIDR(network_cidr)) {
    showError("Format de xarxa CIDR invàlid. Exemple: 192.168.10.0/24");
    return;
  }

  if (!validateIP(router_ip)) {
    showError("IP del router invàlida. Exemple: 192.168.10.1");
    return;
  }

  if (!validateInterface(iface)) {
    showError("Nom d'interfície invàlid. Exemples: eth0, enp0s3, wlan0");
    return;
  }

  if (pool_size < 2 || pool_size > 65000) {
    showError("El número d'IPs ha d'estar entre 2 i 65000");
    return;
  }

  if (default_lease < 60 || max_lease < default_lease) {
    showError("Temps de lloguer invàlids. El temps per defecte ha de ser mínim 60s i el màxim ha de ser major.");
    return;
  }

  // Validar DNS si s'han especificat
  if (dns_list) {
    const dnsIps = dns_list.split(',').map(s => s.trim());
    for (const ip of dnsIps) {
      if (!validateIP(ip)) {
        showError(`IP DNS invàlida: ${ip}`);
        return;
      }
    }
  }

  // Validar IPs excloses si s'han especificat
  if (excluded) {
    const excludedIps = excluded.split(',').map(s => s.trim());
    for (const ip of excludedIps) {
      if (!validateIP(ip)) {
        showError(`IP exclosa invàlida: ${ip}`);
        return;
      }
    }
  }

  const payload = {
    network_cidr,
    router_ip,
    iface,
    dns_list,
    excluded,
    pool_size,
    default_lease,
    max_lease
  };

  closeDhcpWizard();
  fetchService(`${API_URL}/dhcp/configure`, 'POST', payload);
}

function submitDnsConfig(){
  const domain = document.getElementById('dns_domain').value.trim();
  const server_ip = document.getElementById('dns_ip').value.trim();
  const ns_host = document.getElementById('dns_ns').value.trim();
  const forwarders = document.getElementById('dns_forwarders').value.trim();

  // Validacions
  if (!domain || !server_ip || !ns_host) {
    showError("Omple: Domini, IP del servidor i NS host.");
    return;
  }

  if (!validateDomain(domain)) {
    showError("Format de domini invàlid. Exemple: lan.local o exemple.com");
    return;
  }

  if (!validateIP(server_ip)) {
    showError("IP del servidor invàlida. Exemple: 192.168.10.2");
    return;
  }

  if (!validateHostname(ns_host)) {
    showError("Nom d'host NS invàlid. Exemple: ns1 o dns1");
    return;
  }

  // Validar forwarders si s'han especificat
  if (forwarders) {
    const fwdIps = forwarders.replace(/;/g, ',').split(',').map(s => s.trim()).filter(s => s);
    for (const ip of fwdIps) {
      if (!validateIP(ip)) {
        showError(`IP forwarder invàlida: ${ip}`);
        return;
      }
    }
  }

  const payload = {
    domain,
    server_ip,
    ns_host,
    forwarders
  };

  closeDnsWizard();
  fetchService(`${API_URL}/dns/configure`, 'POST', payload);
}

// ---------- Utilitats ----------
function clearOutput() {
  document.getElementById('resultat').textContent = "Esperant comandes...";
}

// Comprovar backend a l'iniciar
window.addEventListener('load', () => {
  setTimeout(checkBackend, 500);
});