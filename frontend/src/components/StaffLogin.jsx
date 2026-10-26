import React, { useState } from 'react';
import { Lock } from 'lucide-react';
import { login, getErrorMessage } from '../services/api';

const StaffLogin = ({ onLoggedIn }) => {
  const [employeeId, setEmployeeId] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    setIsSubmitting(true);
    try {
      const staff = await login(employeeId.trim(), password);
      onLoggedIn(staff);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'No se pudo iniciar sesión.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-6">
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-1 flex items-center">
          <Lock className="mr-2 text-blue-600" /> Acceso del personal
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          El dashboard muestra datos de pacientes y requiere iniciar sesión.
        </p>

        {errorMessage && (
          <div role="alert" className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 mb-4 rounded text-sm">
            {errorMessage}
          </div>
        )}

        <label htmlFor="employee-id" className="block text-sm font-semibold mb-1 text-gray-700">
          Número de empleado
        </label>
        <input
          id="employee-id"
          className="w-full border rounded p-2 mb-4"
          autoComplete="username"
          maxLength={50}
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          required
        />

        <label htmlFor="password" className="block text-sm font-semibold mb-1 text-gray-700">
          Contraseña
        </label>
        <input
          id="password"
          type="password"
          className="w-full border rounded p-2 mb-6"
          autoComplete="current-password"
          maxLength={200}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {isSubmitting ? 'Ingresando…' : 'Iniciar sesión'}
        </button>
      </form>
    </div>
  );
};

export default StaffLogin;
