import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

test('renders the home page with both entry points', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /Sistema de Triage Inteligente/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Nuevo Paciente/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Dashboard Médico/i })).toBeInTheDocument();
});

test('patient intake requires first and last name before starting', () => {
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Nuevo Paciente/i }));
  fireEvent.click(screen.getByRole('button', { name: /Iniciar Evaluación/i }));
  expect(screen.getByRole('alert')).toHaveTextContent('Nombre y apellido son obligatorios.');
});
