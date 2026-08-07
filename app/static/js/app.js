// Shared helpers for all pages

function requireAuth() {
  const token = localStorage.getItem('edcrms_token');
  if (!token) {
    window.location.href = '/';
  }
}

async function apiGet(url) {
  const token = localStorage.getItem('edcrms_token');
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (res.status === 401) {
    localStorage.removeItem('edcrms_token');
    window.location.href = '/';
    return;
  }
  return res.json();
}

async function apiSend(url, method, body) {
  const token = localStorage.getItem('edcrms_token');
  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

function logout() {
  localStorage.removeItem('edcrms_token');
  localStorage.removeItem('edcrms_user');
  window.location.href = '/';
}

// ---- Role-based UI helpers (used by list pages to hide buttons the ----
// ---- current user's role is not allowed to use). ----
const ROLE_LEVELS = { "Super Admin": 4, "Admin": 3, "Engineer": 2, "Viewer": 1 };

function currentRole() {
  return localStorage.getItem('edcrms_role');
}

function canAtLeast(minRole) {
  return (ROLE_LEVELS[currentRole()] || 0) >= (ROLE_LEVELS[minRole] || 0);
}