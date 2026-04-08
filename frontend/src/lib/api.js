const API = process.env.REACT_APP_BACKEND_URL + '/api';

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  localStorage.setItem('token', token);
}

function clearToken() {
  localStorage.removeItem('token');
}

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

async function handleResponse(res) {
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) {
    const message = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  get: async (path) => {
    const res = await fetch(`${API}${path}`, { headers: headers() });
    return handleResponse(res);
  },
  post: async (path, body) => {
    const res = await fetch(`${API}${path}`, { method: 'POST', headers: headers(), body: body !== undefined ? JSON.stringify(body) : undefined });
    return handleResponse(res);
  },
  patch: async (path, body) => {
    const res = await fetch(`${API}${path}`, { method: 'PATCH', headers: headers(), body: JSON.stringify(body) });
    return handleResponse(res);
  },
  del: async (path) => {
    const res = await fetch(`${API}${path}`, { method: 'DELETE', headers: headers() });
    return handleResponse(res);
  },
  upload: async (path, formData) => {
    const h = {};
    const token = getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API}${path}`, { method: 'POST', headers: h, body: formData });
    return handleResponse(res);
  },
};

export { getToken, setToken, clearToken, API };
