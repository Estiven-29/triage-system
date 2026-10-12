import React, { useState } from 'react';
import { Activity, User, Heart, Thermometer, Wind, Droplet, AlertTriangle } from 'lucide-react';
import {
  startChatbotSession,
  sendChatbotMessage,
  classifyPatient as classifyPatientRequest,
  getErrorMessage,
} from '../services/api';

const VITAL_SIGN_LIMITS = {
  heart_rate: { label: 'Frecuencia cardíaca', min: 0, max: 300, integer: true },
  respiratory_rate: { label: 'Frecuencia respiratoria', min: 0, max: 100, integer: true },
  systolic_bp: { label: 'Presión sistólica', min: 0, max: 300, integer: true },
  diastolic_bp: { label: 'Presión diastólica', min: 0, max: 200, integer: true },
  spo2: { label: 'SpO2', min: 0, max: 100, integer: true },
  temperature: { label: 'Temperatura', min: 25, max: 45, integer: false },
};

const PatientIntake = ({ onGoToDashboard }) => {
  const [step, setStep] = useState(1);
  const [sessionId, setSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [classificationResult, setClassificationResult] = useState(null);
  
  const [patientData, setPatientData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'male',
  });

  const [vitalSigns, setVitalSigns] = useState({
    heart_rate: '',
    respiratory_rate: '',
    systolic_bp: '',
    diastolic_bp: '',
    spo2: '',
    temperature: '',
  });

  const [symptoms, setSymptoms] = useState([]);
  const [chiefComplaint, setChiefComplaint] = useState('');

  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const startChatbot = async () => {
    if (!patientData.first_name.trim() || !patientData.last_name.trim()) {
      setErrorMessage('Nombre y apellido son obligatorios.');
      return;
    }

    setErrorMessage('');
    setIsSubmitting(true);
    try {
      const data = await startChatbotSession({
        ...patientData,
        date_of_birth: patientData.date_of_birth || null,
      });
      setSessionId(data.session_id);
      setChatMessages([{ sender: 'bot', text: data.message }]);
      setStep(2);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Error al iniciar el chatbot.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const sendMessage = async () => {
    const text = currentMessage.trim();
    if (!text || isSubmitting) return;

    const newMessages = [...chatMessages, { sender: 'user', text }];
    setChatMessages(newMessages);
    setCurrentMessage('');
    setErrorMessage('');
    setIsSubmitting(true);

    try {
      const data = await sendChatbotMessage(sessionId, text);

      setChatMessages([...newMessages, { sender: 'bot', text: data.response }]);

      if (data.extracted_data) {
        setSymptoms(data.extracted_data.symptoms || []);
        setChiefComplaint(data.extracted_data.chief_complaint || '');
      }

      if (data.conversation_complete) {
        setStep(3);
      }
    } catch (error) {
      // Revertimos el mensaje optimista y lo devolvemos al input para que
      // el usuario pueda reintentar sin volver a escribirlo.
      setChatMessages(chatMessages);
      setCurrentMessage(text);
      setErrorMessage(getErrorMessage(error, 'Error al enviar el mensaje.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Devuelve [signosVitalesParseados, null] o [null, mensajeDeError].
  // Los rangos replican la validacion del backend (VitalSigns en schemas.py).
  const parseVitalSigns = () => {
    const parsed = {};
    for (const [field, { label, min, max, integer }] of Object.entries(VITAL_SIGN_LIMITS)) {
      const raw = String(vitalSigns[field]).trim();
      const value = Number(raw);
      if (raw === '' || Number.isNaN(value)) {
        return [null, `Falta un valor válido para ${label}.`];
      }
      if (integer && !Number.isInteger(value)) {
        return [null, `${label} debe ser un número entero.`];
      }
      if (value < min || value > max) {
        return [null, `${label} debe estar entre ${min} y ${max}.`];
      }
      parsed[field] = value;
    }
    if (parsed.diastolic_bp >= parsed.systolic_bp) {
      return [null, 'La presión diastólica debe ser menor que la sistólica.'];
    }
    return [parsed, null];
  };

  const classifyPatient = async () => {
    const [parsedVitals, validationError] = parseVitalSigns();
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setErrorMessage('');
    setIsSubmitting(true);
    try {
      const data = await classifyPatientRequest({
        patient_id: sessionId,
        vital_signs: parsedVitals,
        chief_complaint: chiefComplaint,
        symptoms: symptoms,
      });
      setClassificationResult(data);
      setStep(4);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Error al clasificar al paciente.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'CRITICO': return 'bg-red-500';
      case 'URGENTE': return 'bg-yellow-500';
      case 'NORMAL': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const resetForm = () => {
    setStep(1);
    setSessionId(null);
    setChatMessages([]);
    setClassificationResult(null);
    setPatientData({
      first_name: '',
      last_name: '',
      date_of_birth: '',
      gender: 'male'
    });
    setVitalSigns({
      heart_rate: '',
      respiratory_rate: '',
      systolic_bp: '',
      diastolic_bp: '',
      spo2: '',
      temperature: ''
    });
    setSymptoms([]);
    setChiefComplaint('');
    setErrorMessage('');
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center">
            <Activity className="text-blue-600 mr-3" size={32} />
            <div>
              <h1 className="text-2xl font-bold">Sistema de Triage Inteligente</h1>
              <p className="text-gray-500">Clasificación automática con IA</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center">
            {[1, 2, 3, 4].map((s) => (
              <div key={s} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  step >= s ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  {s}
                </div>
                {s < 4 && <div className={`h-1 w-20 mx-2 ${step > s ? 'bg-blue-600' : 'bg-gray-300'}`} />}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-sm text-gray-600">
            <span>Datos Paciente</span>
            <span>Chatbot</span>
            <span>Signos Vitales</span>
            <span>Resultado</span>
          </div>
        </div>

        {errorMessage && (
          <div role="alert" className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded">
            {errorMessage}
          </div>
        )}

        {step === 1 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <User className="mr-2" /> Datos del Paciente
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Nombre"
                className="border rounded p-2"
                value={patientData.first_name}
                onChange={(e) => setPatientData({...patientData, first_name: e.target.value})}
              />
              <input
                type="text"
                placeholder="Apellido"
                className="border rounded p-2"
                value={patientData.last_name}
                onChange={(e) => setPatientData({...patientData, last_name: e.target.value})}
              />
              <input
                type="date"
                placeholder="Fecha de Nacimiento"
                className="border rounded p-2"
                value={patientData.date_of_birth}
                onChange={(e) => setPatientData({...patientData, date_of_birth: e.target.value})}
              />
              <select
                className="border rounded p-2"
                value={patientData.gender}
                onChange={(e) => setPatientData({...patientData, gender: e.target.value})}
              >
                <option value="male">Masculino</option>
                <option value="female">Femenino</option>
                <option value="other">Otro</option>
              </select>
            </div>
            <button
              onClick={startChatbot}
              disabled={isSubmitting}
              className="mt-6 w-full disabled:opacity-50 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Iniciar Evaluación →
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Conversación con Asistente IA</h2>
            
            <div className="border rounded-lg p-4 h-96 overflow-y-auto mb-4 bg-gray-50">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`mb-3 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs px-4 py-2 rounded-lg ${
                    msg.sender === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white border border-gray-300'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 border rounded-lg p-3"
                placeholder="Escriba su respuesta..."
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              />
              <button
                onClick={sendMessage}
                disabled={isSubmitting}
                className="disabled:opacity-50 bg-blue-600 text-white px-6 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Enviar
              </button>
            </div>

            <button
              onClick={() => setStep(3)}
              className="mt-4 w-full bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700"
            >
              Continuar al siguiente paso →
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <Heart className="mr-2 text-red-500" /> Signos Vitales
            </h2>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="flex items-center text-sm font-semibold mb-2 text-gray-700">
                  <Heart className="mr-2" size={18} /> Frecuencia Cardíaca (lpm)
                </label>
                <input
                  type="number"
                  className="w-full border rounded-lg p-3"
                  placeholder="Ej: 75"
                  value={vitalSigns.heart_rate}
                  onChange={(e) => setVitalSigns({...vitalSigns, heart_rate: e.target.value})}
                />
              </div>

              <div>
                <label className="flex items-center text-sm font-semibold mb-2 text-gray-700">
                  <Wind className="mr-2" size={18} /> Frecuencia Respiratoria (rpm)
                </label>
                <input
                  type="number"
                  className="w-full border rounded-lg p-3"
                  placeholder="Ej: 16"
                  value={vitalSigns.respiratory_rate}
                  onChange={(e) => setVitalSigns({...vitalSigns, respiratory_rate: e.target.value})}
                />
              </div>

              <div>
                <label className="flex items-center text-sm font-semibold mb-2 text-gray-700">
                  <Droplet className="mr-2" size={18} /> Presión Sistólica (mmHg)
                </label>
                <input
                  type="number"
                  className="w-full border rounded-lg p-3"
                  placeholder="Ej: 120"
                  value={vitalSigns.systolic_bp}
                  onChange={(e) => setVitalSigns({...vitalSigns, systolic_bp: e.target.value})}
                />
              </div>

              <div>
                <label className="flex items-center text-sm font-semibold mb-2 text-gray-700">
                  <Droplet className="mr-2" size={18} /> Presión Diastólica (mmHg)
                </label>
                <input
                  type="number"
                  className="w-full border rounded-lg p-3"
                  placeholder="Ej: 80"
                  value={vitalSigns.diastolic_bp}
                  onChange={(e) => setVitalSigns({...vitalSigns, diastolic_bp: e.target.value})}
                />
              </div>

              <div>
                <label className="flex items-center text-sm font-semibold mb-2 text-gray-700">
                  <Activity className="mr-2" size={18} /> SpO2 (%)
                </label>
                <input
                  type="number"
                  className="w-full border rounded-lg p-3"
                  placeholder="Ej: 98"
                  value={vitalSigns.spo2}
                  onChange={(e) => setVitalSigns({...vitalSigns, spo2: e.target.value})}
                />
              </div>

              <div>
                <label className="flex items-center text-sm font-semibold mb-2 text-gray-700">
                  <Thermometer className="mr-2" size={18} /> Temperatura (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  className="w-full border rounded-lg p-3"
                  placeholder="Ej: 36.5"
                  value={vitalSigns.temperature}
                  onChange={(e) => setVitalSigns({...vitalSigns, temperature: e.target.value})}
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-semibold mb-2 text-gray-700">
                Motivo de Consulta Principal
              </label>
              <textarea
                className="w-full border rounded-lg p-3"
                rows="3"
                placeholder="Describa el motivo principal de la consulta..."
                value={chiefComplaint}
                onChange={(e) => setChiefComplaint(e.target.value)}
              />
            </div>

            <button
              onClick={classifyPatient}
              disabled={isSubmitting}
              className="disabled:opacity-50 w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center"
            >
              <Activity className="mr-2" /> Clasificar con IA →
            </button>
          </div>
        )}

        {step === 4 && classificationResult && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-6 text-center">Resultado de Clasificación</h2>

            <div className="flex justify-center mb-6">
              <div className={`${getCategoryColor(classificationResult.classification)} text-white px-8 py-4 rounded-lg text-center`}>
                <p className="text-sm font-medium">Categoría de Triage</p>
                <p className="text-4xl font-bold">{classificationResult.classification}</p>
              </div>
            </div>

            {classificationResult.safety_override && (
              <div className="bg-red-50 border-l-4 border-red-500 text-red-800 p-4 mb-6 flex items-start">
                <AlertTriangle className="mr-2 flex-shrink-0" />
                <p className="text-sm">
                  El modelo sugería otra categoría, pero se elevó a CRÍTICO por la regla de
                  seguridad: hay signos vitales con alerta roja (criterio tipo NEWS2).
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <p className="text-gray-600 text-sm">Confianza IA</p>
                <p className="text-2xl font-bold text-blue-600">
                  {(classificationResult.confidence * 100).toFixed(1)}%
                </p>
              </div>
              
              <div className="bg-red-50 rounded-lg p-4 text-center">
                <p className="text-gray-600 text-sm">Risk Score</p>
                <p className="text-2xl font-bold text-red-600">
                  {classificationResult.risk_score}/100
                </p>
              </div>

              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <p className="text-gray-600 text-sm">TISS-28</p>
                <p className="text-2xl font-bold text-purple-600">
                  {classificationResult.tiss28_score}
                </p>
              </div>

              <div className="bg-green-50 rounded-lg p-4 text-center">
                <p className="text-gray-600 text-sm">Complejidad</p>
                <p className="text-lg font-bold text-green-600">
                  {classificationResult.complexity_level}
                </p>
              </div>
            </div>

            {classificationResult.preliminary_diagnoses && classificationResult.preliminary_diagnoses.length > 0 && (
              <div className="mb-6">
                <h3 className="font-semibold mb-3">Diagnósticos Preliminares Sugeridos por IA:</h3>
                <div className="space-y-2">
                  {classificationResult.preliminary_diagnoses.map((diag, idx) => (
                    <div key={idx} className="bg-gray-50 rounded-lg p-3 flex justify-between items-center">
                      <span>{diag.name}</span>
                      <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                        {(diag.probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {classificationResult.recommended_actions && classificationResult.recommended_actions.length > 0 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                <h3 className="font-semibold mb-2 flex items-center text-yellow-800">
                  <Activity className="mr-2" /> Acciones Recomendadas:
                </h3>
                <ul className="list-disc list-inside text-sm text-yellow-800">
                  {classificationResult.recommended_actions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={resetForm}
                className="flex-1 bg-gray-600 text-white py-3 rounded-lg hover:bg-gray-700"
              >
                Nuevo Paciente
              </button>
              <button
                onClick={onGoToDashboard}
                className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"
              >
                Ver Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientIntake;