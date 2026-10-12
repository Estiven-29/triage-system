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

// ==================== WEBSOCKET ====================

export const connectWebSocket = (onMessage) => {
  const ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log('WebSocket connected');
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