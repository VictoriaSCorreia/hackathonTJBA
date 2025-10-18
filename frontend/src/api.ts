// api.ts
import axios, { type AxiosInstance } from 'axios';

// Em desenvolvimento usamos o proxy do Vite.
// Também suportamos override via VITE_API_URL para apontar direto pro backend.
// Mantemos a base como caminho relativo por padrão para funcionar dentro/fora de containers.
const baseURL = (import.meta as any)?.env?.VITE_API_URL
  ? `${(import.meta as any).env.VITE_API_URL.replace(/\/?$/,'')}/api/v1`
  : `/api/v1`;

// Tempo padrão de timeout aumentado para suportar a fase de resposta final
// (chamada ao modelo pode levar >60s). Permitimos override via VITE_API_TIMEOUT_MS.
const defaultTimeout = 180000; // 180 segundos
const timeoutMs = Number((import.meta as any)?.env?.VITE_API_TIMEOUT_MS) || defaultTimeout;

const api: AxiosInstance = axios.create({
  baseURL,
  timeout: timeoutMs,
  // Do NOT set a global Content-Type here; let Axios/browser infer it
});

// Interceptor para anexar o guest_id a cada requisição
api.interceptors.request.use((config) => {
  try {
    const guestId = localStorage.getItem('guest_id');
    if (guestId) {
      // Axios headers typings aceitam string | number | boolean
      (config.headers as any)['X-Guest-Id'] = guestId;
    }
  } catch (e) {
    // Em ambientes sem localStorage, apenas ignore
  }

  // Se o corpo da requisição for FormData, remova qualquer Content-Type
  // para que o browser defina 'multipart/form-data' com boundary automaticamente.
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    if (config.headers) {
      delete (config.headers as any)['Content-Type'];
    }
  } else {
    // Para requisições com corpo JSON, garanta Content-Type apropriado se não definido
    const method = String(config.method || '').toLowerCase();
    const hasBody = ['post', 'put', 'patch'].includes(method);
    if (hasBody) {
      const ct = (config.headers as any)?.['Content-Type'];
      if (!ct) {
        (config.headers as any)['Content-Type'] = 'application/json';
      }
    }
  }

  return config;
});

// Função para garantir sessão de convidado
export async function ensureGuestSession(): Promise<string | null> {
  try {
    const existing = localStorage.getItem('guest_id');
    if (existing) return existing;

    const resp = await api.post('/sessions');
    const guestId = resp?.data?.guest_id as string | undefined;
    if (guestId) {
      localStorage.setItem('guest_id', guestId);
      return guestId;
    }
    console.error('Sessão de convidado criada sem guest_id no payload.');
    return null;
  } catch (err) {
    console.error('Falha ao criar sessão de convidado:', err);
    return null;
  }
}

export default api;

// Log útil apenas em dev para depuração de baseURL
if (import.meta.env.DEV) {
  // eslint-disable-next-line no-console
  console.log('[api] baseURL =', api.defaults.baseURL, 'timeoutMs =', timeoutMs);
}
