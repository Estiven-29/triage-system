import { connectWebSocket } from './api';

// WebSocket falso: registra cada instancia para poder abrirla/cerrarla a mano.
class FakeWebSocket {
  static instances = [];

  constructor(url) {
    this.url = url;
    this.sent = [];
    FakeWebSocket.instances.push(this);
  }

  send(data) {
    this.sent.push(data);
  }

  close() {
    this.onclose?.({ code: 1000 });
  }

  // Helpers del test
  simulateOpen() {
    this.onopen?.();
  }

  simulateDrop(code = 1006) {
    this.onclose?.({ code });
  }
}

beforeEach(() => {
  jest.useFakeTimers();
  FakeWebSocket.instances = [];
  global.WebSocket = FakeWebSocket;
  sessionStorage.setItem('triage_staff_token', 'token-de-prueba');
});

afterEach(() => {
  jest.useRealTimers();
  sessionStorage.clear();
});

test('sends the token as the first message instead of in the URL', () => {
  const conn = connectWebSocket(() => {});
  const [ws] = FakeWebSocket.instances;
  ws.simulateOpen();
  expect(ws.url).not.toContain('token');
  expect(ws.sent).toEqual(['token-de-prueba']);
  conn.close();
});

test('reconnects with exponential backoff and notifies on each connection', () => {
  const events = [];
  const conn = connectWebSocket((event) => events.push(event.type));

  FakeWebSocket.instances[0].simulateOpen();
  FakeWebSocket.instances[0].simulateDrop();
  jest.advanceTimersByTime(999);
  expect(FakeWebSocket.instances).toHaveLength(1);
  jest.advanceTimersByTime(1);
  expect(FakeWebSocket.instances).toHaveLength(2);

  // Sin abrir, el segundo intento vuelve a caer: ahora espera 2 s.
  FakeWebSocket.instances[1].simulateDrop();
  jest.advanceTimersByTime(1999);
  expect(FakeWebSocket.instances).toHaveLength(2);
  jest.advanceTimersByTime(1);
  expect(FakeWebSocket.instances).toHaveLength(3);

  FakeWebSocket.instances[2].simulateOpen();
  expect(events).toEqual(['connected', 'connected']);
  conn.close();
});

test('does not reconnect after an auth rejection or a manual close', () => {
  connectWebSocket(() => {});
  FakeWebSocket.instances[0].simulateDrop(1008);
  jest.advanceTimersByTime(60000);
  expect(FakeWebSocket.instances).toHaveLength(1);

  const conn = connectWebSocket(() => {});
  conn.close();
  jest.advanceTimersByTime(60000);
  expect(FakeWebSocket.instances).toHaveLength(2);
});
