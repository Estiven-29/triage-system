import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Activity, Users, Clock, AlertTriangle, TrendingUp, AlertCircle } from 'lucide-react';
import { API_BASE_URL, getDashboardMetrics, getActivePatients, connectWebSocket } from '../services/api';

// Carga de personal: el backend no modela asignacion/turnos de personal,
// asi que esta seccion se mantiene como dato ilustrativo (se indica en la UI).
const ILLUSTRATIVE_STAFF_WORKLOAD = [
  { name: 'Dr. García', role: 'Cardiólogo', tiss28Load: 60, capacity: 70, patients: 2, ratio: '1:1', available: true },
  { name: 'Dra. Martínez', role: 'Urgencias', tiss28Load: 53, capacity: 60, patients: 2, ratio: '1:2', available: true },
  { name: 'Dr. López', role: 'Urgencias', tiss28Load: 28, capacity: 50, patients: 1, ratio: '1:3', available: true },
  { name: 'Dra. Fernández', role: 'Cirugía', tiss28Load: 15, capacity: 50, patients: 0, ratio: '0:0', available: true }
];

const TriageDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [realTimeData, setRealTimeData] = useState({
    activePatients: [],
    staffWorkload: ILLUSTRATIVE_STAFF_WORKLOAD,
    systemMetrics: {
      totalPatients: 0,
      critical: 0,
      urgent: 0,
      normal: 0,
      avgWaitTime: 0,
      mlConfidence: 0,
      avgTiss28: 0
    },
    tiss28Distribution: []
  });
  const [loadError, setLoadError] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [metrics, activePatients] = await Promise.all([
        getDashboardMetrics(),
        getActivePatients(),
      ]);
      setRealTimeData(prev => ({
        ...prev,
        systemMetrics: metrics.systemMetrics,
        tiss28Distribution: metrics.tiss28Distribution,
        activePatients,
      }));
      setLoadError(false);
    } catch (error) {
      console.error('Error cargando datos del dashboard:', error);
      setLoadError(true);
    }
  }, []);

  useEffect(() => {
    refresh();

    // Polling como respaldo cada 8s, mas un refresco inmediato cuando el
    // WebSocket avisa que se clasifico un paciente nuevo.
    const interval = setInterval(refresh, 8000);
    const ws = connectWebSocket((event) => {
      if (event.type === 'new_patient') refresh();
    });

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [refresh]);

  const categoryColors = {
    'CRITICO': '#ef4444',
    'URGENTE': '#f59e0b',
    'NORMAL': '#10b981'
  };

  const MetricCard = ({ icon: Icon, title, value, subtitle, color }) => (
    <div className="bg-white rounded-lg shadow p-6 border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold mt-2" style={{ color }}>{value}</p>
          {subtitle && <p className="text-gray-400 text-xs mt-1">{subtitle}</p>}
        </div>
        <Icon className="w-12 h-12 opacity-20" style={{ color }} />
      </div>
    </div>
  );

  const PatientCard = ({ patient }) => (
    <div className="bg-white rounded-lg shadow-md p-4 mb-3 border-l-4 hover:shadow-lg transition-shadow"
         style={{ borderLeftColor: categoryColors[patient.category] }}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-bold text-lg">{patient.name}</h3>
          <p className="text-gray-600 text-sm">{patient.age ? `${patient.age} años | ` : ''}{patient.complaint || 'Sin motivo registrado'}</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-semibold text-white"
              style={{ backgroundColor: categoryColors[patient.category] }}>
          {patient.category}
        </span>
      </div>
      
      <div className="grid grid-cols-4 gap-2 mt-3 text-sm">
        <div className="text-center">
          <p className="text-gray-500 text-xs">Risk Score</p>
          <p className="font-bold text-lg">{patient.riskScore}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-500 text-xs">TISS-28</p>
          <p className="font-bold text-lg">{patient.tiss28}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-500 text-xs">Espera</p>
          <p className="font-bold text-lg">{patient.waitTime}m</p>
        </div>
        <div className="text-center">
          <p className="text-gray-500 text-xs">Asignado</p>
          <p className="font-bold text-xs truncate">{patient.assignedTo}</p>
        </div>
      </div>
    </div>
  );

  const StaffWorkloadCard = ({ staff }) => {
    const loadPercentage = (staff.tiss28Load / staff.capacity) * 100;
    let statusColor = '#10b981';
    if (loadPercentage > 80) statusColor = '#ef4444';
    else if (loadPercentage > 60) statusColor = '#f59e0b';

    return (
      <div className="bg-white rounded-lg shadow p-4 mb-3">
        <div className="flex justify-between items-center mb-3">
          <div>
            <h4 className="font-bold">{staff.name}</h4>
            <p className="text-sm text-gray-500">{staff.role}</p>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-semibold ${staff.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {staff.available ? 'Disponible' : 'Ocupado'}
          </span>
        </div>

        <div className="mb-2">
          <div className="flex justify-between text-sm mb-1">
            <span>Carga TISS-28</span>
            <span className="font-bold">{staff.tiss28Load}/{staff.capacity}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div className="h-3 rounded-full transition-all duration-500"
                 style={{ width: `${loadPercentage}%`, backgroundColor: statusColor }}>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-500">Pacientes:</span>
            <span className="font-bold ml-2">{staff.patients}</span>
          </div>
          <div>
            <span className="text-gray-500">Ratio:</span>
            <span className="font-bold ml-2">{staff.ratio}</span>
          </div>
        </div>
      </div>
    );
  };

  const OverviewTab = () => {
    const pieData = [
      { name: 'Crítico', value: realTimeData.systemMetrics.critical, color: '#ef4444' },
      { name: 'Urgente', value: realTimeData.systemMetrics.urgent, color: '#f59e0b' },
      { name: 'Normal', value: realTimeData.systemMetrics.normal, color: '#10b981' }
    ];

    return (
      <div className="space-y-6">
        {loadError && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0" />
            <p className="text-sm text-red-700">
              No se pudo conectar con el backend ({API_BASE_URL}).
              Verifica que este corriendo.
            </p>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Users}
            title="Pacientes Activos"
            value={realTimeData.systemMetrics.totalPatients}
            color="#3b82f6"
          />
          <MetricCard
            icon={AlertTriangle}
            title="Casos Críticos"
            value={realTimeData.systemMetrics.critical}
            subtitle="Requieren atención inmediata"
            color="#ef4444"
          />
          <MetricCard
            icon={Clock}
            title="Tiempo Espera Prom."
            value={`${realTimeData.systemMetrics.avgWaitTime}m`}
            color="#f59e0b"
          />
          <MetricCard
            icon={TrendingUp}
            title="TISS-28 Promedio"
            value={realTimeData.systemMetrics.avgTiss28 ? realTimeData.systemMetrics.avgTiss28.toFixed(1) : '0.0'}
            subtitle={`Confianza ML: ${realTimeData.systemMetrics.mlConfidence || 0}%`}
            color="#8b5cf6"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Distribución por Categoría</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  dataKey="value"
                  nameKey="name"
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Distribución TISS-28</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={realTimeData.tiss28Distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8b5cf6" name="Pacientes" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">Pacientes en Espera</h3>
            <button
              onClick={refresh}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
            >
              Actualizar
            </button>
          </div>
          {realTimeData.activePatients.length === 0 ? (
            <p className="text-gray-500 text-sm py-6 text-center">
              No hay pacientes clasificados todavía. Ve a "Nuevo Paciente" para registrar uno.
            </p>
          ) : (
            <div className="space-y-3">
              {realTimeData.activePatients
                .slice()
                .sort((a, b) => a.category === 'CRITICO' ? -1 : b.category === 'CRITICO' ? 1 : a.waitTime - b.waitTime)
                .map(patient => (
                  <PatientCard key={patient.id} patient={patient} />
                ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const WorkloadTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold mb-1">Carga de Trabajo del Personal (TISS-28)</h3>
        <p className="text-xs text-gray-400 mb-4">
          Datos de ejemplo con fines ilustrativos: el backend aun no gestiona asignacion de personal.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div>
            <h4 className="font-semibold mb-3 text-gray-700">Personal Médico</h4>
            {realTimeData.staffWorkload.map((staff, idx) => (
              <StaffWorkloadCard key={idx} staff={staff} />
            ))}
          </div>

          <div>
            <h4 className="font-semibold mb-3 text-gray-700">Análisis de Capacidad</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={realTimeData.staffWorkload}
                layout="vertical"
                margin={{ left: 100 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} />
                <YAxis type="category" dataKey="name" />
                <Tooltip />
                <Legend />
                <Bar dataKey="tiss28Load" fill="#3b82f6" name="Carga Actual" />
                <Bar dataKey="capacity" fill="#d1d5db" name="Capacidad Máxima" />
              </BarChart>
            </ResponsiveContainer>

            <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400">
              <div className="flex">
                <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-yellow-800">Recomendación del Sistema</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    Dr. García está cerca de su capacidad máxima (86%). Considere reasignar nuevos pacientes críticos a Dr. López.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8">
          <h4 className="font-semibold mb-3 text-gray-700">Intervenciones TISS-28 Activas</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Intervención</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pacientes</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Puntaje</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Personal Req.</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Ventilación Mecánica</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">1</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">3</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Ratio 1:1</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Medicación Vasoactiva</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">2</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">3-4</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Ratio 1:1</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Monitorización Arterial</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">2</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">2</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Ratio 1:2</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Oxigenoterapia</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">3</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">2</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">Ratio 1:3</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  const AnalyticsTab = () => {
    const performanceData = [
      { time: '00:00', pacientes: 3, tiss28Avg: 18, mlConfidence: 85 },
      { time: '04:00', pacientes: 2, tiss28Avg: 15, mlConfidence: 88 },
      { time: '08:00', pacientes: 8, tiss28Avg: 22, mlConfidence: 82 },
      { time: '12:00', pacientes: 12, tiss28Avg: 25, mlConfidence: 79 },
      { time: '16:00', pacientes: 10, tiss28Avg: 21, mlConfidence: 84 },
      { time: '20:00', pacientes: 5, tiss28Avg: 19, mlConfidence: 86 }
    ];

    // Metricas reales, medidas con ml-training/evaluate_model.py sobre un
    // conjunto sintetico de evaluacion (semilla distinta a la de entrenamiento).
    const modelPerformance = [
      { categoria: 'Precisión', actual: 91, objetivo: 80 },
      { categoria: 'Recall Crítico', actual: 91, objetivo: 90 },
      { categoria: 'Recall Urgente', actual: 84, objetivo: 80 },
      { categoria: 'Confianza', actual: 71, objetivo: 70 },
      { categoria: 'Cohen Kappa', actual: 79, objetivo: 65 }
    ];

    return (
      <div className="space-y-6">
        <div className="bg-amber-50 border-l-4 border-amber-400 p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-amber-600 mr-2 flex-shrink-0" />
          <p className="text-sm text-amber-800">
            La tendencia horaria, la matriz de confusión y las tarjetas de impacto de esta
            pestaña son datos de ejemplo ilustrativos (no hay aún seguimiento histórico real).
            El radar de "Rendimiento del Modelo ML" sí usa métricas reales, medidas con
            <code className="mx-1 bg-amber-100 px-1 rounded">ml-training/evaluate_model.py</code>
            sobre un conjunto sintético de evaluación.
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Tendencia de Pacientes (24h)</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="pacientes" stroke="#3b82f6" strokeWidth={2} name="Pacientes" />
                <Line type="monotone" dataKey="tiss28Avg" stroke="#8b5cf6" strokeWidth={2} name="TISS-28 Promedio" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Confianza del Modelo ML</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="mlConfidence" stroke="#10b981" strokeWidth={2} name="Confianza %" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold mb-4">Rendimiento del Modelo ML</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={modelPerformance}>
              <PolarGrid />
              <PolarAngleAxis dataKey="categoria" />
              <PolarRadiusAxis domain={[0, 100]} />
              <Radar name="Actual" dataKey="actual" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
              <Radar name="Objetivo" dataKey="objetivo" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
              <Tooltip />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
            <h4 className="text-sm font-medium opacity-90">Reducción Tiempo Espera</h4>
            <p className="text-4xl font-bold mt-2">-38%</p>
            <p className="text-sm mt-2 opacity-80">vs. mes anterior</p>
          </div>
          
          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
            <h4 className="text-sm font-medium opacity-90">Precisión Clasificación</h4>
            <p className="text-4xl font-bold mt-2">87%</p>
            <p className="text-sm mt-2 opacity-80">+3% esta semana</p>
          </div>
          
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
            <h4 className="text-sm font-medium opacity-90">Satisfacción Personal</h4>
            <p className="text-4xl font-bold mt-2">4.6/5</p>
            <p className="text-sm mt-2 opacity-80">Distribución equilibrada TISS-28</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold mb-4">Matriz de Confusión - Últimos 7 días</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr>
                  <th className="px-4 py-2"></th>
                  <th className="px-4 py-2 text-center bg-red-50 font-semibold">Pred: CRÍTICO</th>
                  <th className="px-4 py-2 text-center bg-yellow-50 font-semibold">Pred: URGENTE</th>
                  <th className="px-4 py-2 text-center bg-green-50 font-semibold">Pred: NORMAL</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="px-4 py-2 font-semibold bg-red-50">Real: CRÍTICO</td>
                  <td className="px-4 py-2 text-center bg-green-100 font-bold">48</td>
                  <td className="px-4 py-2 text-center bg-yellow-100">4</td>
                  <td className="px-4 py-2 text-center bg-red-100">0</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-semibold bg-yellow-50">Real: URGENTE</td>
                  <td className="px-4 py-2 text-center bg-yellow-100">6</td>
                  <td className="px-4 py-2 text-center bg-green-100 font-bold">142</td>
                  <td className="px-4 py-2 text-center bg-yellow-100">12</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-semibold bg-green-50">Real: NORMAL</td>
                  <td className="px-4 py-2 text-center bg-red-100">2</td>
                  <td className="px-4 py-2 text-center bg-yellow-100">15</td>
                  <td className="px-4 py-2 text-center bg-green-100 font-bold">298</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            <p><span className="font-semibold">Precisión global:</span> 87.3%</p>
            <p><span className="font-semibold">Recall casos críticos:</span> 92.3% (48/52)</p>
            <p><span className="font-semibold">Falsos negativos críticos:</span> 4 casos (requieren revisión)</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 flex items-center">
                <Activity className="mr-3 text-blue-600" size={36} />
                Sistema de Triage Inteligente
              </h1>
              <p className="text-gray-500 mt-1">Clasificación automática con ML + TISS-28</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Última actualización</p>
              <p className="text-lg font-semibold">{new Date().toLocaleTimeString('es-ES')}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b">
            <button
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              onClick={() => setActiveTab('overview')}
            >
              Vista General
            </button>
            <button
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'workload'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              onClick={() => setActiveTab('workload')}
            >
              Carga de Trabajo TISS-28
            </button>
            <button
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'analytics'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              onClick={() => setActiveTab('analytics')}
            >
              Analítica y Rendimiento
            </button>
          </div>
        </div>

        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'workload' && <WorkloadTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
      </div>
    </div>
  );
};

export default TriageDashboard;