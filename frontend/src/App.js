// src/App.js
import React, { useState } from 'react';
import './App.css';
import TriageDashboard from './components/TriageDashboard';
import PatientIntake from './components/PatientIntake';

function App() {
  const [currentView, setCurrentView] = useState('home');

  const HomePage = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
      <div className="max-w-4xl w-full">
        <div className="bg-white rounded-2xl shadow-2xl p-12 text-center">
          <div className="mb-8">
            <svg className="w-24 h-24 mx-auto text-blue-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h1 className="text-5xl font-bold text-gray-800 mb-4">
              Sistema de Triage Inteligente
            </h1>
            <p className="text-xl text-gray-600">
              Clasificación automática de pacientes con IA + TISS-28
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-12">
            <button
              onClick={() => setCurrentView('intake')}
              className="group bg-blue-600 hover:bg-blue-700 text-white rounded-xl p-8 transition-all transform hover:scale-105 shadow-lg"
            >
              <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
              <h2 className="text-2xl font-bold mb-2">Nuevo Paciente</h2>
              <p className="text-blue-100">
                Registrar y clasificar paciente con IA
              </p>
            </button>

            <button
              onClick={() => setCurrentView('dashboard')}
              className="group bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl p-8 transition-all transform hover:scale-105 shadow-lg"
            >
              <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h2 className="text-2xl font-bold mb-2">Dashboard Médico</h2>
              <p className="text-indigo-100">
                Ver pacientes activos y métricas en tiempo real
              </p>
            </button>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-200">
            <div className="grid grid-cols-3 gap-8 text-center">
              <div>
                <p className="text-3xl font-bold text-blue-600">91%</p>
                <p className="text-sm text-gray-600">Precisión del modelo (datos sintéticos)</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-green-600">&lt;1s</p>
                <p className="text-sm text-gray-600">Tiempo de clasificación</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-purple-600">3</p>
                <p className="text-sm text-gray-600">Niveles de triage</p>
              </div>
            </div>
          </div>

          <div className="mt-8">
            <p className="text-sm text-gray-500">
              🤖 Clasificacion asistida por Machine Learning | 📋 Proyecto educativo, no un dispositivo medico
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      {currentView === 'home' && <HomePage />}
      {currentView === 'intake' && (
        <div>
          <button
            onClick={() => setCurrentView('home')}
            className="fixed top-4 left-4 z-50 bg-white px-4 py-2 rounded-lg shadow-lg hover:bg-gray-100 transition-colors"
          >
            ← Volver al inicio
          </button>
          <PatientIntake onGoToDashboard={() => setCurrentView('dashboard')} />
        </div>
      )}
      {currentView === 'dashboard' && (
        <div>
          <button
            onClick={() => setCurrentView('home')}
            className="fixed top-4 left-4 z-50 bg-white px-4 py-2 rounded-lg shadow-lg hover:bg-gray-100 transition-colors"
          >
            ← Volver al inicio
          </button>
          <TriageDashboard />
        </div>
      )}
    </div>
  );
}

export default App;