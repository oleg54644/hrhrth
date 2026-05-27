"""
WebSocket client — держит соединение с сервером в фоновом потоке.
Использует встроенный websockets или ws4py (без внешних зависимостей).
"""

import json, threading, time

try:
    import websocket   # websocket-client
    _LIB = 'websocket-client'
except ImportError:
    _LIB = None


class WSClient:
    def __init__(self, app):
        self.app  = app
        self._ws  = None
        self._thr = None
        self._token = None
        self._running = False

    # ── Public ─────────────────────────────────────────────────────────────

    def connect(self, token: str):
        self._token = token
        if _LIB is None:
            print('[WS] websocket-client не установлен, WS недоступен')
            return
        self._running = True
        self._thr = threading.Thread(target=self._run, daemon=True)
        self._thr.start()

    def disconnect(self):
        self._running = False
        if self._ws:
            try: self._ws.close()
            except: pass

    def send(self, data: dict):
        if self._ws:
            try: self._ws.send(json.dumps(data))
            except Exception as e:
                print(f'[WS] send error: {e}')

    # ── Internal ───────────────────────────────────────────────────────────

    def _run(self):
        server = self.app.storage.get_server()
        ws_url = server.replace('http://', 'ws://').replace('https://', 'wss://')
        url    = f'{ws_url}/ws?token={self._token}'

        while self._running:
            try:
                self._ws = websocket.WebSocketApp(
                    url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self._ws.run_forever(ping_interval=25, ping_timeout=10)
            except Exception as e:
                print(f'[WS] connection error: {e}')
            if self._running:
                time.sleep(5)   # reconnect after 5s

    def _on_message(self, ws, raw):
        try:
            msg = json.loads(raw)
        except:
            return

        t = msg.get('type')
        if t == 'incoming_call':
            self.app.on_incoming_call(
                msg['from'], msg['from_user'], msg['call_id'])
        elif t == 'answered':
            self.app.on_call_answered(msg['call_id'])
        elif t == 'hangup':
            self.app.on_call_hangup(msg['call_id'])
        elif t == 'error':
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: self.app.sm.get_screen('call')
                    .show_error(msg.get('message', 'Ошибка')), 0)

    def _on_error(self, ws, err):
        print(f'[WS] error: {err}')

    def _on_close(self, ws, code, msg):
        print(f'[WS] closed: {code}')
