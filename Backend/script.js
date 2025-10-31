const API_URL = 'http://localhost:5000';

function updateOutput(message, isError = false) {
  const output = document.getElementById('resultat');
  const timestamp = new Date().toLocaleTimeString('ca-ES');
  const prefix = isError ? '❌ ERROR' : '✅';
  output.textContent = `[${timestamp}] ${prefix}\n${message}\n\n${output.textContent}`;
}

function fetchService(url, method = "GET", body = null) {
  updateOutput(`Executant: ${method} ${url}...`, false);

  const opts = { method: method };
  if (body) {
    opts.headers = { "Content-Type": "application/json" };
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
  const payload = {
    network_cidr: document.getElementById('dhcp_network').value.trim(),
    router_ip: document.getElementById('dhcp_router').value.trim(),
    iface: document.getElementById('dhcp_iface').value.trim(),
    dns_list: document.getElementById('dhcp_dns').value.trim(),
    excluded: document.getElementById('dhcp_excluded').value.trim(),
    pool_size: parseInt(document.getElementById('dhcp_pool').value,10),
    default_lease: parseInt(document.getElementById('dhcp_dflt_lease').value,10),
    max_lease: parseInt(document.getElementById('dhcp_max_lease').value,10)
  };

  if(!payload.network_cidr || !payload.router_ip || !payload.iface || !payload.pool_size){
    alert("Omple com a mínim: Xarxa CIDR, IP del router, Interfície i Nº d'IPs.");
    return;
  }

  fetchService(`${API_URL}/dhcp/configure`, 'POST', payload);
}

function submitDnsConfig(){
  const payload = {
    domain: document.getElementById('dns_domain').value.trim(),
    server_ip: document.getElementById('dns_ip').value.trim(),
    ns_host: document.getElementById('dns_ns').value.trim(),
    forwarders: document.getElementById('dns_forwarders').value.trim()
  };

  if(!payload.domain || !payload.server_ip || !payload.ns_host){
    alert("Omple: Domini, IP del servidor i NS host.");
    return;
  }

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
