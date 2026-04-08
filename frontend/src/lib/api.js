const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  localStorage.setItem('token', token);
}

function clearToken() {
  localStorage.removeItem('token');
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API}${path}`, { ...options, headers, credentials: 'include' });
  if (res.status === 401) {
    clearToken();
    window.location.href = '/auth';
    throw new Error('Unauthorized');
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = data?.detail;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg) || res.statusText);
  }
  return data;
}

export const api = {
  get: (path) => apiFetch(path),
  post: (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: (path, body) => apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) }),
  del: (path) => apiFetch(path, { method: 'DELETE' }),
  upload: (path, formData) => apiFetch(path, { method: 'POST', body: formData }),
  getToken,
  setToken,
  clearToken,
  API_URL: API,
};
