// ==========================
// 📡 CONFIGURACIÓ GENERAL
// ==========================
const API_URL = "http://localhost:5000";
const resultat = document.getElementById("resultat");
const backendIndicator = document.getElementById("backendIndicator");
const backendStatusText = document.getElementById("backendStatusText");

// ==========================
// 🔧 FUNCIONS GENERALS
// ==========================
async function execCommand(endpoint) {
  resultat.innerText = "⏳ Executant comanda...";
  try {
    const res = await fetch(`${API_URL}/${endpoint}`);
    const data = await res.text();
    resultat.innerText = data;
  } catch (err) {
    resultat.innerText = "❌ Error de connexió amb el backend.";
  }
}

async function checkBackend() {
  try {
    const res = await fetch(`${API_URL}/ping`);
    if (res.ok) {
      backendIndicator.classList.add("active");
      backendStatusText.textContent = "Backend: Connectat ✅";
    } else {
      throw new Error();
    }
  } catch {
    backendIndicator.classList.remove("active");
    backendStatusText.textContent = "Backend: Desconnectat ❌";
  }
}

// ==========================
// 🧩 SERVEI DHCP
// ==========================
function dhcpStatus() { execCommand("dhcp/status"); }
function dhcpStart() { execCommand("dhcp/start"); }
function dhcpStop() { execCommand("dhcp/stop"); }
function dhcpRestart() { execCommand("dhcp/restart"); }
function dhcpInstall() { execCommand("dhcp/install"); }

// ==========================
// 🌐 SERVEI DNS
// ==========================
function dnsStatus() { execCommand("dns/status"); }
function dnsStart() { execCommand("dns/start"); }
function dnsStop() { execCommand("dns/stop"); }
function dnsRestart() { execCommand("dns/restart"); }
function dnsInstall() { execCommand("dns/install"); }

// ==========================
// 📝 EDICIÓ DE CONFIGURACIÓ
// ==========================
const editorModal = document.getElementById("editorModal");
const configEditor = document.getElementById("configEditor");
const configSelector = document.getElementById("configSelector");

function editConfigs() {
  editorModal.style.display = "flex";
  loadConfigFile();
}

function closeEditor() {
  editorModal.style.display = "none";
}

async function loadConfigFile() {
  const file = configSelector.value;
  resultat.innerText = `📂 Obrint ${file}...`;
  try {
    const res = await fetch(`${API_URL}/config/load?file=${encodeURIComponent(file)}`);
    configEditor.value = await res.text();
  } catch {
    configEditor.value = "❌ Error al carregar el fitxer.";
  }
}

async function saveConfig() {
  const file = configSelector.value;
  const content = configEditor.value;
  resultat.innerText = `💾 Desant ${file}...`;
  try {
    const res = await fetch(`${API_URL}/config/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file, content })
    });
    resultat.innerText = await res.text();
  } catch {
    resultat.innerText = "❌ Error al desar la configuració.";
  }
  closeEditor();
}

// ==========================
// ⚙️ ASSISTENT DHCP (WIZARD)
// ==========================
function openDhcpWizard() {
  document.getElementById("dhcpWizardModal").style.display = "flex";
}

function closeDhcpWizard() {
  document.getElementById("dhcpWizardModal").style.display = "none";
}

async function generateDhcpConfig() {
 const subnetInput = document.getElementById("dhcpNetwork").value.trim();

  // Detectem si hi ha prefix (ex: 192.168.1.0/24)
  let subnet = subnetInput;
  let netmask = "255.255.255.0"; // per defecte

  if (subnetInput.includes("/")) {
    const [ip, prefix] = subnetInput.split("/");
    subnet = ip;
    const prefixNum = parseInt(prefix);

    // Taula bàsica de correspondències
    const prefixToMask = {
      8: "255.0.0.0",
      16: "255.255.0.0",
      24: "255.255.255.0",
      25: "255.255.255.128",
      26: "255.255.255.192",
      27: "255.255.255.224",
      28: "255.255.255.240",
      29: "255.255.255.248",
      30: "255.255.255.252"
    };

    if (prefixToMask[prefixNum]) {
      netmask = prefixToMask[prefixNum];
    }
  }

  const data = {
    subnet,
    netmask,
    range: `${document.getElementById("dhcpRangeStart").value} ${document.getElementById("dhcpRangeEnd").value}`,
    router: document.getElementById("dhcpRouter").value,
    dns: document.getElementById("dhcpDns").value
  };


  resultat.innerText = "⚙️ Generant configuració DHCP...";

  try {
    const res = await fetch(`${API_URL}/config/generate_dhcp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const text = await res.text();
    resultat.innerText = text;
  } catch (err) {
    resultat.innerText = "❌ Error: no s'ha pogut generar el fitxer DHCP.";
  }

  closeDhcpWizard();
}

// ==========================
// 🧹 NETEJA RESULTATS
// ==========================
function clearOutput() {
  resultat.innerText = "";
}

// ==========================
// 🚀 INICIALITZACIÓ
// ==========================
window.onload = () => {
  checkBackend();
  setInterval(checkBackend, 8000); // comprova l’estat cada 8 segons
};
