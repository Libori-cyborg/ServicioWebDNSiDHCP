const API_URL = `${location.protocol}//${location.hostname}:5000`;
let API_KEY = null;

// ================= LOGIN =================

function login() {
  const key = document.getElementById("loginKey").value;
  const err = document.getElementById("loginError");

  fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key })
  })
  .then(r => {
    if (!r.ok) throw new Error();
    API_KEY = key;
    sessionStorage.setItem("auth", key);
    document.getElementById("loginModal").style.display = "none";
    document.getElementById("app").style.display = "block";
  })
  .catch(() => {
    err.textContent = "❌ Clau incorrecta";
  });
}

function logout() {
  sessionStorage.clear();
  location.reload();
}

function requireAuth() {
  if (!API_KEY) {
    alert("No autoritzat");
    return false;
  }
  return true;
}

// ================= UTIL =================

function updateOutput(msg) {
  document.getElementById("resultat").textContent = msg;
}

function fetchService(url, method="GET") {
  if (!requireAuth()) return;

  fetch(url, {
    method,
    headers: { "X-API-KEY": API_KEY }
  })
  .then(r => r.json())
  .then(d => updateOutput(d.output))
  .catch(e => updateOutput(e.message));
}

// ================= SERVICES =================

const dhcpStatus = () => fetchService(`${API_URL}/dhcp/status`);
const dhcpStart  = () => fetchService(`${API_URL}/dhcp/start`, "POST");
const dhcpStop   = () => fetchService(`${API_URL}/dhcp/stop`, "POST");

const dnsStatus = () => fetchService(`${API_URL}/dns/status`);
const dnsStart  = () => fetchService(`${API_URL}/dns/start`, "POST");
const dnsStop   = () => fetchService(`${API_URL}/dns/stop`, "POST");

// ================= INIT =================

window.onload = () => {
  const saved = sessionStorage.getItem("auth");
  if (saved) {
    API_KEY = saved;
    document.getElementById("loginModal").style.display = "none";
    document.getElementById("app").style.display = "block";
  }
};
