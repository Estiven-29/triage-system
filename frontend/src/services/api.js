import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
  const ws = new WebSocket(`ws://localhost:8000/ws/triage`);

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