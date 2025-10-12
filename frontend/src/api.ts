// api.ts
import axios, { type AxiosInstance } from 'axios';

// Em desenvolvimento usamos o proxy do Vite.
// Mantemos a base como caminho relativo para
// funcionar tanto dentro quanto fora de containers.
const baseURL = `/api/v1`;

const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 10000, // 10 segundos
  headers: {
    'Content-Type': 'application/json',
  },
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
  console.log('[api] baseURL =', api.defaults.baseURL);
}
