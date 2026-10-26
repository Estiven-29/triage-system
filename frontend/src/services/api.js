import axios from 'axios';

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Misma base que la API REST, cambiando http(s) por ws(s).
export const WS_URL = `${API_BASE_URL.replace(/^http/, 'ws')}/ws/triage`;

// Convierte un error de axios en un mensaje legible para el usuario.
// FastAPI devuelve `detail` como string (404) o como lista de errores (422).
export const getErrorMessage = (error, fallback = 'Ocurrió un error inesperado') => {
  if (!error.response) {
    return `No se pudo conectar con el backend (${API_BASE_URL}).`;
  }
  const { detail } = error.response.data || {};
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => `${d.loc?.slice(-1)[0] ?? ''}: ${d.msg}`).join('; ');
  }
  return fallback;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== AUTENTICACIÓN ====================

// El token del personal vive en sessionStorage: se borra al cerrar la
// pestaña. El acceso puede fallar (modo privado, almacenamiento bloqueado),
// por eso cada lectura/escritura va en try/catch.
const TOKEN_KEY = 'triage_staff_token';

export const getAuthToken = () => {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
};

const setAuthToken = (token) => {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // Sin almacenamiento la sesión dura solo mientras la página esté abierta.
  }
};

let onUnauthorized = () => {};

// Permite a la app reaccionar (volver al login) cuando el backend rechaza
// el token por inválido o expirado.
export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler;
};

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLogin = error.config?.url === '/api/auth/login';
    if (error.response?.status === 401 && !isLogin) {
      setAuthToken(null);
      onUnauthorized();
    }
    return Promise.reject(error);
  }
);

export const login = async (employeeId, password) => {
  const response = await api.post('/api/auth/login', { employee_id: employeeId, password });
  setAuthToken(response.data.access_token);
  return response.data.staff;
};

export const getCurrentStaff = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

export const logout = () => setAuthToken(null);

// ==================== CHATBOT ====================

export const startChatbotSession = async (patientData) => {
  try {
    const response = await api.post('/api/chatbot/start', patientData);
    return response.data;
  } catch (error) {
    console.error('Error starting chatbot session:', error);
    throw error;
  }
};

export const sendChatbotMessage = async (sessionId, message) => {
  try {
    const response = await api.post('/api/chatbot/message', {
      session_id: sessionId,
      message: message,
    });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

// ==================== CLASIFICACIÓN ====================

export const classifyPatient = async (triageData) => {
  try {
    const response = await api.post('/api/triage/classify', triageData);
    return response.data;
  } catch (error) {
    console.error('Error classifying patient:', error);
    throw error;
  }
};

export const dischargePatient = async (assessmentId) => {
  try {
    const response = await api.post(`/api/triage/assessments/${assessmentId}/discharge`);
    return response.data;
  } catch (error) {
    console.error('Error discharging patient:', error);
    throw error;
  }
};

// ==================== DASHBOARD ====================

export const getDashboardMetrics = async () => {
  try {
    const response = await api.get('/api/dashboard/metrics');
    return response.data;
  } catch (error) {
    console.error('Error fetching metrics:', error);
    throw error;
  }
};

export const getActivePatients = async () => {
  try {
    const response = await api.get('/api/dashboard/active-patients');
    return response.data;
  } catch (error) {
    console.error('Error fetching active patients:', error);
    throw error;
  }
};

export const getStaffWorkload = async () => {
  try {
    const response = await api.get('/api/dashboard/staff-workload');
    return response.data;
  } catch (error) {
    console.error('Error fetching staff workload:', error);
    throw error;
  }
};

// ==================== WEBSOCKET ====================

export const connectWebSocket = (onMessage) => {
  const ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    // El token va como primer mensaje y no en la URL, para que no quede
    // registrado en los logs de acceso del servidor.
    ws.send(getAuthToken() || '');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };

  return ws;
};

export default api;